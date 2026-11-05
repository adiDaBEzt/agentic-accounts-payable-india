"""Workbench side of the process:

    intake → wxO object storage → ap_invoice_processing_flow (extract · GST checks · TDS classification ·
    ERP controls · routing decision table · Odoo bill posted | held | blocked) → notify the supplier

Reviewer actions on held bills (approve / reject / email) and the ERP sync run here.
"""

import html
import shutil
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

from apcore import controls
from apcore.india import inr
from apcore.odoo import Odoo
from app import config, mail, store
from app.wxo import WxO

wxo = WxO()
odoo = Odoo(config.ODOO_URL, config.ODOO_DB, config.ODOO_USERNAME, config.ODOO_PASSWORD)
_pool = ThreadPoolExecutor(max_workers=3)



# ---- intake ------------------------------------------------------------------------------
def submit(data: bytes, filename: str, source: str = "upload", meta: dict | None = None) -> dict:
    safe = Path(filename).name.replace(" ", "_")
    path = config.UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{safe}"
    path.write_bytes(data)
    doc = store.create(source=source, file_name=safe, file_path=str(path), preview_path=_preview(path),
                       status="processing", stage="received", meta=meta or {})
    store.log(doc["id"], "intake", "done", f"Received {safe} via {source} ({len(data) / 1024:.0f} KB)")
    _pool.submit(_run, doc["id"])
    return store.get(doc["id"])


def _preview(path: Path) -> str:
    out = path.with_suffix(".preview.png")
    if path.suffix.lower() == ".pdf":
        pdfium.PdfDocument(str(path))[0].render(scale=2).to_pil().save(out)
    else:
        Image.open(path).convert("RGB").save(out)
    return str(out)


# ---- processing --------------------------------------------------------------------------
def _run(doc_id: int) -> None:
    doc = store.get(doc_id)
    try:
        t0 = time.perf_counter()
        store.update(doc_id, stage="extracting")
        ref = wxo.upload(Path(doc["file_path"]).read_bytes(), doc["file_name"])
        store.log(doc_id, "upload", "done", "Stored in watsonx Orchestrate object storage", _ms(t0))

        t1 = time.perf_counter()
        store.log(doc_id, "flow", "running", "ap_invoice_processing_flow started")
        run = wxo.run_flow(config.WXO_FLOW_NAME, {"document_ref": ref},
                           on_progress=lambda node: store.log(doc_id, "flow", "running", f"{node} complete"))
        out = run["output"]
        inv = out.get("invoice") or {}
        booked = out.get("posted") or out.get("held") or {}
        result = booked.pop("controls", None) or out.get("controls") or {}
        result.update(decision=out.get("route") or "exception", route_reason=out.get("route_reason") or "")
        erp = booked
        if result["decision"] == "blocked":
            dup = next((c for c in result.get("checks", []) if c["code"] == "DUP-01"), {})
            erp = {"summary": "Blocked — no bill created", "bill": None, "reason": dup.get("detail", "")}
        extraction = {k: v for k, v in out.items() if k not in ("controls", "posted", "held", "route", "route_reason")}
        fails = [c for c in result.get("checks", []) if c["status"] == "fail"]
        store.log(doc_id, "flow", "done", f"Flow instance {run['instance_id'][:8]} · route: {result['decision']}",
                  _ms(t1), instance_id=run["instance_id"],
                  nodes=[{**n, "label": n["name"]} for n in run["nodes"]])
        store.log(doc_id, "controls", "done", f"{len(result.get('checks', []))} controls · {len(fails)} exception(s)"
                  + (f" · {result['route_reason']}" if result["route_reason"] else ""))
        store.log(doc_id, "erp", "done", erp.get("summary", ""))
        status = {"touchless": "posted", "exception": "exception", "blocked": "blocked"}[result["decision"]]
        store.update(doc_id, status=status, stage="done", extraction=extraction, controls=result, erp=erp,
                     vendor=inv.get("supplier_name"), invoice_number=inv.get("invoice_number"),
                     invoice_date=inv.get("invoice_date"), total=inv.get("total_amount"),
                     meta={**doc["meta"], "cycle_seconds": round(time.perf_counter() - t0, 1)})
        _acknowledge(store.get(doc_id))
    except Exception as exc:  # surfaced in the UI with the failing step
        store.log(doc_id, "error", "failed", str(exc)[:400])
        store.update(doc_id, status="failed", error=str(exc)[:400])


def _ms(t: float) -> float:
    return round((time.perf_counter() - t) * 1000)


def _acknowledge(doc: dict) -> None:
    sender = doc["meta"].get("sender")
    if not (sender and mail.configured()):
        return
    status = {"posted": "has been accepted and scheduled for payment",
              "exception": "is under review by our Accounts Payable team",
              "blocked": "appears to be a duplicate of an invoice we have already booked"}.get(doc["status"], "was received")
    try:
        mail.send(sender, f"Re: {doc['meta'].get('subject') or 'Invoice'} — {doc['invoice_number'] or doc['file_name']}",
                  mail.render([f"Thank you. Invoice <b>{html.escape(doc['invoice_number'] or doc['file_name'])}</b> {status}."],
                              [("Invoice total", f"₹{inr(doc['total'] or 0)}"), ("Reference", f"AP-{doc['id']:05d}")]),
                  doc["meta"].get("message_id", ""))
        store.log(doc["id"], "notify", "done", f"Acknowledgement emailed to {sender}")
    except Exception as exc:
        store.log(doc["id"], "notify", "failed", f"Acknowledgement not sent: {exc}")


# ---- reviewer actions ---------------------------------------------------------------------
def approve(doc_id: int, resolution: str = "as_invoiced", note: str = "") -> dict:
    doc = store.get(doc_id)
    bill = (doc["erp"] or {}).get("bill")
    if doc["status"] != "exception" or not bill:
        raise ValueError("Only invoices on hold with a draft bill can be approved")
    if resolution == "received_qty":
        lines = controls.bill_lines(doc["controls"], odoo, received_qty_only=True)
        odoo.call("account.move", "write", [bill["id"]], {"invoice_line_ids": [(5, 0, 0)] + [(0, 0, l) for l in lines]})
    posted = odoo.post_bill(bill["id"])
    label = "for received quantity only" if resolution == "received_qty" else "as invoiced"
    odoo.close_reviews(bill["id"], f"Approved {label}. {note}".strip())
    odoo.note("account.move", bill["id"], f"<p>Approved by AP reviewer {label}. {html.escape(note)}</p>")
    store.log(doc_id, "review", "done", f"Approved {label}; posted {posted['name']}" + (f" — {note}" if note else ""))
    return store.update(doc_id, status="approved", erp={**doc["erp"], "bill": posted, "resolution": resolution})


def reject(doc_id: int, reason: str, email_vendor: bool = False, body: str = "") -> dict:
    doc = store.get(doc_id)
    bill = (doc["erp"] or {}).get("bill")
    if bill:
        odoo.close_reviews(bill["id"], f"Rejected: {reason}")
        odoo.note("account.move", bill["id"], f"<p>Rejected by AP reviewer: {html.escape(reason)}</p>")
        odoo.cancel_bill(bill["id"])
        bill = odoo.bill(bill["id"])
    store.log(doc_id, "review", "done", f"Rejected — {reason}")
    if email_vendor:
        email_supplier(doc_id, body=body)
    return store.update(doc_id, status="rejected", erp={**(doc["erp"] or {}), "bill": bill})


def vendor_email_draft(doc_id: int) -> dict:
    doc = store.get(doc_id)
    vendor = (doc["controls"] or {}).get("vendor") or {}
    inv = (doc["extraction"] or {}).get("invoice") or {}
    issues = [c for c in (doc["controls"] or {}).get("checks", []) if c["status"] == "fail"]
    supplier_text = {
        "GST-03": "GST has been charged under the wrong regime for the place of supply. Please issue a corrected invoice.",
        "GST-05": "The invoice is addressed to an incorrect GSTIN. Please re-issue it to our registered GSTIN.",
        "EINV-02": "The invoice does not carry an IRN although e-invoicing applies to you. Please register it on the IRP.",
        "PO-03": "Unit prices differ from the purchase order. Please issue a credit note or share the approved revision.",
        "GRN-01": "Billed quantity exceeds the quantity received at our plant. We can pay for the received quantity; "
                  "please issue a credit note for the balance.",
        "BANK-01": "The bank details on the invoice differ from our records. For your security we will call your "
                   "registered contact to verify before making any change; payment is on hold until then.",
        "DUP-01": "This invoice number has already been booked; no further action is needed.",
        "PO-01": "We could not find the purchase order quoted on the invoice. Please confirm the PO number.",
    }
    points = [supplier_text.get(c["code"], c["title"]) for c in issues]
    body = (f"Dear {vendor.get('name', 'Supplier')},\n\nThank you for invoice {inv.get('invoice_number', '')} dated "
            f"{inv.get('invoice_date', '')} for ₹{inr(inv.get('total_amount') or 0)}. Our review found:\n\n"
            + "\n".join(f"• {p}" for p in points) + "\n\nRegards,\nAccounts Payable\n" + (doc["controls"] or {}).get("company", ""))
    return {"to": vendor.get("email", ""), "subject": f"Invoice {inv.get('invoice_number', '')} — action required",
            "body": body}


def email_supplier(doc_id: int, to: str = "", subject: str = "", body: str = "") -> dict:
    draft = vendor_email_draft(doc_id)
    to, subject, body = to or draft["to"], subject or draft["subject"], body or draft["body"]
    sent_to = mail.send(to, subject, mail.render([html.escape(p).replace("\n", "<br/>") for p in body.split("\n\n")]))
    store.log(doc_id, "notify", "done", f"Supplier emailed at {sent_to}: {subject}")
    return store.get(doc_id)


_last_sync = [0.0]


def sync_from_erp(min_interval_s: float = 8.0) -> None:
    """Reflect decisions taken outside this app (AP Copilot agent, or directly in Odoo) on held invoices."""
    if time.time() - _last_sync[0] < min_interval_s:
        return
    _last_sync[0] = time.time()
    held = [d for d in store.all_docs() if d["status"] == "exception" and (d["erp"] or {}).get("bill")]
    if not held:
        return
    states = {b["id"]: b for b in odoo.search_read("account.move", [("id", "in", [d["erp"]["bill"]["id"] for d in held])],
                                                   ["id", "state", "name"])}
    for d in held:
        b = states.get(d["erp"]["bill"]["id"])
        if b and b["state"] in ("posted", "cancel"):
            bill = odoo.bill(b["id"])
            store.log(d["id"], "review", "done", f"{'Posted' if b['state'] == 'posted' else 'Cancelled'} {b['name'] or ''} outside the "
                                                 "workbench (AP Copilot or Odoo)")
            store.update(d["id"], status="approved" if b["state"] == "posted" else "rejected", erp={**d["erp"], "bill": bill})


# ---- inbox & housekeeping -----------------------------------------------------------------
def poll_inbox() -> list[dict]:
    return [submit(m["data"], m["filename"], "email",
                   {"sender": m["sender"], "subject": m["subject"], "message_id": m["message_id"]})
            for m in mail.fetch_invoices()]


def reset() -> int:
    """Remove every bill this app created in Odoo and clear local documents (repeatable demos)."""
    removed = 0
    for doc in store.all_docs():
        bill = (doc["erp"] or {}).get("bill")
        if bill:
            try:
                odoo.call("account.move", "button_draft", [bill["id"]])
                odoo.call("account.move", "unlink", [bill["id"]])
            except Exception:
                odoo.cancel_bill(bill["id"])
            removed += 1
    store.clear()
    shutil.rmtree(config.UPLOAD_DIR, ignore_errors=True)
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return removed
