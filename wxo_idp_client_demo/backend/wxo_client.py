"""
IBM watsonx Orchestrate REST API Client for Intelligent Document Processing (IDP).

Handles:
1. S3 Pre-Signed File Upload: POST /v1/orchestrate/upload-to-s3
2. Headless Direct Flow Execution: POST /v1/orchestrate/flows/{flow_id}/run/async + polling
3. Conversational Agent 2-Turn Execution: POST /v1/orchestrate/runs
"""

import json
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
import requests

# Load .env file from root of demo package or parent
for candidate_path in [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
]:
    if os.path.exists(candidate_path):
        with open(candidate_path, "r") as _ef:
            for _line in _ef:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())

TENANT_URL = os.environ.get(
    "WXO_TENANT_URL",
    "https://api.ca-tor.watson-orchestrate.cloud.ibm.com/instances/e2def58b-0869-4446-a0e3-55ecca8f07e9",
).rstrip("/")
API_KEY = os.environ.get("WXO_API_KEY", "")
FLOW_ID = os.environ.get("WXO_FLOW_ID", "513e67d6-2974-4776-a0ac-5869876bee9a")
AGENT_ID = os.environ.get("WXO_AGENT_ID", "23215e30-2f2f-4373-974b-0d7bb89e657a")


class WxOClient:
    def __init__(
        self,
        tenant_url: Optional[str] = None,
        api_key: Optional[str] = None,
        flow_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        self.tenant_url = (tenant_url or TENANT_URL).rstrip("/")
        self.api_key = api_key or API_KEY
        self.flow_id = flow_id or FLOW_ID
        self.agent_id = agent_id or AGENT_ID
        self._cached_token: Optional[str] = None
        self._token_expiry: float = 0.0

    def get_iam_token(self) -> Tuple[str, float]:
        """Fetch or reuse an IBM Cloud IAM Bearer token."""
        now = time.time()
        if self._cached_token and now < (self._token_expiry - 60):
            return self._cached_token, 0.0

        t0 = time.perf_counter()
        resp = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self.api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._cached_token = data["access_token"]
        self._token_expiry = now + data.get("expires_in", 3600)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        return self._cached_token, elapsed_ms

    def upload_file_to_s3(
        self, file_bytes: bytes, filename: str, token: str
    ) -> Tuple[List[Dict[str, Any]], str, float]:
        """
        Upload document to IBM Cloud Object Storage via watsonx Orchestrate S3 upload API.
        Endpoint: POST /v1/orchestrate/upload-to-s3
        """
        t0 = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        content_type = "application/pdf" if filename.lower().endswith(".pdf") else "image/png"
        files = {"file": (filename, file_bytes, content_type)}

        resp = requests.post(
            f"{self.tenant_url}/v1/orchestrate/upload-to-s3",
            headers=headers,
            files=files,
            timeout=60,
        )
        resp.raise_for_status()
        s3_files = resp.json().get("files", [])
        if not s3_files:
            raise RuntimeError(f"No file records returned from S3 upload: {resp.text}")

        s3_url = s3_files[0]["url"]
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        return s3_files, s3_url, elapsed_ms

    def run_direct_flow(
        self, s3_url: str, token: str
    ) -> Tuple[Dict[str, Any], str, float]:
        """
        Invoke the deployed `invoice_idp_flow` asynchronously via:
        POST /v1/orchestrate/flows/{flow_id}/run/async with {"document_ref": s3_url}
        and poll GET /v1/orchestrate/flows?instance_id={instance_id} until completed.
        """
        t0 = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        resp = requests.post(
            f"{self.tenant_url}/v1/orchestrate/flows/{self.flow_id}/run/async",
            headers=headers,
            json={"document_ref": s3_url},
            timeout=30,
        )
        resp.raise_for_status()
        instance_id = resp.json()["instance_id"]

        for _ in range(90):
            time.sleep(2.0)
            poll_resp = requests.get(
                f"{self.tenant_url}/v1/orchestrate/flows",
                params={"instance_id": instance_id},
                headers=headers,
                timeout=20,
            )
            poll_resp.raise_for_status()
            instances = poll_resp.json()
            if instances and isinstance(instances, list):
                inst = instances[0]
                state = inst.get("state")
                if state == "completed":
                    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
                    return inst.get("output") or {}, instance_id, elapsed_ms
                if state in ("failed", "error", "cancelled"):
                    raise RuntimeError(f"Flow instance {instance_id} failed: {inst.get('error')}")

        raise TimeoutError(f"Flow instance {instance_id} did not complete within timeout.")

    def run_agent_two_turn(
        self, s3_files: List[Dict[str, Any]], token: str
    ) -> Tuple[Dict[str, Any], str, str, float]:
        """
        Execute 2-turn Conversational Agent slot filling protocol via POST /v1/orchestrate/runs.
        Turn 1: Initialize conversation -> Agent requests document_ref slot.
        Turn 2: Provide S3 file reference context payload -> Agent executes tool and returns JSON.
        """
        t0 = time.perf_counter()
        thread_id = str(uuid.uuid4())
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Turn 1
        turn1_body = {
            "agent_id": self.agent_id,
            "thread_id": thread_id,
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "Please process and extract this uploaded invoice document."}],
            },
        }
        resp1 = requests.post(
            f"{self.tenant_url}/v1/orchestrate/runs",
            headers=headers,
            json=turn1_body,
            timeout=60,
        )
        resp1.raise_for_status()
        r1_json = resp1.json()
        run_id = r1_json.get("run_id") or r1_json.get("id") or ""

        # Turn 2: Send file reference
        turn2_body = {
            "agent_id": self.agent_id,
            "thread_id": thread_id,
            "message": {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Here is the uploaded invoice file in S3."},
                    {
                        "type": "file_download",
                        "name": s3_files[0].get("file_name", "document.pdf"),
                        "url": s3_files[0].get("url", ""),
                        "storage_provider": s3_files[0].get("storage_provider", "ibm-cos"),
                        "storage_data": s3_files[0].get("storage_data", {}),
                    },
                ],
            },
        }
        resp2 = requests.post(
            f"{self.tenant_url}/v1/orchestrate/runs",
            headers=headers,
            json=turn2_body,
            timeout=180,
        )
        resp2.raise_for_status()
        r2_json = resp2.json()
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

        # Parse JSON from agent text response
        raw_text = ""
        for msg in r2_json.get("messages", []):
            if msg.get("role") == "assistant":
                for c in msg.get("content", []):
                    if c.get("type") == "text":
                        raw_text += c.get("text", "")

        parsed_json: Dict[str, Any] = {}
        json_matches = re.findall(r"```json\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if json_matches:
            try:
                parsed_json = json.loads(json_matches[-1])
            except Exception:
                pass

        if not parsed_json:
            for brace_match in re.findall(r"(\{.*\})", raw_text, re.DOTALL):
                try:
                    parsed_json = json.loads(brace_match)
                    if "structured_invoice" in parsed_json or "invoice_number" in parsed_json:
                        break
                except Exception:
                    continue

        return (
            {
                "agent_raw_response": r2_json,
                "agent_text": raw_text,
                "structured_invoice": parsed_json.get("structured_invoice") or parsed_json,
                "kvps": parsed_json.get("kvps", []),
                "logic_summary": parsed_json.get("logic_summary", {}),
                "extracted_text": parsed_json.get("extracted_text", raw_text),
            },
            thread_id,
            run_id,
            elapsed_ms,
        )


def normalize_wxo_kvps(raw_kvps: List[Any]) -> Tuple[List[Dict[str, Any]], float]:
    """Normalize KVPs from docproc node output into consistent dictionary format."""
    normalized: List[Dict[str, Any]] = []
    confidences: List[float] = []

    for item in raw_kvps:
        if isinstance(item, dict):
            key = item.get("key") or item.get("label") or item.get("field") or ""
            val = item.get("value") or item.get("text") or ""
            conf = float(item.get("confidence") or 0.98)
            bbox = item.get("bbox") or item.get("bounding_box") or {}
            page = item.get("page") or item.get("page_number") or 1
        else:
            key = getattr(item, "key", "") or getattr(item, "label", "") or ""
            val = getattr(item, "value", "") or getattr(item, "text", "") or ""
            conf = float(getattr(item, "confidence", 0.98) or 0.98)
            bbox = getattr(item, "bbox", {}) or {}
            page = getattr(item, "page", 1) or 1

        if key or val:
            normalized.append(
                {
                    "key": str(key),
                    "value": str(val),
                    "confidence": conf,
                    "bbox": bbox if isinstance(bbox, dict) else {},
                    "page": page,
                }
            )
            confidences.append(conf)

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.98
    return normalized, round(avg_conf, 4)
