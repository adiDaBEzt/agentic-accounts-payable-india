"""
SQLite Database Layer for the Invoice IDP Pipeline Demo.

Stores extracted invoice records, line-item rows, raw WDU KVP confidence telemetry,
and S3/COS pre-signed storage metadata.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DB_PATH = Path(__file__).resolve().parent.parent / "invoices.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_type TEXT NOT NULL DEFAULT 'Invoice',
                invoice_number TEXT NOT NULL DEFAULT '',
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
                wxo_thread_id TEXT NOT NULL DEFAULT '',
                wxo_run_id TEXT NOT NULL DEFAULT '',
                extracted_text TEXT NOT NULL DEFAULT '',
                raw_kvps_json TEXT NOT NULL DEFAULT '[]',
                telemetry_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS invoice_line_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                line_index INTEGER NOT NULL DEFAULT 1,
                description TEXT NOT NULL DEFAULT '',
                quantity TEXT NOT NULL DEFAULT '1',
                unit_price REAL NOT NULL DEFAULT 0.0,
                amount REAL NOT NULL DEFAULT 0.0,
                gl_category TEXT NOT NULL DEFAULT 'General Expense',
                confidence REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
            );
            """
        )
        # Migrate existing tables if missing new columns
        cursor = conn.execute("PRAGMA table_info(invoices)")
        cols = [r["name"] for r in cursor.fetchall()]
        if "document_type" not in cols:
            conn.execute("ALTER TABLE invoices ADD COLUMN document_type TEXT NOT NULL DEFAULT 'Invoice'")
        if "approval_tier" not in cols:
            conn.execute("ALTER TABLE invoices ADD COLUMN approval_tier TEXT NOT NULL DEFAULT 'AUTO_APPROVED'")
        if "math_summary" not in cols:
            conn.execute("ALTER TABLE invoices ADD COLUMN math_summary TEXT NOT NULL DEFAULT ''")

        cursor_items = conn.execute("PRAGMA table_info(invoice_line_items)")
        item_cols = [r["name"] for r in cursor_items.fetchall()]
        if "gl_category" not in item_cols:
            conn.execute("ALTER TABLE invoice_line_items ADD COLUMN gl_category TEXT NOT NULL DEFAULT 'General Expense'")
        conn.commit()


def _parse_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = (
        str(value)
        .replace("$", "")
        .replace("CAD", "")
        .replace("USD", "")
        .replace("EUR", "")
        .replace(",", "")
        .strip()
    )
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def save_invoice_record(
    structured_invoice: Dict[str, Any],
    kvps: Optional[List[Dict[str, Any]]],
    extracted_text: str,
    execution_mode: str,
    file_name: str,
    s3_url: str,
    wxo_thread_id: str = "",
    wxo_run_id: str = "",
    avg_confidence: float = 0.0,
    logic_summary: Optional[Dict[str, Any]] = None,
    telemetry: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    kvps_list = kvps or []
    telemetry_list = telemetry or []
    logic_dict = logic_summary or {}

    # Extract approval tier and math summary
    approval_tier = (
        structured_invoice.get("approval_tier")
        or logic_dict.get("approval_tier")
        or "AUTO_APPROVED"
    )
    math_summary = (
        logic_dict.get("math_summary")
        or structured_invoice.get("audit_notes")
        or structured_invoice.get("validation_notes")
        or ""
    )
    doc_type = (
        logic_dict.get("detected_document_type")
        or structured_invoice.get("document_type")
        or "Invoice"
    )

    # Build a lookup of line item confidence from raw kvps if available
    line_item_confidences: List[float] = []
    for entry in kvps_list:
        if entry.get("key") == "line_items" and isinstance(entry.get("value"), list):
            for row_dict in entry["value"]:
                if isinstance(row_dict, dict):
                    row_confs = [
                        float(cell.get("confidence", 0.0))
                        for cell in row_dict.values()
                        if isinstance(cell, dict) and cell.get("confidence") is not None
                    ]
                    line_item_confidences.append(
                        round(sum(row_confs) / len(row_confs), 4) if row_confs else avg_confidence
                    )

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO invoices (
                document_type,
                invoice_number, invoice_date, due_date,
                vendor_name, vendor_address, buyer_name, buyer_address,
                po_number, payment_terms, currency,
                subtotal_amount, tax_amount, total_amount,
                avg_confidence, validation_notes, approval_tier, math_summary,
                execution_mode, file_name, s3_url, wxo_thread_id, wxo_run_id,
                extracted_text, raw_kvps_json, telemetry_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_type,
                str(structured_invoice.get("invoice_number") or logic_dict.get("invoice_number") or ""),
                str(structured_invoice.get("invoice_date") or logic_dict.get("doc_date") or ""),
                str(structured_invoice.get("due_date") or ""),
                str(structured_invoice.get("vendor_name") or logic_dict.get("vendor_name") or ""),
                str(structured_invoice.get("vendor_address") or ""),
                str(structured_invoice.get("buyer_name") or logic_dict.get("buyer_name") or ""),
                str(structured_invoice.get("buyer_address") or ""),
                str(structured_invoice.get("po_number") or logic_dict.get("po_number") or ""),
                str(structured_invoice.get("payment_terms") or ""),
                str(structured_invoice.get("currency") or logic_dict.get("currency") or "USD"),
                _parse_float(structured_invoice.get("subtotal_amount") or logic_dict.get("computed_subtotal")),
                _parse_float(structured_invoice.get("tax_amount") or logic_dict.get("computed_tax")),
                _parse_float(structured_invoice.get("total_amount") or logic_dict.get("computed_total")),
                round(avg_confidence, 4),
                str(structured_invoice.get("audit_notes") or structured_invoice.get("validation_notes") or ""),
                approval_tier,
                math_summary,
                execution_mode,
                file_name,
                s3_url,
                wxo_thread_id,
                wxo_run_id,
                extracted_text,
                json.dumps(kvps_list),
                json.dumps(telemetry_list),
                created_at,
            ),
        )
        invoice_id = cursor.lastrowid

        line_items = structured_invoice.get("line_items") or []
        for idx, item in enumerate(line_items):
            item_conf = (
                line_item_confidences[idx]
                if idx < len(line_item_confidences)
                else round(avg_confidence, 4)
            )
            conn.execute(
                """
                INSERT INTO invoice_line_items (
                    invoice_id, line_index, description, quantity, unit_price, amount, gl_category, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    idx + 1,
                    str(item.get("description") or ""),
                    str(item.get("quantity") or "1"),
                    _parse_float(item.get("unit_price")),
                    _parse_float(item.get("amount")),
                    str(item.get("gl_category") or "General Expense"),
                    item_conf,
                ),
            )
        conn.commit()

    return get_invoice_by_id(invoice_id)


def get_invoice_by_id(invoice_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
        if not row:
            return None
        inv = dict(row)
        inv["raw_kvps"] = json.loads(inv.pop("raw_kvps_json", "[]"))
        inv["telemetry"] = json.loads(inv.pop("telemetry_json", "[]"))
        items = conn.execute(
            "SELECT * FROM invoice_line_items WHERE invoice_id = ? ORDER BY line_index ASC",
            (invoice_id,),
        ).fetchall()
        inv["line_items"] = [dict(it) for it in items]
        return inv


def list_invoices(limit: int = 50) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM invoices ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        results = []
        for row in rows:
            inv = dict(row)
            inv["raw_kvps"] = json.loads(inv.pop("raw_kvps_json", "[]"))
            inv["telemetry"] = json.loads(inv.pop("telemetry_json", "[]"))
            items = conn.execute(
                "SELECT * FROM invoice_line_items WHERE invoice_id = ? ORDER BY line_index ASC",
                (inv["id"],),
            ).fetchall()
            inv["line_items"] = [dict(it) for it in items]
            results.append(inv)
        return results


def delete_invoice_by_id(invoice_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        conn.commit()
        return cur.rowcount > 0
