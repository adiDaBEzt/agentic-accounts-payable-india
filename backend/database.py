"""
Database Access Layer for IBM watsonx Orchestrate Enterprise AP Command Center.

Dual-mode persistent storage:
1. Neon PostgreSQL Cloud Database (Primary enterprise cloud database)
2. Local SQLite fallback (invoices.db) if running without internet / cloud DB credentials.
"""

import os
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


SQLITE_DB_PATH = Path(__file__).resolve().parent.parent / "invoices.db"


def _get_database_url() -> Optional[str]:
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return dsn.strip().strip('"').strip("'")
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    return val
    return None


DATABASE_URL = _get_database_url()


class DBConnection:
    def __init__(self):
        self.is_postgres = False
        self.conn = None

    def __enter__(self):
        global DATABASE_URL
        if PSYCOPG2_AVAILABLE and DATABASE_URL:
            try:
                self.conn = psycopg2.connect(DATABASE_URL)
                self.is_postgres = True
                return self
            except Exception as e:
                # Fallback to SQLite gracefully if network/credentials fail
                pass

        self.conn = sqlite3.connect(str(SQLITE_DB_PATH))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.is_postgres = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
            self.conn.close()

    def execute(self, query: str, params: Tuple[Any, ...] = ()) -> Any:
        if self.is_postgres:
            pg_query = query.replace("?", "%s")
            cur = self.conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(pg_query, params)
            return cur
        else:
            return self.conn.execute(query, params)


def get_connection() -> DBConnection:
    return DBConnection()


def get_database_status() -> Dict[str, Any]:
    global DATABASE_URL
    if PSYCOPG2_AVAILABLE and DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("SELECT version();")
            ver = cur.fetchone()[0]
            conn.close()
            return {
                "engine": "Neon PostgreSQL",
                "connected": True,
                "version": ver.split()[0] + " " + ver.split()[1],
                "database": "neondb",
                "cloud": "Neon Serverless AWS (us-east-2)",
            }
        except Exception as e:
            return {
                "engine": "SQLite (Fallback)",
                "connected": True,
                "notice": f"Neon connection error: {str(e)[:60]}",
                "database": str(SQLITE_DB_PATH.name),
            }
    return {
        "engine": "SQLite",
        "connected": True,
        "database": str(SQLITE_DB_PATH.name),
    }


def init_db() -> None:
    with get_connection() as db:
        if db.is_postgres:
            cur = db.conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY,
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
                subtotal_amount DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                tax_amount DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                total_amount DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                avg_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                validation_notes TEXT NOT NULL DEFAULT '',
                approval_tier TEXT NOT NULL DEFAULT 'AUTO_APPROVED',
                math_summary TEXT NOT NULL DEFAULT '',
                execution_mode TEXT NOT NULL DEFAULT 'direct_flow',
                source_channel TEXT NOT NULL DEFAULT 'web_upload',
                odoo_bill_id INTEGER DEFAULT NULL,
                odoo_url TEXT NOT NULL DEFAULT '',
                odoo_state TEXT NOT NULL DEFAULT 'draft',
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
                id SERIAL PRIMARY KEY,
                invoice_id INTEGER NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
                line_index INTEGER NOT NULL DEFAULT 1,
                description TEXT NOT NULL DEFAULT '',
                quantity TEXT NOT NULL DEFAULT '1',
                unit_price DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                amount DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                gl_category TEXT NOT NULL DEFAULT 'General Expense',
                confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0
            );
            """)
        else:
            db.conn.executescript("""
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
                source_channel TEXT NOT NULL DEFAULT 'web_upload',
                odoo_bill_id INTEGER DEFAULT NULL,
                odoo_url TEXT NOT NULL DEFAULT '',
                odoo_state TEXT NOT NULL DEFAULT 'draft',
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
            """)


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
    source_channel: str = "web_upload",
    odoo_bill_id: Optional[int] = None,
    odoo_url: str = "",
) -> Dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    kvps_list = kvps or []
    telemetry_list = telemetry or []
    logic_dict = logic_summary or {}

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
    ocr_upper = (extracted_text or "").upper()
    f_lower = file_name.lower()
    inv_num_val = (structured_invoice.get("invoice_number") or "").upper()

    if f_lower.startswith("po_") or f_lower.startswith("purchase_order_") or (
        ("PURCHASE ORDER" in ocr_upper or "PURCHASEORDER" in (structured_invoice.get("document_type") or "").upper())
        and "INVOICE" not in ocr_upper
        and not f_lower.startswith("invoice_")
        and not inv_num_val.startswith("INV-")
    ):
        doc_type = "Purchase Order"
    elif f_lower.startswith("receipt_") or "PAYMENT RECEIPT" in ocr_upper or "RECEIPT NUMBER" in ocr_upper or "TOTAL PAID" in ocr_upper or "RECEIPT" in (structured_invoice.get("document_type") or "").upper():
        doc_type = "Receipt"
    elif f_lower.startswith("invoice_") or f_lower.startswith("clean_") or f_lower.startswith("variance_") or "INVOICE" in ocr_upper or inv_num_val.startswith("INV-"):
        doc_type = "Invoice"
    elif logic_dict.get("detected_document_type") and logic_dict.get("detected_document_type") != "Invoice":
        doc_type = logic_dict.get("detected_document_type")
    elif structured_invoice.get("document_type") and structured_invoice.get("document_type") not in ("", "Invoice"):
        doc_type = structured_invoice.get("document_type")
    else:
        doc_type = "Invoice"

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

    with get_connection() as db:
        if db.is_postgres:
            insert_sql = """
            INSERT INTO invoices (
                document_type,
                invoice_number, invoice_date, due_date,
                vendor_name, vendor_address, buyer_name, buyer_address,
                po_number, payment_terms, currency,
                subtotal_amount, tax_amount, total_amount,
                avg_confidence, validation_notes, approval_tier, math_summary,
                execution_mode, source_channel, odoo_bill_id, odoo_url,
                file_name, s3_url, wxo_thread_id, wxo_run_id,
                extracted_text, raw_kvps_json, telemetry_json, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """
            cur = db.conn.cursor()
            cur.execute(
                insert_sql,
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
                    source_channel,
                    odoo_bill_id,
                    odoo_url,
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
            invoice_id = cur.fetchone()[0]

            line_items = structured_invoice.get("line_items") or []
            for idx, item in enumerate(line_items):
                item_conf = (
                    line_item_confidences[idx]
                    if idx < len(line_item_confidences)
                    else round(avg_confidence, 4)
                )
                cur.execute(
                    """
                    INSERT INTO invoice_line_items (
                        invoice_id, line_index, description, quantity, unit_price, amount, gl_category, confidence
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
        else:
            cur = db.execute(
                """
                INSERT INTO invoices (
                    document_type,
                    invoice_number, invoice_date, due_date,
                    vendor_name, vendor_address, buyer_name, buyer_address,
                    po_number, payment_terms, currency,
                    subtotal_amount, tax_amount, total_amount,
                    avg_confidence, validation_notes, approval_tier, math_summary,
                    execution_mode, source_channel, odoo_bill_id, odoo_url,
                    file_name, s3_url, wxo_thread_id, wxo_run_id,
                    extracted_text, raw_kvps_json, telemetry_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    source_channel,
                    odoo_bill_id,
                    odoo_url,
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
            invoice_id = cur.lastrowid

            line_items = structured_invoice.get("line_items") or []
            for idx, item in enumerate(line_items):
                item_conf = (
                    line_item_confidences[idx]
                    if idx < len(line_item_confidences)
                    else round(avg_confidence, 4)
                )
                db.execute(
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

    return get_invoice_by_id(invoice_id)


def get_invoice_by_id(invoice_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as db:
        cur = db.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        row = cur.fetchone()
        if not row:
            return None
        inv = dict(row)
        inv["raw_kvps"] = json.loads(inv.pop("raw_kvps_json", "[]") or "[]")
        inv["telemetry"] = json.loads(inv.pop("telemetry_json", "[]") or "[]")

        cur_items = db.execute(
            "SELECT * FROM invoice_line_items WHERE invoice_id = ? ORDER BY line_index ASC",
            (invoice_id,),
        )
        inv["line_items"] = [dict(it) for it in cur_items.fetchall()]
        return inv


def list_invoices(limit: int = 50) -> List[Dict[str, Any]]:
    with get_connection() as db:
        cur = db.execute("SELECT * FROM invoices ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        results = []
        for row in rows:
            inv = dict(row)
            inv["raw_kvps"] = json.loads(inv.pop("raw_kvps_json", "[]") or "[]")
            inv["telemetry"] = json.loads(inv.pop("telemetry_json", "[]") or "[]")
            cur_items = db.execute(
                "SELECT * FROM invoice_line_items WHERE invoice_id = ? ORDER BY line_index ASC",
                (inv["id"],),
            )
            inv["line_items"] = [dict(it) for it in cur_items.fetchall()]
            results.append(inv)
        return results


def update_invoice_odoo_status(
    invoice_id: int, odoo_bill_id: int, odoo_url: str, odoo_state: str = "draft"
) -> None:
    with get_connection() as db:
        db.execute(
            "UPDATE invoices SET odoo_bill_id = ?, odoo_url = ?, odoo_state = ? WHERE id = ?",
            (odoo_bill_id, odoo_url, odoo_state, invoice_id),
        )


def update_invoice_workflow(
    invoice_id: int,
    approval_tier: Optional[str] = None,
    validation_notes: Optional[str] = None,
    odoo_bill_id: Optional[int] = None,
    odoo_url: Optional[str] = None,
    odoo_state: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    updates: List[str] = []
    params: List[Any] = []

    if approval_tier is not None:
        updates.append("approval_tier = ?")
        params.append(approval_tier)
    if validation_notes is not None:
        updates.append("validation_notes = ?")
        params.append(validation_notes)
    if odoo_bill_id is not None:
        updates.append("odoo_bill_id = ?")
        params.append(odoo_bill_id)
    if odoo_url is not None:
        updates.append("odoo_url = ?")
        params.append(odoo_url)
    if odoo_state is not None:
        updates.append("odoo_state = ?")
        params.append(odoo_state)

    if overrides:
        allowed_str_fields = {
            "invoice_number",
            "invoice_date",
            "due_date",
            "vendor_name",
            "buyer_name",
            "po_number",
            "payment_terms",
            "currency",
            "document_type",
        }
        allowed_float_fields = {"subtotal_amount", "tax_amount", "total_amount"}
        for key, val in overrides.items():
            if key in allowed_str_fields and val is not None:
                updates.append(f"{key} = ?")
                params.append(str(val))
            elif key in allowed_float_fields and val is not None:
                updates.append(f"{key} = ?")
                params.append(_parse_float(val))

    if updates:
        params.append(invoice_id)
        with get_connection() as db:
            db.execute(
                f"UPDATE invoices SET {', '.join(updates)} WHERE id = ?",
                tuple(params),
            )

    return get_invoice_by_id(invoice_id)


def delete_invoice_by_id(invoice_id: int) -> bool:
    with get_connection() as db:
        if db.is_postgres:
            cur = db.conn.cursor()
            cur.execute("DELETE FROM invoices WHERE id = %s", (invoice_id,))
            return cur.rowcount > 0
        else:
            cur = db.conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            return cur.rowcount > 0


def clear_all_invoices() -> int:
    """
    Truncates/deletes all invoice records and associated line items from
    both Neon Serverless PostgreSQL and local SQLite fallback.
    Resets identity sequences so fresh uploads start clean at ID #1.
    """
    deleted_count = 0
    with get_connection() as db:
        if db.is_postgres:
            cur = db.conn.cursor()
            cur.execute("SELECT count(*) FROM invoices")
            row = cur.fetchone()
            deleted_count = row["count"] if isinstance(row, dict) else row[0]
            cur.execute("TRUNCATE TABLE invoice_line_items, invoices RESTART IDENTITY CASCADE;")
        else:
            cur = db.conn.cursor()
            cur.execute("SELECT count(*) FROM invoices")
            row = cur.fetchone()
            deleted_count = row[0]
            db.conn.execute("DELETE FROM invoice_line_items;")
            db.conn.execute("DELETE FROM invoices;")
            try:
                db.conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('invoices', 'invoice_line_items');")
            except Exception:
                pass
    return deleted_count
