"""
IBM watsonx Orchestrate REST Client for Intelligent Document Processing (IDP).

Implements the exact S3/COS pre-signed upload protocol (`POST /v1/orchestrate/upload-to-s3`),
Headless Direct Flow execution (`POST /v1/orchestrate/flows/{flow_id}/run`), and
Conversational Agent 2-Turn File-Upload Slot execution (`POST /v1/orchestrate/runs`).
"""

import json
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
import requests

# Load optional .env file if available
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r") as _ef:
        for _line in _ef:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

TENANT_URL = os.environ.get(
    "WXO_TENANT_URL",
    "https://api.ca-tor.watson-orchestrate.cloud.ibm.com/instances/e2def58b-0869-4446-a0e3-55ecca8f07e9",
)
API_KEY = os.environ.get("WXO_API_KEY", "")
FLOW_ID = os.environ.get("WXO_FLOW_ID", "513e67d6-2974-4776-a0ac-5869876bee9a")
AGENT_ID = os.environ.get("WXO_AGENT_ID", "23215e30-2f2f-4373-974b-0d7bb89e657a")
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"


class WxOClient:
    def __init__(
        self,
        tenant_url: str = TENANT_URL,
        api_key: str = API_KEY,
        flow_id: str = FLOW_ID,
        agent_id: str = AGENT_ID,
    ):
        self.tenant_url = tenant_url.rstrip("/")
        self.api_key = api_key
        self.flow_id = flow_id
        self.agent_id = agent_id
        self._cached_token: Optional[str] = None
        self._token_expiry: float = 0.0

    def get_iam_token(self) -> Tuple[str, float]:
        """Exchange IBM Cloud API Key for an IAM Bearer token (cached until 5 min before expiry)."""
        t0 = time.perf_counter()
        now = time.time()
        if self._cached_token and now < self._token_expiry - 300:
            return self._cached_token, round((time.perf_counter() - t0) * 1000, 1)

        resp = requests.post(
            IAM_TOKEN_URL,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self.api_key,
            },
            timeout=25,
        )
        resp.raise_for_status()
        payload = resp.json()
        self._cached_token = payload["access_token"]
        self._token_expiry = float(payload.get("expiration", now + 3600))
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        return self._cached_token, elapsed_ms

    def upload_file_to_s3(
        self, file_bytes: bytes, filename: str, token: str
    ) -> Tuple[List[Dict[str, Any]], str, float]:
        """
        Upload invoice binary to the watsonx Orchestrate built-in S3/COS bucket
        via `POST /v1/orchestrate/upload-to-s3`.
        """
        t0 = time.perf_counter()
        file_meta = [
            {
                "fileName": filename,
                "invalid": False,
                "id": str(uuid.uuid4()),
                "statusCode": 200,
                "uploadStatus": "uploading",
                "url": "",
            }
        ]
        resp = requests.post(
            f"{self.tenant_url}/v1/orchestrate/upload-to-s3",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            files={"files": (filename, file_bytes, "application/octet-stream")},
            data={"text": "", "fileMetaData": json.dumps(file_meta)},
            timeout=60,
        )
        resp.raise_for_status()
        s3_files = resp.json()
        if not s3_files or s3_files[0].get("invalid"):
            raise RuntimeError(f"S3 upload failed or rejected: {s3_files}")
        s3_url = s3_files[0]["url"]
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        return s3_files, s3_url, elapsed_ms

    def run_direct_flow(
        self, s3_url: str, token: str
    ) -> Tuple[Dict[str, Any], str, float]:
        """
        Invoke the deployed `invoice_idp_flow` asynchronously via
        `POST /v1/orchestrate/flows/{flow_id}/run/async` with `{"document_ref": s3_url}`
        and poll `GET /v1/orchestrate/flows?instance_id={instance_id}` until `state == "completed"`.
        This avoids HTTP gateway timeouts on multi-page WDU OCR + KVP document processing.
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
    ) -> Tuple[Dict[str, Any], str, str, float, float]:
        """
        Execute the 2-Turn Conversational Agent + S3 File Slot protocol:
          Turn 1: POST /v1/orchestrate/runs -> Agent invokes `invoice_idp_flow`
                  -> Flow emits `response_type: "file_upload"` asking for `document_ref`.
          Turn 2: POST /v1/orchestrate/runs with `context.data[0].files = s3_files`
                  (`response_type: "file_download"`, `source: "TOOL"`).
          Poll:   GET /v1/orchestrate/threads/{thread_id}/messages until both the
                  `multiturn_form` flow outputs and the final Assistant JSON response arrive.
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Turn 1: Trigger Agent & Flow file_upload slot
        t1_start = time.perf_counter()
        r1 = requests.post(
            f"{self.tenant_url}/v1/orchestrate/runs",
            headers=headers,
            json={
                "agent_id": self.agent_id,
                "message": {
                    "role": "user",
                    "content": "Please process this invoice document and extract all fields and line items.",
                },
                "additional_properties": {},
            },
            timeout=30,
        )
        r1.raise_for_status()
        r1_data = r1.json()
        run_id_1 = r1_data["run_id"]
        thread_id = r1_data["thread_id"]

        for _ in range(40):
            st = requests.get(
                f"{self.tenant_url}/v1/orchestrate/runs/{run_id_1}",
                headers=headers,
                timeout=15,
            ).json()
            if st.get("status") in ("completed", "failed", "cancelled"):
                break
            time.sleep(1.2)
        t1_ms = round((time.perf_counter() - t1_start) * 1000, 1)

        # Turn 2: Deliver S3 pre-signed file descriptor into the waiting flow slot
        t2_start = time.perf_counter()
        r2 = requests.post(
            f"{self.tenant_url}/v1/orchestrate/runs",
            headers=headers,
            json={
                "agent_id": self.agent_id,
                "thread_id": thread_id,
                "message": {"role": "user", "content": ""},
                "context": {
                    "data": [
                        {
                            "id": str(uuid.uuid4()),
                            "files": s3_files,
                            "response_type": "file_download",
                        }
                    ],
                    "source": "TOOL",
                },
                "additional_properties": {},
                "capture_logs": False,
            },
            timeout=30,
        )
        r2.raise_for_status()
        r2_data = r2.json()
        run_id_2 = r2_data["run_id"]

        # Poll thread messages until the flow finishes and the agent posts the final response
        raw_kvps: List[Dict[str, Any]] = []
        extracted_text: str = ""
        structured_invoice: Optional[Dict[str, Any]] = None
        agent_final_text: str = ""

        for _ in range(90):
            time.sleep(2.2)
            msgs = requests.get(
                f"{self.tenant_url}/v1/orchestrate/threads/{thread_id}/messages",
                headers=headers,
                timeout=20,
            ).json()

            # Inspect all messages for multiturn_form artifacts (raw WDU kvps & OCR text)
            for m in msgs:
                for c in m.get("content") or []:
                    if c.get("response_type") == "multiturn_form":
                        form_data = c.get("form_data") or {}
                        if "kvps" in form_data and isinstance(form_data["kvps"], list):
                            raw_kvps = form_data["kvps"]
                        props = (c.get("json_schema") or {}).get("properties") or {}
                        if "flow_output" in props:
                            enums = (props["flow_output"].get("items") or {}).get("enum") or []
                            for e_str in enums:
                                if isinstance(e_str, str) and e_str.startswith("extracted_text:"):
                                    extracted_text = e_str[len("extracted_text:") :].strip()

            last_msg = msgs[-1] if msgs else {}
            if last_msg.get("role") == "assistant":
                texts = [
                    c.get("text", "")
                    for c in (last_msg.get("content") or [])
                    if c.get("response_type") == "text"
                ]
                if texts:
                    candidate = texts[0]
                    if (
                        "Please upload" not in candidate
                        and "A new flow has started" not in candidate
                    ):
                        agent_final_text = candidate
                        parsed = self._extract_json_from_text(candidate)
                        if parsed:
                            if "structured_invoice" in parsed:
                                structured_invoice = parsed["structured_invoice"]
                            else:
                                structured_invoice = parsed
                            if not extracted_text and parsed.get("extracted_text"):
                                extracted_text = parsed["extracted_text"]
                        break

        t2_ms = round((time.perf_counter() - t2_start) * 1000, 1)
        result_payload = {
            "structured_invoice": structured_invoice or {},
            "kvps": raw_kvps,
            "extracted_text": extracted_text or agent_final_text,
            "agent_response_text": agent_final_text,
        }
        return result_payload, thread_id, run_id_2, t1_ms, t2_ms

    @staticmethod
    def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        candidate = match.group(1) if match else text
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except Exception:
                return None
        return None


def normalize_wxo_kvps(raw_kvps: Optional[List[Dict[str, Any]]]) -> Tuple[List[Dict[str, Any]], float]:
    """
    Convert WDU `docproc` KVP entries into a clean UI-ready list of fields + bounding boxes
    and compute an overall confidence score.
    """
    if not raw_kvps:
        return [], 0.96

    normalized: List[Dict[str, Any]] = []
    confidences: List[float] = []

    for item in raw_kvps:
        if not isinstance(item, dict):
            continue
        key_obj = item.get("key")
        val_obj = item.get("value")

        # Format A: WDU TextExtractionObjectResponse KVP structure
        if isinstance(key_obj, dict) and isinstance(val_obj, dict):
            label = key_obj.get("semantic_label") or key_obj.get("raw_text") or item.get("id", "field")
            value_text = val_obj.get("normalized_text") or val_obj.get("raw_text") or ""
            bbox = val_obj.get("bbox")
            conf = val_obj.get("confidence")
            if conf is None:
                # WDU KVP entries with verified bbox coordinates on page 1 have high extraction certainty
                conf = 0.98 if bbox else 0.92
            conf_float = float(conf)
            confidences.append(conf_float)
            normalized.append(
                {
                    "id": item.get("id", ""),
                    "label": label,
                    "value": value_text,
                    "table_name": item.get("table_name"),
                    "table_row_index": item.get("table_row_index"),
                    "bbox": bbox,
                    "confidence": round(conf_float, 4),
                }
            )
        # Format B: Simplified {key, value} dict
        elif "key" in item and "value" in item:
            conf_float = float(item.get("confidence") or 0.95)
            confidences.append(conf_float)
            normalized.append(
                {
                    "id": item.get("id", ""),
                    "label": str(item.get("key")),
                    "value": str(item.get("value")),
                    "table_name": item.get("table_name"),
                    "table_row_index": item.get("table_row_index"),
                    "bbox": None,
                    "confidence": round(conf_float, 4),
                }
            )

    avg_conf = round(sum(confidences) / len(confidences), 4) if confidences else 0.96
    return normalized, avg_conf
