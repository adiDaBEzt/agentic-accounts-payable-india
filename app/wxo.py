"""watsonx Orchestrate REST client: IAM auth, file upload, async flow runs and agent chat."""

import json
import threading
import time
import uuid

import requests

from app import config

IAM_URL = "https://iam.cloud.ibm.com/identity/token"
TERMINAL = ("completed", "failed", "cancelled")


class WxOError(RuntimeError):
    pass


class WxO:
    def __init__(self, instance_url=None, api_key=None):
        self.base = (instance_url or config.WXO_INSTANCE_URL).rstrip("/")
        self.api_key = api_key or config.WXO_API_KEY
        self._token = None
        self._expiry = 0.0
        self._ids: dict[str, str] = {}
        self._lock = threading.Lock()

    # ---- plumbing --------------------------------------------------------------------
    def token(self) -> str:
        with self._lock:
            if not self._token or time.time() > self._expiry - 300:
                r = requests.post(IAM_URL, timeout=20, data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": self.api_key})
                r.raise_for_status()
                body = r.json()
                self._token, self._expiry = body["access_token"], float(body["expiration"])
            return self._token

    def _req(self, method, path, **kw):
        headers = {"Authorization": f"Bearer {self.token()}", "Accept": "application/json", **kw.pop("headers", {})}
        r = requests.request(method, f"{self.base}/v1/orchestrate{path}", headers=headers, timeout=kw.pop("timeout", 30), **kw)
        if r.status_code >= 400:
            raise WxOError(f"{method} {path} → {r.status_code}: {r.text[:300]}")
        return r.json() if r.content else {}

    def ping(self) -> dict:
        self.token()
        return {"connected": True, "instance": self.base.split("/instances/")[-1][:8], "region": self.base.split(".")[1]}

    # ---- assets ----------------------------------------------------------------------
    def flow_id(self, name: str) -> str:
        if name not in self._ids:
            tools = self._req("GET", "/tools")
            match = next((t for t in tools if t.get("name") == name), None)
            if not match:
                raise WxOError(f"Flow '{name}' is not deployed. Run wxo/deploy.sh first.")
            self._ids[name] = match["binding"]["flow"]["flow_id"]
        return self._ids[name]

    def agent_id(self, name: str) -> str:
        key = f"agent:{name}"
        if key not in self._ids:
            agents = self._req("GET", "/agents")
            match = next((a for a in agents if a.get("name") == name), None)
            if not match:
                raise WxOError(f"Agent '{name}' is not deployed. Run wxo/deploy.sh first.")
            self._ids[key] = match["id"]
        return self._ids[key]

    # ---- document flow ---------------------------------------------------------------
    def upload(self, data: bytes, filename: str) -> str:
        """Upload a document to the tenant's object storage; returns the pre-signed document_ref URL."""
        meta = [{"fileName": filename, "invalid": False, "id": str(uuid.uuid4()), "statusCode": 200,
                 "uploadStatus": "uploading", "url": ""}]
        files = self._req("POST", "/upload-to-s3", timeout=90,
                          files={"files": (filename, data, "application/octet-stream")},
                          data={"text": "", "fileMetaData": json.dumps(meta)})
        if not files or files[0].get("invalid"):
            raise WxOError(f"Upload rejected: {files}")
        return files[0]["url"]

    def run_flow(self, name: str, payload: dict, on_progress=None, timeout_s: int = 300) -> dict:
        """Start a flow asynchronously and poll it. 'interrupted' means a node (e.g. docproc) is
        awaiting an async callback, not that the run failed."""
        fid = self.flow_id(name)
        instance_id = self._req("POST", f"/flows/{fid}/run/async", json=payload,
                                headers={"Content-Type": "application/json"})["instance_id"]
        deadline = time.time() + timeout_s
        seen = set()
        while time.time() < deadline:
            time.sleep(2.0)
            inst = (self._req("GET", "/flows", params={"instance_id": instance_id}) or [{}])[0]
            for t in inst.get("tasks") or []:
                if t.get("state") == "completed" and t["name"] not in seen and not t["name"].startswith("__"):
                    seen.add(t["name"])
                    if on_progress:
                        on_progress(t["name"])
            if inst.get("state") in TERMINAL:
                if inst["state"] != "completed":
                    raise WxOError(f"Flow {instance_id} {inst['state']}: {inst.get('error')}")
                nodes = [{"name": t["name"], "duration_ms": (t.get("trace_context") or {}).get("duration_ms", 0)}
                         for t in inst.get("tasks") or [] if not t["name"].startswith("__")]
                return {"instance_id": instance_id, "output": inst.get("output") or {}, "nodes": nodes,
                        "duration_ms": (inst.get("trace_context") or {}).get("duration_ms", 0)}
        raise WxOError(f"Flow {instance_id} timed out after {timeout_s}s")

    # ---- agent chat ------------------------------------------------------------------
    def chat(self, agent_name: str, message: str, thread_id: str | None = None, timeout_s: int = 120) -> dict:
        body = {"agent_id": self.agent_id(agent_name), "message": {"role": "user", "content": message}}
        if thread_id:
            body["thread_id"] = thread_id
        run = self._req("POST", "/runs", json=body, headers={"Content-Type": "application/json"})
        run_id, thread_id = run["run_id"], run["thread_id"]
        deadline = time.time() + timeout_s
        status = {}
        while time.time() < deadline:
            time.sleep(1.2)
            status = self._req("GET", f"/runs/{run_id}")
            if status.get("status") in TERMINAL:
                break
        if status.get("status") != "completed":
            raise WxOError(f"Agent run {status.get('status', 'timed out')}: {status.get('last_error') or ''}")
        messages = self._req("GET", f"/threads/{thread_id}/messages")
        reply, tools = "", []
        for m in reversed(messages):
            if m.get("role") != "assistant":
                break
            for c in m.get("content") or []:
                if c.get("response_type") == "text" and not reply:
                    reply = c.get("text", "")
            for step in (m.get("step_history") or []):
                for d in step.get("step_details") or []:
                    for call in d.get("tool_calls") or []:
                        tools.append(call.get("name"))
        return {"reply": reply, "thread_id": thread_id, "tools": sorted(set(filter(None, tools)))}
