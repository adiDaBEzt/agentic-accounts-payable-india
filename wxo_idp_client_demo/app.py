"""
Standalone FastAPI Application for IBM watsonx Orchestrate IDP Client Demo.

Zero external ERP or email dependencies. Pure watsonx Orchestrate IDP pipeline
demonstrating WDU OCR, KVP extraction, Python Logic audit, and GenAI structuring.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.database import (
    delete_document_by_id,
    get_document_by_id,
    init_db,
    list_documents,
    save_document_record,
)
from backend.wxo_client import AGENT_ID, FLOW_ID, TENANT_URL, WxOClient, normalize_wxo_kvps

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
SAMPLES_DIR = ROOT_DIR / "samples"

app = FastAPI(
    title="IBM watsonx Orchestrate — Intelligent Document Processing (IDP)",
    version="1.0.0",
    description="Client Demo Application for watsonx Orchestrate Agentic Multi-Document Flow.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

wxo_client = WxOClient()


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "tenant_url": TENANT_URL,
        "flow_id": FLOW_ID,
        "agent_id": AGENT_ID,
        "flow_name": "invoice_idp_flow",
        "agent_name": "invoice_idp_agent",
    }


@app.get("/api/samples")
def get_sample_documents():
    """List sample PDFs and PNGs available in samples/ folder."""
    samples = []
    if SAMPLES_DIR.exists():
        for f in sorted(SAMPLES_DIR.glob("*.pdf")):
            name = f.name
            doc_type = "Invoice"
            if "po_" in name.lower():
                doc_type = "Purchase Order"
            elif "receipt_" in name.lower():
                doc_type = "Receipt"

            samples.append(
                {
                    "filename": name,
                    "document_type": doc_type,
                    "title": name.replace(".pdf", "").replace("_", " ").title(),
                    "pdf_url": f"/samples/{name}",
                    "png_url": f"/samples/{name.replace('.pdf', '.png')}",
                }
            )
    return {"samples": samples}


@app.post("/api/process")
async def api_process_document(
    file: Optional[UploadFile] = File(None),
    sample_filename: Optional[str] = Form(None),
    execution_mode: str = Form("direct_flow"),
):
    """
    Process document through watsonx Orchestrate IDP:
    1. Read bytes (from upload or sample)
    2. Upload to S3 COS pre-signed bucket
    3. Execute direct_flow or agent_two_turn
    4. Save to local SQLite
    5. Return structured result with telemetry
    """
    telemetry: List[Dict[str, Any]] = []

    # 1. Acquire bytes
    if file and file.filename:
        filename = file.filename
        file_bytes = await file.read()
    elif sample_filename:
        sample_path = SAMPLES_DIR / sample_filename
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail=f"Sample {sample_filename} not found")
        filename = sample_path.name
        file_bytes = sample_path.read_bytes()
    else:
        raise HTTPException(status_code=400, detail="No file or sample provided")

    try:
        # 2. IAM Token
        token, token_ms = wxo_client.get_iam_token()
        telemetry.append(
            {
                "step": 1,
                "name": "IBM Cloud IAM Authentication",
                "endpoint": "POST https://iam.cloud.ibm.com/identity/token",
                "duration_ms": token_ms,
                "status": "completed",
                "detail": "Retrieved Bearer OAuth token",
            }
        )

        # 3. S3 COS Upload
        s3_files, s3_url, s3_ms = wxo_client.upload_file_to_s3(file_bytes, filename, token)
        telemetry.append(
            {
                "step": 2,
                "name": "watsonx S3 Upload",
                "endpoint": "POST /v1/orchestrate/upload-to-s3",
                "duration_ms": s3_ms,
                "status": "completed",
                "detail": f"Uploaded {filename} to IBM COS (File key: {s3_files[0].get('key', 'uploaded')})",
            }
        )

        # 4. Execute Flow or Agent
        if execution_mode == "agent_two_turn":
            flow_data, thread_id, run_id, t1_ms, t2_ms = wxo_client.run_agent_two_turn(s3_files, token)
            telemetry.append(
                {
                    "step": 3,
                    "name": "Conversational Agent 2-Turn Execution",
                    "endpoint": "POST /v1/orchestrate/runs",
                    "duration_ms": round(t1_ms + t2_ms, 1),
                    "status": "completed",
                    "detail": f"Agent {AGENT_ID} executed invoice_idp_flow tool (Thread: {thread_id[:8]}...)",
                }
            )
        else:
            flow_data, instance_id, flow_ms = wxo_client.run_direct_flow(s3_url, token)
            telemetry.append(
                {
                    "step": 3,
                    "name": "Headless Direct Flow Execution",
                    "endpoint": f"POST /v1/orchestrate/flows/{FLOW_ID}/run/async",
                    "duration_ms": flow_ms,
                    "status": "completed",
                    "detail": f"Async flow instance {instance_id} completed (docproc + Logic + GenAI)",
                }
            )

        raw_kvps = flow_data.get("kvps") or []
        normalized_kvps, avg_conf = normalize_wxo_kvps(raw_kvps)
        structured_doc = flow_data.get("structured_invoice") or {}
        logic_summary = flow_data.get("logic_summary") or {}
        extracted_text = flow_data.get("extracted_text") or ""

        # 5. Local Database Persistence
        saved_record = save_document_record(
            structured_doc=structured_doc,
            kvps=normalized_kvps,
            extracted_text=extracted_text,
            execution_mode=execution_mode,
            file_name=filename,
            s3_url=s3_url,
            avg_confidence=avg_conf,
            logic_summary=logic_summary,
            telemetry=telemetry,
        )

        return {
            "status": "success",
            "document": saved_record,
            "structured_invoice": structured_doc,
            "logic_summary": logic_summary,
            "kvps": normalized_kvps,
            "avg_confidence": avg_conf,
            "extracted_text": extracted_text,
            "telemetry": telemetry,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices")
def api_list_documents():
    return {"documents": list_documents()}


@app.get("/api/invoices/{doc_id}")
def api_get_document(doc_id: int):
    doc = get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.delete("/api/invoices/{doc_id}")
def api_delete_document(doc_id: int):
    success = delete_document_by_id(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "id": doc_id}


# Static files mount
if SAMPLES_DIR.exists():
    app.mount("/samples", StaticFiles(directory=str(SAMPLES_DIR)), name="samples")
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Frontend not found"}


if __name__ == "__main__":
    import uvicorn
    print("\nStarting IBM watsonx Orchestrate IDP Client Demo on http://127.0.0.1:8000 ...\n")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
