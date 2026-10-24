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


# Enterprise Purchase Order Catalog for 2-Way & 3-Way Matching, Step POs & Conversational Audit
ENTERPRISE_PO_LEDGER = {
    "PO-99812": {
        "po_number": "PO-99812",
        "vendor": "Acme Cloud Systems Inc.",
        "vendor_Normalized": "Acme Cloud Systems Inc.",
        "buyer_name": "Global Logistics Corp.",
        "order_date": "2026-03-01",
        "authorized_subtotal": 5100.00,
        "authorized_amount": 5100.00,
        "authorized_total": 5610.00,
        "billed_subtotal": 5100.00,
        "billed_amount": 5100.00,
        "billed_total": 5610.00,
        "currency": "USD",
        "match_status": "EXACT_3WAY_MATCH",
        "department": "Cloud Infrastructure & DevOps",
        "gl_code": "6200-CLOUD-INFRA",
        "payment_terms": "2/10 Net 30",
        "approver": "Marcus Vance (VP Infrastructure)",
        "grn_number": "GRN-2026-0912",
        "grn_date": "2026-03-12",
        "receiving_dock": "Cloud Provisioning Portal / IT Asset Desk",
        "grn_inspector": "Marcus Vance (VP Infrastructure)",
        "grn_status": "FULL_RECEIPT_VERIFIED",
        "early_discount_terms": "2/10 Net 30",
        "early_discount_yield": "$112.20 USD (Paid within 10 days)",
        "step_po": "Step 2: Core License & High-Volume IDP Activation ($5,100 / $12,000 ceiling, Active & Verified)",
        "latest_billed_invoice": "INV-2026-0042",
        "variance_amount": 0.00,
        "variance_pct": 0.0,
        "audit_findings": "3-Way Match Passed: 2/2 Connector Licenses active, 1/1 IDP Pack provisioned, 6/6 Engineering hours signed off. Exact subtotal match ($5,100.00). Early discount captured.",
        "items": [
            {"description": "watsonx Orchestrate Enterprise Connector License", "qty": 2, "unit_price": 1500.00, "amount": 3000.00, "grn_received": 2, "grn_accepted": 2},
            {"description": "Intelligent Document Processing (IDP) High-Volume Pack", "qty": 1, "unit_price": 1200.00, "amount": 1200.00, "grn_received": 1, "grn_accepted": 1},
            {"description": "Dedicated Solutions Engineering Onboarding (Hours)", "qty": 6, "unit_price": 150.00, "amount": 900.00, "grn_received": 6, "grn_accepted": 6},
        ],
    },
    "PO-44210": {
        "po_number": "PO-44210",
        "vendor": "Northern AI Robotics Ltd.",
        "vendor_Normalized": "Northern AI Robotics Ltd.",
        "buyer_name": "Maple Leaf Manufacturing Inc.",
        "order_date": "2026-03-20",
        "authorized_subtotal": 6400.00,
        "authorized_amount": 6400.00,
        "authorized_total": 7232.00,
        "billed_subtotal": 6400.00,
        "billed_amount": 6400.00,
        "billed_total": 7232.00,
        "currency": "CAD",
        "match_status": "EXACT_3WAY_MATCH",
        "department": "Manufacturing Automation & Quality Assurance",
        "gl_code": "5110-FACTORY-EQUIP",
        "payment_terms": "1.5/10 Net 30",
        "approver": "Elena Rostova (Quality Assurance Lead)",
        "grn_number": "GRN-2026-0441",
        "grn_date": "2026-03-30",
        "receiving_dock": "Toronto Assembly Plant — Dock #2",
        "grn_inspector": "Elena Rostova (Quality Assurance Lead)",
        "grn_status": "FULL_RECEIPT_VERIFIED",
        "early_discount_terms": "1.5/10 Net 30",
        "early_discount_yield": "CAD 108.48 (Paid within 10 days)",
        "step_po": "Step 1: Lot #1 Camera Units (4x @ $850 Step-Tier Price) + Gateway ($6,400 / CAD 12,800 ceiling, Active & Verified)",
        "latest_billed_invoice": "INV-2026-1089",
        "variance_amount": 0.00,
        "variance_pct": 0.0,
        "audit_findings": "3-Way Match Passed: 4/4 Optical Cameras passed calibration at Dock #2, 1/1 Gateway server mounted, SLA contract registered. Step-tier volume pricing ($850/camera) verified against BPA-NORTH-2026.",
        "items": [
            {"description": "Optical Inspection Camera Unit Model X7", "qty": 4, "unit_price": 850.00, "amount": 3400.00, "grn_received": 4, "grn_accepted": 4},
            {"description": "Edge Inference Gateway Server Box", "qty": 1, "unit_price": 2400.00, "amount": 2400.00, "grn_received": 1, "grn_accepted": 1},
            {"description": "Annual Firmware Maintenance & Calibration Plan", "qty": 1, "unit_price": 600.00, "amount": 600.00, "grn_received": 1, "grn_accepted": 1},
        ],
    },
    "PO-77504": {
        "po_number": "PO-77504",
        "vendor": "Pacific CyberSecurity Solutions Inc.",
        "vendor_Normalized": "Pacific CyberSecurity Solutions Inc.",
        "buyer_name": "Apex Financial Holdings Ltd.",
        "order_date": "2026-10-05",
        "authorized_subtotal": 14200.00,
        "authorized_amount": 14200.00,
        "authorized_total": 15336.00,
        "billed_subtotal": 15000.00,
        "billed_amount": 15000.00,
        "billed_total": 16200.00,
        "currency": "USD",
        "match_status": "STEP_CEILING_BREACH_HOLD",
        "department": "Information Security & CISO SOC",
        "gl_code": "6820-CYBER-SEC",
        "payment_terms": "2/10 Net 30",
        "approver": "Devon Brooks (Deputy CISO)",
        "grn_number": "SES-2026-0775 (Service Entry Sheet)",
        "grn_date": "2026-10-19",
        "receiving_dock": "CISO Security Operations Center (Service Entry Sheet)",
        "grn_inspector": "Devon Brooks (Deputy CISO)",
        "grn_status": "SERVICE_CAP_VARIANCE (5 Red-Team Days Billed vs 4 Days Authorized)",
        "early_discount_terms": "2/10 Net 30",
        "early_discount_yield": "$306.72 USD if authorized",
        "step_po": "Step 2: Appliance Rollout & 4-Day Red Team Assessment (Cap: $14,200.00, BREACH: billed $15,000.00 subtotal)",
        "latest_billed_invoice": "INV-2026-2045",
        "variance_amount": 800.00,
        "variance_pct": 5.63,
        "audit_findings": "BREACH DETECTED: Vendor billed 5 Penetration Testing & Red Team days ($4,000.00) on INV-2026-2045, but Service Entry Sheet SES-2026-0775 authorized and signed off on only 4 days ($3,200.00). Unapproved 5th day introduces a +$800.00 variance over PO authorized subtotal ($14,200.00 vs $15,000.00 billed). AP automated hard hold applied pending Deputy CISO Devon Brooks authorization.",
        "items": [
            {"description": "Zero-Trust Network Intrusion Detection Appliance", "qty": 3, "unit_price": 2200.00, "amount": 6600.00, "grn_received": 3, "grn_accepted": 3, "grn_note": "3/3 appliances deployed in NY data center"},
            {"description": "24/7 SOC Threat Hunting & Incident Response Retainer", "qty": 1, "unit_price": 3500.00, "amount": 3500.00, "grn_received": 1, "grn_accepted": 1, "grn_note": "1/1 retainer active in tenant"},
            {"description": "Penetration Testing & Red Team Assessment (Days)", "qty": 4, "unit_price": 800.00, "amount": 3200.00, "grn_received": 4, "grn_accepted": 4, "grn_note": "SES-2026-0775: Only 4 days authorized. Vendor billed 5 days ($4,000), resulting in +$800 unapproved breach."},
            {"description": "Hardware Security Module (HSM) Key Vault License", "qty": 2, "unit_price": 450.00, "amount": 900.00, "grn_received": 2, "grn_accepted": 2, "grn_note": "2/2 HSM licenses activated"},
        ],
    },
    "PO-2026-7731": {
        "po_number": "PO-2026-7731",
        "vendor": "Titan Hypercompute Systems LLC",
        "vendor_Normalized": "Titan Hypercompute Systems LLC",
        "buyer_name": "Alpha Global Systems Ltd.",
        "order_date": "2026-10-19",
        "authorized_subtotal": 14750.00,
        "authorized_amount": 14750.00,
        "authorized_total": 15930.00,
        "billed_subtotal": 14750.00,
        "billed_amount": 14750.00,
        "billed_total": 15930.00,
        "currency": "USD",
        "match_status": "PARTIAL_SHIPMENT_SHORTAGE_DEBIT_MEMO",
        "department": "AI Compute Engineering & Data Center Operations",
        "gl_code": "5120-AI-COMPUTE-HW",
        "payment_terms": "2/10 Net 30",
        "approver": "Sarah Jenkins (VP AI Systems)",
        "grn_number": "GRN-2026-0773",
        "grn_date": "2026-10-21",
        "receiving_dock": "Santa Clara AI Data Center — Receiving Dock B",
        "grn_inspector": "Sarah Jenkins (VP AI Systems)",
        "grn_status": "PARTIAL_SHIPMENT_SHORTAGE (3 of 4 Optical Packs Received)",
        "early_discount_terms": "2/10 Net 30",
        "early_discount_yield": "$304.56 USD after debit memo",
        "step_po": "Step 1: Blade Server & Optical Transceiver Delivery ($14,750 cap, Shortage on Line 2)",
        "latest_billed_invoice": "INV-2026-7731",
        "variance_amount": -650.00,
        "variance_pct": -4.41,
        "debit_memo_number": "DM-2026-7731",
        "debit_memo_amount": 702.00,
        "short_pay_amount": 15228.00,
        "audit_findings": "3-WAY DOCK SHORTAGE DETECTED: Vendor billed for 4x 100GbE QSFP28 Optical Network Transceiver Packs ($2,600.00). However, Santa Clara Dock B (GRN-2026-0773) confirmed physical receipt of only 3 packs (1 pack backordered on slip BO-991, -$650.00 shortage). AP automated settlement generated Debit Memo DM-2026-7731 for -$702.00 (-$650 + 8% tax). Invoice adjusted to short-pay $15,228.00 net, protecting cash outflow.",
        "items": [
            {"description": "Enterprise AI Compute Blade Server (Dual Xeon / 8x GPU)", "qty": 1, "unit_price": 9800.00, "amount": 9800.00, "grn_received": 1, "grn_accepted": 1, "grn_note": "1/1 server chassis received & burn-in tested"},
            {"description": "100GbE QSFP28 Optical Network Transceiver Pack", "qty": 4, "unit_price": 650.00, "amount": 2600.00, "grn_received": 3, "grn_accepted": 3, "grn_note": "SHORT SHIPMENT: Only 3 packs received at Dock B (1 pack backordered on slip BO-991, -$650 shortage). Debit Memo DM-2026-7731 issued for -$702."},
            {"description": "24/7 Mission-Critical Support & Hardware Warranty (1 Yr)", "qty": 1, "unit_price": 2350.00, "amount": 2350.00, "grn_received": 1, "grn_accepted": 1, "grn_note": "Warranty certificate verified"},
        ],
    },
    "PO-2026-8812": {
        "po_number": "PO-2026-8812",
        "vendor": "Quantum Server Racks Inc.",
        "vendor_Normalized": "Quantum Server Racks Inc.",
        "buyer_name": "Global Logistics Corp.",
        "order_date": "2026-10-18",
        "authorized_subtotal": 12500.00,
        "authorized_amount": 12500.00,
        "authorized_total": 12500.00,
        "billed_subtotal": 12500.00,
        "billed_amount": 12500.00,
        "billed_total": 12500.00,
        "currency": "USD",
        "match_status": "EXACT_3WAY_MATCH",
        "department": "Facilities & Data Center Infrastructure",
        "gl_code": "5110-DIRECT-EQUIP",
        "payment_terms": "2/10 Net 45",
        "approver": "Carlos Mendez (Logistics Supervisor)",
        "grn_number": "GRN-2026-0881",
        "grn_date": "2026-10-20",
        "receiving_dock": "Newark Port Terminal — Warehouse Bay 4",
        "grn_inspector": "Carlos Mendez (Logistics Supervisor)",
        "grn_status": "FULL_RECEIPT_VERIFIED",
        "early_discount_terms": "2/10 Net 45",
        "early_discount_yield": "$250.00 USD (Paid within 10 days)",
        "step_po": "Step 1: 5x 42U Server Racks + 10x Redundant PDUs ($12,500 ceiling, Active & Verified)",
        "latest_billed_invoice": "PO-2026-8812",
        "variance_amount": 0.00,
        "variance_pct": 0.0,
        "audit_findings": "3-Way Match Passed: 5/5 42U Server Racks and 10/10 PDUs inspected and continuity tested at Newark Bay 4.",
        "items": [
            {"description": "42U Heavy-Duty Server Rack Cabinet with Cooling", "qty": 5, "unit_price": 1800.00, "amount": 9000.00, "grn_received": 5, "grn_accepted": 5, "grn_note": "5/5 cabinets inspected at Bay 4"},
            {"description": "Redundant Rack PDU Power Distribution Unit", "qty": 10, "unit_price": 350.00, "amount": 3500.00, "grn_received": 10, "grn_accepted": 10, "grn_note": "10/10 PDUs continuity tested"},
        ],
    },
    "PO-2026-9481": {
        "po_number": "PO-2026-9481",
        "vendor": "Apex Cloud Infrastructure Inc.",
        "vendor_Normalized": "Apex Cloud Infrastructure Inc.",
        "buyer_name": "Alpha Global Systems Ltd.",
        "order_date": "2026-10-15",
        "authorized_subtotal": 5000.00,
        "authorized_amount": 5000.00,
        "authorized_total": 5400.00,
        "billed_subtotal": 5000.00,
        "billed_amount": 5000.00,
        "billed_total": 5400.00,
        "currency": "USD",
        "match_status": "EXACT_3WAY_MATCH",
        "department": "AI Cloud Infrastructure",
        "gl_code": "6200-CLOUD-INFRA",
        "payment_terms": "2/10 Net 30",
        "approver": "Sarah Jenkins (VP AI Systems)",
        "grn_number": "GRN-2026-0948",
        "grn_date": "2026-10-20",
        "receiving_dock": "Cloud Telemetry & SRE Entitlement Gateway",
        "grn_inspector": "Sarah Jenkins (VP AI Systems)",
        "grn_status": "FULL_RECEIPT_VERIFIED",
        "early_discount_terms": "2/10 Net 30",
        "early_discount_yield": "$108.00 USD (Paid within 10 days)",
        "step_po": "Step 2: Core Cloud GPU Compute & High-Bandwidth Interconnect ($5,000 / $10,000 ceiling, Active & Verified)",
        "latest_billed_invoice": "INV-2026-9481",
        "variance_amount": 0.00,
        "variance_pct": 0.0,
        "audit_findings": "3-Way Match Passed: GPU compute slice entitlements and high-bandwidth interconnects active.",
        "items": [
            {"description": "watsonx Orchestrate Enterprise Cloud Compute Slice", "qty": 2, "unit_price": 2000.00, "amount": 4000.00, "grn_received": 2, "grn_accepted": 2},
            {"description": "High-Bandwidth Interconnect & VPC Gateway Allocation", "qty": 1, "unit_price": 1000.00, "amount": 1000.00, "grn_received": 1, "grn_accepted": 1},
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
        "Query the Enterprise Purchase Order (PO) database (PO-99812, PO-44210, PO-77504, PO-2026-7731, PO-2026-8812, PO-2026-9481) "
        "and perform 2-Way & 3-Way matching against vendor invoices and Goods Receipt Notes (GRN/SES). "
        "Use this tool when the user asks about POs, open budgets, authorized vs billed amounts, variances, line items, GL codes, approvers, or audit findings."
    ),
    permission=ToolPermission.READ_ONLY,
)
def query_purchase_orders_and_matching(
    po_number: str = "",
    vendor_name: str = "",
    invoice_amount: float = 0.0,
) -> dict:
    """
    Looks up Purchase Orders and computes 2-Way & 3-Way PO vs. Invoice variance analysis.

    Args:
        po_number: Optional PO number (e.g., 'PO-99812', 'PO-44210', 'PO-77504', 'PO-2026-7731', 'PO-2026-8812', 'PO-2026-9481'). Leave empty to list all POs.
        vendor_name: Optional vendor name to match against the PO catalog.
        invoice_amount: Optional billed invoice amount to run a variance check against the matched PO. If omitted, uses the actual vendor billed amount from the ledger.
    """
    po_q = (po_number or "").strip().upper()
    v_q = (vendor_name or "").strip().lower()

    matched_pos = []
    for code, po in ENTERPRISE_PO_LEDGER.items():
        if po_q and (po_q in code or po_q.replace("-", "") in code.replace("-", "")):
            matched_pos.append(po)
        elif v_q and (v_q in po["vendor"].lower() or v_q in po["vendor_Normalized"].lower()):
            matched_pos.append(po)
        elif not po_q and not v_q:
            matched_pos.append(po)

    if not matched_pos:
        matched_pos = list(ENTERPRISE_PO_LEDGER.values())

    variance_analysis = None
    if len(matched_pos) == 1:
        target_po = matched_pos[0]
        auth_amt = float(target_po["authorized_amount"])
        # If user passed explicit invoice_amount > 0, use it; otherwise use the ledger billed_amount
        if invoice_amount and float(invoice_amount) > 0:
            inv_amt = float(invoice_amount)
            diff = round(inv_amt - auth_amt, 2)
            pct = round((abs(diff) / auth_amt) * 100, 2) if auth_amt > 0 else 0.0
            if abs(diff) <= 0.01:
                status = "EXACT_2WAY_MATCH"
            elif diff > 0:
                status = "STEP_CEILING_BREACH"
            else:
                status = "PARTIAL_SHIPMENT_SHORTAGE"
            findings = f"Invoice billed amount (${inv_amt:,.2f}) vs PO authorized amount (${auth_amt:,.2f}): Variance of ${diff:,.2f} ({pct}%)."
        else:
            inv_amt = float(target_po.get("billed_amount", auth_amt))
            diff = float(target_po.get("variance_amount", 0.0))
            pct = float(target_po.get("variance_pct", 0.0))
            status = target_po.get("match_status", "EXACT_3WAY_MATCH")
            findings = target_po.get("audit_findings", "")

        variance_analysis = {
            "po_number": target_po["po_number"],
            "vendor": target_po["vendor"],
            "buyer": target_po.get("buyer_name", "Enterprise AP"),
            "authorized_subtotal": auth_amt,
            "authorized_total": target_po.get("authorized_total", auth_amt),
            "currency": target_po.get("currency", "USD"),
            "invoice_billed_amount": inv_amt,
            "invoice_billed_total": target_po.get("billed_total", inv_amt),
            "latest_billed_invoice": target_po.get("latest_billed_invoice", "N/A"),
            "variance_amount": diff,
            "variance_pct": pct,
            "match_status": status,
            "grn_number": target_po.get("grn_number", "N/A"),
            "grn_status": target_po.get("grn_status", "N/A"),
            "receiving_dock": target_po.get("receiving_dock", "N/A"),
            "debit_memo_number": target_po.get("debit_memo_number"),
            "debit_memo_amount": target_po.get("debit_memo_amount"),
            "short_pay_amount": target_po.get("short_pay_amount"),
            "step_po": target_po.get("step_po", "N/A"),
            "audit_findings": findings,
        }

    return {
        "status": "success",
        "total_pos_in_catalog": len(ENTERPRISE_PO_LEDGER),
        "matched_count": len(matched_pos),
        "purchase_orders": matched_pos,
        "two_way_match_audit": variance_analysis,
    }
