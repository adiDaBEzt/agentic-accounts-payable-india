import os
import json
import sqlite3
import psycopg2

def run_migration():
    dsn = None
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    dsn = line.split("=", 1)[1].strip()
                    break

    if not dsn:
        dsn = os.getenv("DATABASE_URL")

    if not dsn:
        print("No DATABASE_URL found.")
        return

    print("Connecting to Neon PostgreSQL...")
    pg_conn = psycopg2.connect(dsn)
    pg_cur = pg_conn.cursor()

    pg_cur.execute("""
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
    pg_conn.commit()

    pg_cur.execute("SELECT count(*) FROM invoices;")
    count = pg_cur.fetchone()[0]
    print(f"Neon current invoice count: {count}")

    if count == 0 and os.path.exists("invoices.db"):
        print("Migrating from SQLite invoices.db to Neon PostgreSQL...")
        sq_conn = sqlite3.connect("invoices.db")
        sq_conn.row_factory = sqlite3.Row
        sq_cur = sq_conn.cursor()
        sq_rows = sq_cur.execute("SELECT * FROM invoices ORDER BY id ASC").fetchall()
        for row in sq_rows:
            d = dict(row)
            old_id = d.pop("id")
            cols = list(d.keys())
            placeholders = ["%s"] * len(cols)
            sql = f"INSERT INTO invoices (id, {', '.join(cols)}) VALUES (%s, {', '.join(placeholders)})"
            pg_cur.execute(sql, [old_id] + list(d.values()))

            items = sq_cur.execute("SELECT * FROM invoice_line_items WHERE invoice_id = ?", (old_id,)).fetchall()
            for item in items:
                it_d = dict(item)
                it_id = it_d.pop("id")
                it_cols = list(it_d.keys())
                it_ph = ["%s"] * len(it_cols)
                it_sql = f"INSERT INTO invoice_line_items (id, {', '.join(it_cols)}) VALUES (%s, {', '.join(it_ph)})"
                pg_cur.execute(it_sql, [it_id] + list(it_d.values()))

        pg_cur.execute("SELECT setval(pg_get_serial_sequence('invoices', 'id'), coalesce(max(id), 1)) FROM invoices;")
        pg_cur.execute("SELECT setval(pg_get_serial_sequence('invoice_line_items', 'id'), coalesce(max(id), 1)) FROM invoice_line_items;")
        pg_conn.commit()
        sq_conn.close()
        print("Migration complete!")
        pg_cur.execute("SELECT count(*) FROM invoices;")
        print(f"Neon new invoice count: {pg_cur.fetchone()[0]}")

    pg_conn.close()

if __name__ == "__main__":
    run_migration()
