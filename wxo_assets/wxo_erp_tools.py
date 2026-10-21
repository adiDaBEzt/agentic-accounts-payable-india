"""
IBM watsonx Orchestrate ADK — Live Odoo ERP & Purchase Order Tools
Provides real-time conversational tools for the watsonx Orchestrate Embedded Agent:
1. query_odoo_erp_bills: Live XML-RPC query of Vendor Bills in Odoo Cloud ERP
2. post_or_create_odoo_bill: Approve/Post draft bills or create new Vendor Bills in Odoo ERP
3. query_purchase_orders_and_matching: Query PO database and run 2-Way PO vs. Invoice matching
"""
import os
import xmlrpc.client
from datetime import date
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission


# Enterprise Purchase Order Catalog for 2-Way Matching & Conversational Audit
ENTERPRISE_PO_LEDGER = {
    "PO-99812": {
        "po_number": "PO-99812",
        "vendor": " CloudHost Inc.",
        "vendor_Normalized": "CloudHost Inc.",
        "authorized_amount": 3850.00,
        "open_amount": 3850.00,
        "currency": "USD",
        "status": "OPEN",
        "department": "Cloud Infrastructure & DevOps",
        "gl_code": "6200-CLOUD-INFRA",
        "payment_terms": "Net 30",
        "approver": "Marcus Vance (VP Infrastructure)",
        "items": [
            {"description": "Dedicated GPU Cluster Node (NVIDIA H100x4)", "qty": 1, "unit_price": 2500.00, "amount": 2500.00},
            {"description": "Enterprise S3 Storage Tier (50TB)", "qty": 1, "unit_price": 1000.00, "amount": 1000.00},
            {"description": "Taxes & Regulatory Cloud Surcharge", "qty": 1, "unit_price": 350.00, "amount": 350.00},
        ],
    },
    "PO-44210": {
        "po_number": "PO-44210",
        "vendor": "logan",
        "vendor_Normalized": "Logan Industrial Services",
        "authorized_amount": 55.00,
        "open_amount": 55.00,
        "currency": "USD",
        "status": "OPEN",
        "department": "Facilities & Operations",
        "gl_code": "5310-OPS-MAINT",
        "payment_terms": "Net 15",
        "approver": "Elena Rostova (Ops Director)",
        "items": [
            {"description": "Standard Field Service & Consumables", "qty": 1, "unit_price": 55.00, "amount": 55.00},
        ],
    },
    "PO-77504": {
        "po_number": "PO-77504",
        "vendor": "Unknown Vendor",
        "vendor_Normalized": "Apex Global Consulting LLP",
        "authorized_amount": 11500.00,
        "open_amount": 11500.00,
        "currency": "USD",
        "status": "PARTIAL_RECEIPT",
        "department": "Executive Advisory & Legal",
        "gl_code": "6800-PROF-SERVICES",
        "payment_terms": "Net 45",
        "approver": "CFO Committee (Executive Board)",
        "items": [
            {"description": "Q4 Enterprise Architecture Audit & SOC2 Advisory", "qty": 1, "unit_price": 11500.00, "amount": 11500.00},
        ],
    },
    "PO-2026-8812": {
        "po_number": "PO-2026-8812",
        "vendor": "Precision Industrial Robotics Corp.",
        "vendor_Normalized": "Precision Industrial Robotics Corp.",
        "authorized_amount": 18450.00,
        "open_amount": 18450.00,
        "currency": "USD",
        "status": "OPEN",
        "department": "Manufacturing Automation",
        "gl_code": "5110-DIRECT-EQUIP",
        "payment_terms": "Net 30",
        "approver": "David Chen (SVP Manufacturing)",
        "items": [
            {"description": "6-Axis Harmonic Servo Actuator Unit (Model HX-900)", "qty": 2, "unit_price": 6800.00, "amount": 13600.00},
            {"description": "Laser Vision Calibration Array & Optical Controller", "qty": 1, "unit_price": 3200.00, "amount": 3200.00},
            {"description": "On-Site Factory Commissioning & Safety Certification", "qty": 1, "unit_price": 1650.00, "amount": 1650.00},
        ],
    },
    "PO-2026-9481": {
        "po_number": "PO-2026-9481",
        "vendor": "TechCorp Enterprise Hardware Ltd.",
        "vendor_Normalized": "TechCorp Enterprise Hardware Ltd.",
        "authorized_amount": 16218.50,
        "open_amount": 16218.50,
        "currency": "USD",
        "status": "OPEN",
        "department": "AI Compute Engineering",
        "gl_code": "6200-CLOUD-INFRA",
        "payment_terms": "Net 30",
        "approver": "Sarah Jenkins (VP AI Systems)",
        "items": [
            {"description": "Enterprise AI Compute Blade Server (Dual Xeon / 8x GPU)", "qty": 1, "unit_price": 9800.00, "amount": 9800.00},
            {"description": "100GbE QSFP28 Optical Network Transceiver Pack", "qty": 4, "unit_price": 650.00, "amount": 2600.00},
            {"description": "24/7 Mission-Critical Support & Hardware Warranty (1 Yr)", "qty": 1, "unit_price": 2350.00, "amount": 2350.00},
        ],
    },
}


def _get_odoo_config():
    url = os.getenv("ODOO_URL", "https://invoiceprocessing.odoo.com").rstrip("/")
    db = os.getenv("ODOO_DB", "invoiceprocessing")
    username = os.getenv("ODOO_USERNAME", "")
    password = os.getenv("ODOO_PASSWORD", "")
    return url, db, username, password


@tool(
    name="query_odoo_erp_bills",
    description=(
        "Query live Vendor Bills directly from Odoo Cloud ERP (account.move). "
        "Use this tool whenever the user asks about Odoo bills, vendor invoices in ERP, "
        "draft vs posted bills, vendor spend in Odoo, or specific bill IDs."
    ),
    permission=ToolPermission.READ_ONLY,
)
def query_odoo_erp_bills(search_query: str = "", status_filter: str = "all") -> dict:
    """
    Fetches live Vendor Bills from Odoo Cloud ERP via XML-RPC.

    Args:
        search_query: Optional vendor name, bill number, or invoice reference to filter by (leave empty for all bills).
        status_filter: Optional bill state filter: 'all', 'draft', or 'posted'.
    """
    url, db, username, password = _get_odoo_config()
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        uid = common.authenticate(db, username, password, {})
        if not uid:
            return {"status": "error", "message": "Odoo XML-RPC authentication failed."}

        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
        domain = [["move_type", "=", "in_invoice"]]
        if status_filter and status_filter.lower() in ("draft", "posted"):
            domain.append(["state", "=", status_filter.lower()])

        records = models.execute_kw(
            db,
            uid,
            password,
            "account.move",
            "search_read",
            [domain],
            {
                "fields": [
                    "id",
                    "name",
                    "ref",
                    "partner_id",
                    "invoice_date",
                    "amount_untaxed",
                    "amount_tax",
                    "amount_total",
                    "state",
                    "payment_state",
                ],
                "limit": 40,
                "order": "id desc",
            },
        )

        q = (search_query or "").strip().lower()
        bills = []
        for r in records:
            vendor_name = r["partner_id"][1] if isinstance(r.get("partner_id"), list) else "Unknown Vendor"
            bill_item = {
                "odoo_bill_id": r["id"],
                "bill_number": r.get("name") or f"BILL/{r['id']}",
                "invoice_ref": r.get("ref") or "-",
                "vendor": vendor_name,
                "invoice_date": r.get("invoice_date") or "-",
                "amount_total": round(float(r.get("amount_total") or 0.0), 2),
                "state": r.get("state", "draft"),
                "payment_state": r.get("payment_state", "not_paid"),
                "odoo_url": f"{url}/odoo/vendor-bills/{r['id']}",
            }
            if q:
                haystack = f"{bill_item['odoo_bill_id']} {bill_item['bill_number']} {bill_item['invoice_ref']} {bill_item['vendor']}".lower()
                if q not in haystack:
                    continue
            bills.append(bill_item)

        total_spend = round(sum(b["amount_total"] for b in bills), 2)
        draft_count = sum(1 for b in bills if b["state"] == "draft")
        posted_count = sum(1 for b in bills if b["state"] == "posted")

        return {
            "status": "success",
            "odoo_instance": url,
            "database": db,
            "total_bills_returned": len(bills),
            "draft_bills_count": draft_count,
            "posted_bills_count": posted_count,
            "cumulative_bill_amount": total_spend,
            "bills": bills,
        }
    except Exception as e:
        return {"status": "error", "message": f"Odoo ERP query error: {str(e)}"}


@tool(
    name="post_or_create_odoo_bill",
    description=(
        "Approve and post a draft Vendor Bill in Odoo Cloud ERP (action='post' with bill_id), "
        "or create a new Vendor Bill in Odoo Cloud ERP (action='create' with vendor_name, invoice_number, total_amount)."
    ),
    permission=ToolPermission.READ_WRITE,
)
def post_or_create_odoo_bill(
    action: str = "post",
    bill_id: int = 0,
    vendor_name: str = "",
    invoice_number: str = "",
    total_amount: float = 0.0,
) -> dict:
    """
    Posts an existing Draft Vendor Bill in Odoo ERP or creates a new Vendor Bill.

    Args:
        action: Either 'post' (to approve/finalize an existing draft bill by bill_id) or 'create' (to create a new vendor bill).
        bill_id: The Odoo numeric bill ID (e.g., 16, 17, 18) when action='post'.
        vendor_name: Vendor name when action='create'.
        invoice_number: Invoice reference number when action='create'.
        total_amount: Total bill amount when action='create'.
    """
    url, db, username, password = _get_odoo_config()
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        uid = common.authenticate(db, username, password, {})
        if not uid:
            return {"status": "error", "message": "Odoo XML-RPC authentication failed."}

        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
        act = (action or "post").strip().lower()

        if act == "post" and bill_id > 0:
            recs = models.execute_kw(
                db, uid, password, "account.move", "read", [[int(bill_id)]],
                {"fields": ["id", "name", "state", "ref", "amount_total", "partner_id"]}
            )
            if not recs:
                return {"status": "error", "message": f"Vendor Bill ID #{bill_id} not found in Odoo."}
            rec = recs[0]
            if rec.get("state") != "posted":
                models.execute_kw(db, uid, password, "account.move", "action_post", [[int(bill_id)]])
                recs = models.execute_kw(
                    db, uid, password, "account.move", "read", [[int(bill_id)]],
                    {"fields": ["id", "name", "state", "ref", "amount_total", "partner_id"]}
                )
                rec = recs[0] if recs else rec
            return {
                "status": "success",
                "action": "posted",
                "odoo_bill_id": int(bill_id),
                "bill_number": rec.get("name"),
                "state": rec.get("state", "posted"),
                "vendor": rec["partner_id"][1] if isinstance(rec.get("partner_id"), list) else vendor_name,
                "amount_total": rec.get("amount_total"),
                "odoo_url": f"{url}/odoo/vendor-bills/{int(bill_id)}",
            }

        # Create a new Vendor Bill
        v_name = (vendor_name or "Enterprise Vendor").strip()
        partner_ids = models.execute_kw(
            db, uid, password, "res.partner", "search", [[["name", "ilike", v_name]]], {"limit": 1}
        )
        if partner_ids:
            partner_id = partner_ids[0]
        else:
            partner_id = models.execute_kw(
                db, uid, password, "res.partner", "create", [{"name": v_name, "supplier_rank": 1}]
            )

        new_id = models.execute_kw(
            db,
            uid,
            password,
            "account.move",
            "create",
            [
                {
                    "move_type": "in_invoice",
                    "partner_id": partner_id,
                    "ref": invoice_number or "INV-WXO-AGENT",
                    "invoice_date": date.today().isoformat(),
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": f"{v_name} - Invoice {invoice_number or 'Agent Entry'}",
                                "quantity": 1.0,
                                "price_unit": float(total_amount or 0.0),
                            },
                        )
                    ],
                }
            ],
        )
        return {
            "status": "success",
            "action": "created",
            "odoo_bill_id": new_id,
            "vendor": v_name,
            "invoice_ref": invoice_number,
            "amount_total": float(total_amount or 0.0),
            "state": "draft",
            "odoo_url": f"{url}/odoo/vendor-bills/{new_id}",
        }
    except Exception as e:
        return {"status": "error", "message": f"Odoo ERP write error: {str(e)}"}


@tool(
    name="query_purchase_orders_and_matching",
    description=(
        "Query the Enterprise Purchase Order (PO) database (PO-99812, PO-44210, PO-77504, PO-2026-8812, PO-2026-9481) "
        "and perform 2-Way PO vs. Invoice matching and variance analysis. "
        "Use this tool when the user asks about POs, open budgets, line items, GL codes, approvers, or PO matching."
    ),
    permission=ToolPermission.READ_ONLY,
)
def query_purchase_orders_and_matching(
    po_number: str = "",
    vendor_name: str = "",
    invoice_amount: float = 0.0,
) -> dict:
    """
    Looks up Purchase Orders and optionally computes 2-Way PO vs. Invoice variance.

    Args:
        po_number: Optional PO number (e.g., 'PO-99812', 'PO-44210', 'PO-77504', 'PO-2026-8812', 'PO-2026-9481'). Leave empty to list all POs.
        vendor_name: Optional vendor name to match against the PO catalog.
        invoice_amount: Optional billed invoice amount to run a 2-Way variance check against the matched PO.
    """
    po_q = (po_number or "").strip().upper()
    v_q = (vendor_name or "").strip().lower()

    matched_pos = []
    for code, po in ENTERPRISE_PO_LEDGER.items():
        if po_q and po_q in code:
            matched_pos.append(po)
        elif v_q and (v_q in po["vendor"].lower() or v_q in po["vendor_Normalized"].lower()):
            matched_pos.append(po)
        elif not po_q and not v_q:
            matched_pos.append(po)

    if not matched_pos:
        matched_pos = list(ENTERPRISE_PO_LEDGER.values())

    variance_analysis = None
    if len(matched_pos) == 1 and invoice_amount and float(invoice_amount) > 0:
        target_po = matched_pos[0]
        auth_amt = float(target_po["authorized_amount"])
        inv_amt = float(invoice_amount)
        diff = round(inv_amt - auth_amt, 2)
        pct = round((abs(diff) / auth_amt) * 100, 2) if auth_amt > 0 else 0.0
        variance_analysis = {
            "po_number": target_po["po_number"],
            "po_authorized_amount": auth_amt,
            "invoice_billed_amount": inv_amt,
            "variance_amount": diff,
            "variance_pct": pct,
            "match_status": "EXACT_2WAY_MATCH" if abs(diff) <= 0.01 else ("WITHIN_5PCT_TOLERANCE" if pct <= 5.0 else "PO_VARIANCE_EXCEPTION"),
        }

    return {
        "status": "success",
        "total_pos_in_catalog": len(ENTERPRISE_PO_LEDGER),
        "matched_count": len(matched_pos),
        "purchase_orders": matched_pos,
        "two_way_match_audit": variance_analysis,
    }
