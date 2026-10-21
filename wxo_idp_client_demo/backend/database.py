"""
Local SQLite Database for storing extracted documents in the client demo package.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "demo_invoices.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS demo_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_type TEXT NOT NULL DEFAULT 'Invoice',
                invoice_number TEXT NOT NULL,
                invoice_date TEXT NOT NULL DEFAULT '',
                due_date TEXT NOT NULL DEFAULT '',
                vendor_name TEXT NOT NULL DEFAULT '',
                vendor_address TEXT NOT NULL DEFAULT '',
                buyer_name TEXT NOT NULL DEFAULT '',
                buyer_address TEXT NOT NULL DEFAULT '',
                po_number TEXT NOT NULL DEFAULT '',
                payment_terms TEXT NOT NULL DEFAULT '',
                currency TEXT NOT NULL DEFAULT 'USD',
                subtotal_amount REAL NOT NULL DEFAULT 0.0,
                tax_amount REAL NOT NULL DEFAULT 0.0,
                total_amount REAL NOT NULL DEFAULT 0.0,
                avg_confidence REAL NOT NULL DEFAULT 0.0,
                validation_notes TEXT NOT NULL DEFAULT '',
                approval_tier TEXT NOT NULL DEFAULT 'AUTO_APPROVED',
                math_summary TEXT NOT NULL DEFAULT '',
                execution_mode TEXT NOT NULL DEFAULT 'direct_flow',
                file_name TEXT NOT NULL DEFAULT '',
                s3_url TEXT NOT NULL DEFAULT '',
                extracted_text TEXT NOT NULL DEFAULT '',
                raw_kvps_json TEXT NOT NULL DEFAULT '[]',
                telemetry_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS demo_line_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                line_index INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity TEXT NOT NULL,
                unit_price REAL NOT NULL,
                amount REAL NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.98,
                gl_category TEXT NOT NULL DEFAULT 'General',
                FOREIGN KEY (document_id) REFERENCES demo_documents(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()


def save_document_record(
    structured_doc: Dict[str, Any],
    kvps: Optional[List[Dict[str, Any]]] = None,
    extracted_text: str = "",
    execution_mode: str = "direct_flow",
    file_name: str = "",
    s3_url: str = "",
    avg_confidence: float = 0.0,
    logic_summary: Optional[Dict[str, Any]] = None,
    telemetry: Optional[List[Dict[str, Any]]] = None,
    document_type_override: Optional[str] = None,
) -> Dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    kvps_list = kvps or []
    logic_summary = logic_summary or {}

    ocr_upper = (extracted_text or "").upper()
    if document_type_override:
        doc_type = document_type_override
    elif "PURCHASE ORDER" in ocr_upper or "PO NUMBER" in ocr_upper or file_name.lower().startswith("po_") or "PURCHASEORDER" in (structured_doc.get("document_type") or "").upper():
        doc_type = "Purchase Order"
    elif "PAYMENT RECEIPT" in ocr_upper or "RECEIPT NUMBER" in ocr_upper or "TOTAL PAID" in ocr_upper or file_name.lower().startswith("receipt_") or "RECEIPT" in (structured_doc.get("document_type") or "").upper():
        doc_type = "Receipt"
    elif structured_doc.get("document_type") and structured_doc.get("document_type") not in ("", "Invoice"):
        doc_type = structured_doc.get("document_type")
    elif logic_summary.get("detected_document_type") and logic_summary.get("detected_document_type") != "Invoice":
        doc_type = logic_summary.get("detected_document_type")
    else:
        doc_type = "Invoice"
    inv_number = (
        structured_doc.get("invoice_number")
        or logic_summary.get("invoice_number")
        or file_name
    )
    inv_date = structured_doc.get("invoice_date") or logic_summary.get("doc_date") or ""
    due_date = structured_doc.get("due_date") or ""
    vendor_name = structured_doc.get("vendor_name") or logic_summary.get("vendor_name") or ""
    vendor_addr = structured_doc.get("vendor_address") or ""
    buyer_name = structured_doc.get("buyer_name") or logic_summary.get("buyer_name") or ""
    buyer_addr = structured_doc.get("buyer_address") or ""
    po_number = structured_doc.get("po_number") or logic_summary.get("po_number") or ""
    payment_terms = structured_doc.get("payment_terms") or ""
    currency = structured_doc.get("currency") or logic_summary.get("currency") or "USD"

    subtotal = float(structured_doc.get("subtotal_amount") or logic_summary.get("computed_subtotal") or 0.0)
    tax = float(structured_doc.get("tax_amount") or logic_summary.get("computed_tax") or 0.0)
    total = float(structured_doc.get("total_amount") or logic_summary.get("computed_total") or 0.0)

    val_notes = structured_doc.get("audit_notes") or logic_summary.get("math_summary") or ""
    approval_tier = structured_doc.get("approval_tier") or logic_summary.get("approval_tier") or "AUTO_APPROVED"
    math_summary = logic_summary.get("math_summary") or ""

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO demo_documents (
                document_type, invoice_number, invoice_date, due_date,
                vendor_name, vendor_address, buyer_name, buyer_address,
                po_number, payment_terms, currency,
                subtotal_amount, tax_amount, total_amount,
                avg_confidence, validation_notes, approval_tier, math_summary,
                execution_mode, file_name, s3_url,
                extracted_text, raw_kvps_json, telemetry_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_type, inv_number, inv_date, due_date,
                vendor_name, vendor_addr, buyer_name, buyer_addr,
                po_number, payment_terms, currency,
                subtotal, tax, total,
                avg_confidence, val_notes, approval_tier, math_summary,
                execution_mode, file_name, s3_url,
                extracted_text, json.dumps(kvps_list), json.dumps(telemetry or []), created_at,
            ),
        )
        doc_id = cur.lastrowid

        raw_items = structured_doc.get("line_items") or []
        for idx, item in enumerate(raw_items, start=1):
            desc = item.get("description") or f"Item {idx}"
            qty = str(item.get("quantity") or "1")
            uprice = float(item.get("unit_price") or 0.0)
            amt = float(item.get("amount") or (float(qty or 1) * uprice))
            conf = float(item.get("confidence") or avg_confidence or 0.98)
            gl_cat = item.get("gl_category") or "General Ledger"

            conn.execute(
                """
                INSERT INTO demo_line_items (
                    document_id, line_index, description, quantity,
                    unit_price, amount, confidence, gl_category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (doc_id, idx, desc, qty, uprice, amt, conf, gl_cat),
            )
        conn.commit()

    return get_document_by_id(doc_id)


def get_document_by_id(doc_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM demo_documents WHERE id = ?", (doc_id,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        res["raw_kvps"] = json.loads(res.get("raw_kvps_json") or "[]")
        res["telemetry"] = json.loads(res.get("telemetry_json") or "[]")

        items_cur = conn.execute(
            "SELECT * FROM demo_line_items WHERE document_id = ? ORDER BY line_index ASC",
            (doc_id,),
        )
        res["line_items"] = [dict(r) for r in items_cur.fetchall()]
        return res


def list_documents(limit: int = 50) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM demo_documents ORDER BY id DESC LIMIT ?", (limit,)
        )
        results = []
        for row in cur.fetchall():
            rec = dict(row)
            rec["raw_kvps"] = json.loads(rec.get("raw_kvps_json") or "[]")
            rec["telemetry"] = json.loads(rec.get("telemetry_json") or "[]")
            items_cur = conn.execute(
                "SELECT * FROM demo_line_items WHERE document_id = ? ORDER BY line_index ASC",
                (rec["id"],),
            )
            rec["line_items"] = [dict(r) for r in items_cur.fetchall()]
            results.append(rec)
        return results


def delete_document_by_id(doc_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM demo_documents WHERE id = ?", (doc_id,))
        conn.commit()
        return cur.rowcount > 0
