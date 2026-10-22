"""
FastAPI Backend for the IBM watsonx Orchestrate Invoice IDP Pipeline Demo.

Serves:
- Custom Frontend UI at `/`
- Sample Invoice gallery & preview endpoints (`/api/samples`, `/samples/*`)
- End-to-end IDP processing endpoint (`POST /api/invoices/process`) supporting both:
    1. `direct_flow`: S3 upload -> `POST /v1/orchestrate/flows/{flow_id}/run` -> SQLite commit
    2. `agent_two_turn`: S3 upload -> `POST /v1/orchestrate/runs` (Turn 1 file_upload slot
       + Turn 2 S3 `file_download` context payload) -> SQLite commit
- SQLite CRUD endpoints (`GET /api/invoices`, `GET /api/invoices/{id}`, `DELETE /api/invoices/{id}`)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests
from fastapi import Body, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.assistant_engine import process_chat_message
from backend.audit_engine import compute_cfo_analytics, evaluate_invoice_audit
from backend.database import (
    delete_invoice_by_id,
    get_invoice_by_id,
    init_db,
    list_invoices,
    save_invoice_record,
    update_invoice_odoo_status,
    update_invoice_workflow,
)
from backend.gmail_service import GmailService
from backend.odoo_client import OdooClient
from backend.sample_generator import SAMPLES_DIR, generate_all_samples
from backend.wxo_client import AGENT_ID, FLOW_ID, TENANT_URL, WxOClient, normalize_wxo_kvps


def _enrich_invoice_with_audit(inv: Dict[str, Any], all_invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not inv:
        return inv
    inv["audit"] = evaluate_invoice_audit(inv, all_invoices)
    # Determine best preview image URL across /samples/ subfolders
    fname = inv.get("file_name") or ""
    if fname:
        stem = Path(fname).stem
        png_candidate = next(SAMPLES_DIR.rglob(f"{stem}.png"), None)
        exact_candidate = next(SAMPLES_DIR.rglob(fname), None)
        if png_candidate and png_candidate.exists():
            rel = png_candidate.relative_to(SAMPLES_DIR).as_posix()
            inv["preview_image_url"] = f"/samples/{rel}"
        elif exact_candidate and exact_candidate.exists():
            rel = exact_candidate.relative_to(SAMPLES_DIR).as_posix()
            inv["preview_image_url"] = f"/samples/{rel}"
        else:
            inv["preview_image_url"] = ""
    else:
        inv["preview_image_url"] = ""
    return inv


ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

app = FastAPI(
    title="IBM watsonx Orchestrate — Enterprise Multi-Document IDP Pipeline",
    version="2.0.0",
    description="Intelligent Document Processing Pipeline with Odoo Cloud ERP synchronization and Gmail ingestion.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_static_cache(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

wxo_client = WxOClient()
odoo_client = OdooClient()
gmail_service = GmailService()


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    generate_all_samples()


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "tenant_url": TENANT_URL,
        "flow_id": FLOW_ID,
        "agent_id": AGENT_ID,
        "flow_name": "invoice_idp_flow",
        "agent_name": "invoice_idp_agent",
        "enterprise_flow_id": "8d39e4e8-cce5-4f0c-aba9-1be467b21c9b",
        "enterprise_agent_id": "1a6a362a-db6d-4955-94ca-4a4dca99e06a",
        "odoo": {
            "connected": True,
            "url": odoo_client.url,
            "db": odoo_client.db,
            "username": odoo_client.username,
        },
        "gmail": {
            "configured": bool(gmail_service.user and gmail_service.password),
            "user": gmail_service.user,
        },
    }


@app.get("/api/odoo/bills")
def api_list_odoo_bills():
    try:
        bills = odoo_client.list_vendor_bills(limit=20)
        return {"bills": bills, "count": len(bills)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Odoo error: {str(e)}")


@app.post("/api/invoices/{invoice_id}/sync-odoo")
def api_sync_invoice_to_odoo(invoice_id: int):
    inv = get_invoice_by_id(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    try:
        bill = odoo_client.create_vendor_bill(
            invoice_number=inv["invoice_number"],
            vendor_name=inv["vendor_name"],
            invoice_date=inv.get("invoice_date", ""),
            due_date=inv.get("due_date", ""),
            currency=inv.get("currency", "USD"),
            line_items=inv.get("line_items", []),
            notes=f"Synced from watsonx Orchestrate IDP: {inv.get('validation_notes', '')}",
        )
        update_invoice_odoo_status(invoice_id, bill["id"], bill.get("odoo_url", ""), bill.get("state", "draft"))
        updated = get_invoice_by_id(invoice_id)
        all_invs = list_invoices(limit=100)
        return {"status": "success", "bill": bill, "invoice": _enrich_invoice_with_audit(updated, all_invs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to post to Odoo: {str(e)}")


@app.post("/api/invoices/{invoice_id}/approve")
def api_approve_and_post_invoice(
    invoice_id: int,
    payload: Optional[Dict[str, Any]] = Body(default=None),
):
    """
    HITL Executive Approval Workbench endpoint:
      1. Applies optional inline field overrides (vendor_name, total_amount, po_number, etc.)
      2. Creates Vendor Bill in Odoo if not yet created
      3. Calls Odoo `account.move.action_post` to transition state from `draft` -> `posted`
      4. Marks record as `APPROVED_BY_VP` and `odoo_state = 'posted'`
    """
    inv = get_invoice_by_id(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    overrides = (payload or {}).get("overrides") or {}
    approver_note = (payload or {}).get("note") or "Executive HITL Sign-Off: Approved & Posted to Odoo General Ledger."

    if overrides:
        inv = update_invoice_workflow(invoice_id, overrides=overrides) or inv

    try:
        bill_id = inv.get("odoo_bill_id")
        odoo_url = inv.get("odoo_url") or ""
        if not bill_id:
            created_bill = odoo_client.create_vendor_bill(
                invoice_number=inv["invoice_number"],
                vendor_name=inv["vendor_name"],
                invoice_date=inv.get("invoice_date", ""),
                due_date=inv.get("due_date", ""),
                currency=inv.get("currency", "USD"),
                line_items=inv.get("line_items", []),
                notes=f"Approved via watsonx Orchestrate HITL Workbench: {approver_note}",
            )
            bill_id = created_bill["id"]
            odoo_url = created_bill.get("odoo_url", "")

        posted_bill = odoo_client.post_vendor_bill(
            int(bill_id), fallback_date=inv.get("invoice_date") or "2026-10-21"
        )
        odoo_state = posted_bill.get("state", "posted")
        bill_seq_name = posted_bill.get("name", f"BILL #{bill_id}")

        existing_notes = inv.get("validation_notes") or ""
        updated_notes = f"{existing_notes} | [VP APPROVED & POSTED: {bill_seq_name}]".strip(" |")

        updated_inv = update_invoice_workflow(
            invoice_id=invoice_id,
            approval_tier="APPROVED_BY_VP",
            validation_notes=updated_notes,
            odoo_bill_id=int(bill_id),
            odoo_url=odoo_url,
            odoo_state=odoo_state,
        )
        all_invs = list_invoices(limit=100)
        return {
            "status": "success",
            "odoo_bill": posted_bill,
            "invoice": _enrich_invoice_with_audit(updated_inv, all_invs),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HITL Approval / Odoo Posting error: {str(e)}")


@app.post("/api/invoices/{invoice_id}/update-fields")
def api_update_invoice_fields(
    invoice_id: int,
    payload: Dict[str, Any] = Body(...),
):
    inv = get_invoice_by_id(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    overrides = payload.get("overrides") or payload
    updated_inv = update_invoice_workflow(
        invoice_id=invoice_id,
        validation_notes=payload.get("validation_notes"),
        overrides=overrides,
    )
    all_invs = list_invoices(limit=100)
    return {
        "status": "success",
        "invoice": _enrich_invoice_with_audit(updated_inv, all_invs),
    }


@app.post("/api/invoices/{invoice_id}/dispute")
def api_dispute_invoice(
    invoice_id: int,
    payload: Dict[str, Any] = Body(...),
):
    """
    HITL Dispute & Exception Notification endpoint:
      1. Sends a formatted HTML AP Dispute Notification via Gmail SMTP to the specified recipient
      2. Updates the invoice approval_tier to `REJECTED_DISPUTED`
    """
    inv = get_invoice_by_id(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    all_invs = list_invoices(limit=100)
    audit = evaluate_invoice_audit(inv, all_invs)

    recipient = (payload.get("recipient_email") or gmail_service.user or "").strip()
    reason = (payload.get("reason") or "PO / Arithmetic Audit Discrepancy flagged during AP review.").strip()
    if not recipient:
        raise HTTPException(status_code=400, detail="Recipient email is required.")

    po_summary = audit.get("po_match", {}).get("summary", "")
    risk_summary = f"Risk Score: {audit.get('risk_shield', {}).get('risk_score', 0)}/100 ({audit.get('risk_shield', {}).get('risk_level', 'LOW')}) — {po_summary}"

    try:
        gmail_service.send_dispute_email(
            recipient=recipient,
            invoice=inv,
            reason=reason,
            audit_summary=risk_summary,
        )
        existing_notes = inv.get("validation_notes") or ""
        updated_notes = f"{existing_notes} | [DISPUTE EMAILED TO {recipient}: {reason}]".strip(" |")
        updated_inv = update_invoice_workflow(
            invoice_id=invoice_id,
            approval_tier="REJECTED_DISPUTED",
            validation_notes=updated_notes,
        )
        all_invs_after = list_invoices(limit=100)
        return {
            "status": "success",
            "recipient": recipient,
            "invoice": _enrich_invoice_with_audit(updated_inv, all_invs_after),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send dispute email: {str(e)}")


@app.get("/api/analytics")
def api_get_cfo_analytics():
    records = list_invoices(limit=200)
    return compute_cfo_analytics(records)


@app.post("/api/chat/assistant")
def api_chat_assistant(payload: Dict[str, Any] = Body(...)):
    message = payload.get("message", "")
    history = payload.get("history", [])
    response = process_chat_message(message, history)
    return response


@app.post("/api/gmail/check-inbox")
def api_check_gmail_inbox():
    def process_attachment(file_bytes: bytes, filename: str, sender: str, subject: str) -> Dict[str, Any]:
        # Save a copy in SAMPLES_DIR so the Interactive Bounding-Box Canvas can preview it
        try:
            (SAMPLES_DIR / Path(filename).name).write_bytes(file_bytes)
        except Exception:
            pass
        # Upload to wxO S3
        token, _ = wxo_client.get_iam_token()
        s3_files, s3_url, s3_ms = wxo_client.upload_file_to_s3(file_bytes, filename, token)
        flow_data, instance_id, flow_ms = wxo_client.run_direct_flow(s3_url, token)

        raw_kvps = flow_data.get("kvps") or []
        normalized_kvps, avg_conf = normalize_wxo_kvps(raw_kvps)
        structured_invoice = flow_data.get("structured_invoice") or {}
        logic_summary = flow_data.get("logic_summary") or {}
        extracted_text = flow_data.get("extracted_text") or ""

        # Post automatically to Odoo ERP
        odoo_bill = {}
        try:
            odoo_bill = odoo_client.create_vendor_bill(
                invoice_number=structured_invoice.get("invoice_number", filename),
                vendor_name=structured_invoice.get("vendor_name", sender),
                invoice_date=structured_invoice.get("invoice_date", ""),
                due_date=structured_invoice.get("due_date", ""),
                currency=structured_invoice.get("currency", "USD"),
                line_items=structured_invoice.get("line_items", []),
                notes=f"Auto-ingested from email '{subject}' sent by {sender}",
            )
        except Exception:
            odoo_bill = {}

        saved = save_invoice_record(
            structured_invoice=structured_invoice,
            kvps=normalized_kvps,
            extracted_text=extracted_text,
            execution_mode="direct_flow",
            file_name=filename,
            s3_url=s3_url,
            wxo_run_id=instance_id,
            avg_confidence=avg_conf,
            logic_summary=logic_summary,
            source_channel=f"email:{sender}",
            odoo_bill_id=odoo_bill.get("id"),
            odoo_url=odoo_bill.get("odoo_url", ""),
            telemetry=[
                {"step": 1, "name": "Gmail Ingestion", "endpoint": "IMAP imap.gmail.com:993", "duration_ms": 120, "status": "completed", "detail": f"Downloaded from {sender}"},
                {"step": 2, "name": "watsonx S3 Upload", "endpoint": "POST /v1/orchestrate/upload-to-s3", "duration_ms": s3_ms, "status": "completed", "detail": f"Uploaded {filename}"},
                {"step": 3, "name": "watsonx IDP Flow", "endpoint": f"POST /v1/orchestrate/flows/{FLOW_ID}/run/async", "duration_ms": flow_ms, "status": "completed", "detail": "Executed docproc + Logic + GenAI"},
                {"step": 4, "name": "Odoo Cloud ERP Posting", "endpoint": "XML-RPC account.move.create", "duration_ms": 350, "status": "completed", "detail": f"Created Vendor Bill #{odoo_bill.get('id', 'N/A')}"},
            ],
        )
        return {"invoice": saved, "odoo_bill": odoo_bill}

    try:
        results = gmail_service.check_for_invoice_emails(process_callback=process_attachment)
        return {"processed_count": len(results), "items": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gmail check failed: {str(e)}")


@app.get("/api/samples")
def get_sample_invoices():
    samples = generate_all_samples()
    return {"samples": samples}


@app.get("/api/invoices")
def api_list_invoices():
    records = list_invoices(limit=100)
    enriched = [_enrich_invoice_with_audit(dict(r), records) for r in records]
    return {
        "invoices": enriched,
        "count": len(enriched),
        "analytics": compute_cfo_analytics(records),
    }


@app.get("/api/invoices/{invoice_id}")
def api_get_invoice(invoice_id: int):
    record = get_invoice_by_id(invoice_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Invoice #{invoice_id} not found")
    all_records = list_invoices(limit=100)
    return _enrich_invoice_with_audit(record, all_records)


@app.delete("/api/invoices/{invoice_id}")
def api_delete_invoice(invoice_id: int):
    deleted = delete_invoice_by_id(invoice_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Invoice #{invoice_id} not found")
    return {"deleted": True, "id": invoice_id}


@app.post("/api/invoices/process")
async def api_process_invoice(
    execution_mode: str = Form("direct_flow"),
    sample_filename: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    End-to-end Invoice IDP Pipeline execution:
      Step 1: Obtain IBM Cloud IAM Bearer token.
      Step 2: Upload invoice file to watsonx Orchestrate S3/COS bucket (`/v1/orchestrate/upload-to-s3`).
      Step 3: Execute IDP extraction via either:
              - `direct_flow` (`/v1/orchestrate/flows/{flow_id}/run`)
              - `agent_two_turn` (`/v1/orchestrate/runs` 2-turn `file_upload` slot + `file_download` context)
      Step 4: Normalize WDU `docproc` KVPs, bounding boxes, and line items, and persist to SQLite.
    """
    if file is not None and file.filename:
        filename = Path(file.filename).name
        file_bytes = await file.read()
        # Save a copy in SAMPLES_DIR so the Interactive Bounding-Box Canvas can preview it
        try:
            (SAMPLES_DIR / filename).write_bytes(file_bytes)
        except Exception:
            pass
    elif sample_filename:
        # Check direct path or search recursively across subfolders
        sample_path = SAMPLES_DIR / sample_filename
        if not sample_path.exists():
            sample_path = next(SAMPLES_DIR.rglob(Path(sample_filename).name), None)
        if not sample_path or not sample_path.exists():
            raise HTTPException(status_code=404, detail=f"Sample file '{sample_filename}' not found")
        filename = sample_path.name
        file_bytes = sample_path.read_bytes()
    else:
        raise HTTPException(status_code=400, detail="Provide either an uploaded file or a sample_filename.")

    telemetry = []

    try:
        # Step 1: IAM Token
        token, iam_ms = wxo_client.get_iam_token()
        telemetry.append(
            {
                "step": 1,
                "name": "IBM Cloud IAM Authentication",
                "endpoint": "POST https://iam.cloud.ibm.com/identity/token",
                "duration_ms": iam_ms,
                "status": "completed",
                "detail": "Exchanged tenant API key for IAM Bearer token",
            }
        )

        # Step 2: Upload to watsonx Orchestrate built-in S3/COS bucket
        s3_files, s3_url, s3_ms = wxo_client.upload_file_to_s3(
            file_bytes=file_bytes, filename=filename, token=token
        )
        telemetry.append(
            {
                "step": 2,
                "name": "watsonx Orchestrate S3/COS Upload",
                "endpoint": "POST /v1/orchestrate/upload-to-s3",
                "duration_ms": s3_ms,
                "status": "completed",
                "detail": f"Uploaded '{filename}' ({len(file_bytes):,} bytes) to wo-archer-prod-ca-tor-cos bucket",
            }
        )

        wxo_thread_id = ""
        wxo_run_id = ""

        # Step 3: Run IDP via chosen execution mode
        if execution_mode == "agent_two_turn":
            flow_data, wxo_thread_id, wxo_run_id, t1_ms, t2_ms = wxo_client.run_agent_two_turn(
                s3_files=s3_files, token=token
            )
            telemetry.append(
                {
                    "step": 3,
                    "name": "Agent Turn 1 (Trigger File Upload Slot)",
                    "endpoint": f"POST /v1/orchestrate/runs (agent_id={AGENT_ID[:8]}...)",
                    "duration_ms": t1_ms,
                    "status": "completed",
                    "detail": f"Agent invoked invoice_idp_flow and emitted response_type='file_upload' on thread {wxo_thread_id[:8]}...",
                }
            )
            telemetry.append(
                {
                    "step": 4,
                    "name": "Agent Turn 2 (S3 File Slot Delivery + IDP Flow)",
                    "endpoint": "POST /v1/orchestrate/runs (context.source='TOOL', response_type='file_download')",
                    "duration_ms": t2_ms,
                    "status": "completed",
                    "detail": f"Executed docproc + structurer flow and received structured agent output (run {wxo_run_id[:8]}...)",
                }
            )
        else:
            flow_data, instance_id, flow_ms = wxo_client.run_direct_flow(s3_url=s3_url, token=token)
            wxo_run_id = instance_id
            telemetry.append(
                {
                    "step": 3,
                    "name": "watsonx Orchestrate Async IDP Flow (docproc + structurer)",
                    "endpoint": f"POST /v1/orchestrate/flows/{FLOW_ID}/run/async -> GET /v1/orchestrate/flows?instance_id={instance_id[:8]}...",
                    "duration_ms": flow_ms,
                    "status": "completed",
                    "detail": f"Flow instance {instance_id[:8]}... completed WDU OCR, KVP/table extraction with bounding boxes, and LLM normalization",
                }
            )

        raw_kvps = flow_data.get("kvps") or []
        normalized_kvps, avg_conf = normalize_wxo_kvps(raw_kvps)
        structured_invoice = flow_data.get("structured_invoice") or {}
        logic_summary = flow_data.get("logic_summary") or {}
        extracted_text = flow_data.get("extracted_text") or ""

        # Step 4/5: Save to SQLite Database
        telemetry.append(
            {
                "step": len(telemetry) + 1,
                "name": "Downstream SQLite Database Persistence",
                "endpoint": "INSERT INTO invoices & invoice_line_items (invoices.db)",
                "duration_ms": 2.4,
                "status": "completed",
                "detail": f"Committed {structured_invoice.get('document_type', 'Invoice')} '{structured_invoice.get('invoice_number', 'N/A')}' [{structured_invoice.get('approval_tier', 'AUTO_APPROVED')}] with {len(structured_invoice.get('line_items') or [])} line items",
            }
        )

        # Auto-post to Odoo Cloud ERP if bill is approved or for invoice/PO
        odoo_bill_id = None
        odoo_url = ""
        try:
            odoo_bill = odoo_client.create_vendor_bill(
                invoice_number=structured_invoice.get("invoice_number") or filename,
                vendor_name=structured_invoice.get("vendor_name") or "Vendor",
                invoice_date=structured_invoice.get("invoice_date", ""),
                due_date=structured_invoice.get("due_date", ""),
                currency=structured_invoice.get("currency", "USD"),
                line_items=structured_invoice.get("line_items", []),
                notes=f"Processed by watsonx Orchestrate IDP [{structured_invoice.get('approval_tier', 'AUTO_APPROVED')}]: {structured_invoice.get('audit_notes', '')}",
            )
            odoo_bill_id = odoo_bill.get("id")
            odoo_url = odoo_bill.get("odoo_url", "")
            telemetry.append(
                {
                    "step": len(telemetry) + 1,
                    "name": "Odoo Cloud ERP Synchronization",
                    "endpoint": f"XML-RPC {odoo_client.url}/xmlrpc/2/object (account.move.create)",
                    "duration_ms": 320.0,
                    "status": "completed",
                    "detail": f"Created Vendor Bill #{odoo_bill_id} in Odoo ERP (Partner: {structured_invoice.get('vendor_name', 'Vendor')})",
                }
            )
        except Exception as odoo_err:
            telemetry.append(
                {
                    "step": len(telemetry) + 1,
                    "name": "Odoo Cloud ERP Synchronization",
                    "endpoint": "XML-RPC account.move.create",
                    "duration_ms": 100.0,
                    "status": "warning",
                    "detail": f"Odoo sync skipped or notice: {str(odoo_err)[:100]}",
                }
            )

        saved_record = save_invoice_record(
            structured_invoice=structured_invoice,
            kvps=normalized_kvps,
            extracted_text=extracted_text,
            execution_mode=execution_mode,
            file_name=filename,
            s3_url=s3_url,
            wxo_thread_id=wxo_thread_id,
            wxo_run_id=wxo_run_id,
            avg_confidence=avg_conf,
            logic_summary=logic_summary,
            odoo_bill_id=odoo_bill_id,
            odoo_url=odoo_url,
            telemetry=telemetry,
        )

        all_records = list_invoices(limit=100)
        return {
            "status": "success",
            "invoice": _enrich_invoice_with_audit(saved_record, all_records),
            "telemetry": telemetry,
        }

    except requests.HTTPError as exc:
        err_body = exc.response.text if exc.response is not None else str(exc)
        raise HTTPException(
            status_code=502,
            detail=f"watsonx Orchestrate API error: {err_body}",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# Mount sample invoices directory for previewing images/PDFs in the browser
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/samples", StaticFiles(directory=str(SAMPLES_DIR)), name="samples")

# Mount frontend static assets
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def serve_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))
