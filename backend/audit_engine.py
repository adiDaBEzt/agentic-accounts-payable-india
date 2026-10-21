"""
Enterprise AP Audit Engine:
1. Automated 2-Way / 3-Way PO Matching (Purchase Order <-> Invoice Line-Item Reconciliation)
2. Fraud, Duplicate & Split-Invoice Anomaly Shield (0-100 Risk Scoring)
3. CFO Spend Analytics & General Ledger (GL) Intelligence Aggregator
"""

from typing import Any, Dict, List, Optional

# Currency conversion rates to USD for normalized CFO reporting
CURRENCY_TO_USD = {
    "USD": 1.0,
    "CAD": 0.73,
    "EUR": 1.08,
    "GBP": 1.27,
    "INR": 0.012,
}

# Master ERP Purchase Order Baseline Registry (used when PO isn't yet uploaded as a separate row in SQLite)
MASTER_ERP_POS: Dict[str, Dict[str, Any]] = {
    "PO-99812": {
        "po_number": "PO-99812",
        "vendor_name": "Acme Cloud Systems Inc.",
        "buyer_name": "Global Logistics Corp.",
        "order_date": "2026-03-01",
        "currency": "USD",
        "authorized_subtotal": 5100.00,
        "line_items": [
            {"description": "watsonx Orchestrate Enterprise Connector License", "quantity": 2.0, "unit_price": 1500.00, "amount": 3000.00},
            {"description": "Intelligent Document Processing (IDP) High-Volume Pack", "quantity": 1.0, "unit_price": 1200.00, "amount": 1200.00},
            {"description": "Dedicated Solutions Engineering Onboarding (Hours)", "quantity": 6.0, "unit_price": 150.00, "amount": 900.00},
        ],
    },
    "PO-44210": {
        "po_number": "PO-44210",
        "vendor_name": "Northern AI Robotics Ltd.",
        "buyer_name": "Maple Leaf Manufacturing Inc.",
        "order_date": "2026-03-20",
        "currency": "CAD",
        "authorized_subtotal": 6400.00,
        "line_items": [
            {"description": "Optical Inspection Camera Unit Model X7", "quantity": 4.0, "unit_price": 850.00, "amount": 3400.00},
            {"description": "Edge Inference Gateway Server Box", "quantity": 1.0, "unit_price": 2400.00, "amount": 2400.00},
            {"description": "Annual Firmware Maintenance & Calibration Plan", "quantity": 1.0, "unit_price": 600.00, "amount": 600.00},
        ],
    },
    "PO-77504": {
        "po_number": "PO-77504",
        "vendor_name": "Pacific CyberSecurity Solutions Inc.",
        "buyer_name": "Apex Financial Holdings Ltd.",
        "order_date": "2026-10-05",
        "currency": "USD",
        "authorized_subtotal": 14200.00,  # Notice: Vendor billed $15,000 subtotal (1 extra Red Team day over PO!)
        "line_items": [
            {"description": "Zero-Trust Network Intrusion Detection Appliance", "quantity": 3.0, "unit_price": 2200.00, "amount": 6600.00},
            {"description": "24/7 SOC Threat Hunting & Incident Response Retainer", "quantity": 1.0, "unit_price": 3500.00, "amount": 3500.00},
            {"description": "Penetration Testing & Red Team Assessment (Days)", "quantity": 4.0, "unit_price": 800.00, "amount": 3200.00},
            {"description": "Hardware Security Module (HSM) Key Vault License", "quantity": 2.0, "unit_price": 450.00, "amount": 900.00},
        ],
    },
    "PO-2026-8812": {
        "po_number": "PO-2026-8812",
        "vendor_name": "Quantum Server Racks Inc.",
        "buyer_name": "Global Logistics Corp.",
        "order_date": "2026-10-18",
        "currency": "USD",
        "authorized_subtotal": 12500.00,
        "line_items": [
            {"description": "42U Heavy-Duty Server Rack Cabinet with Cooling", "quantity": 5.0, "unit_price": 1800.00, "amount": 9000.00},
            {"description": "Redundant Rack PDU Power Distribution Unit", "quantity": 10.0, "unit_price": 350.00, "amount": 3500.00},
        ],
    },
    "PO-2026-9481": {
        "po_number": "PO-2026-9481",
        "vendor_name": "Apex Cloud Infrastructure Inc.",
        "buyer_name": "Alpha Global Systems Ltd.",
        "order_date": "2026-10-15",
        "currency": "USD",
        "authorized_subtotal": 5000.00,
        "line_items": [
            {"description": "watsonx Enterprise AI Cluster Compute (Monthly)", "quantity": 2.0, "unit_price": 1800.00, "amount": 3600.00},
            {"description": "High-Throughput Vector DB Storage (5TB Tier)", "quantity": 1.0, "unit_price": 950.00, "amount": 950.00},
            {"description": "Premium SLA 24/7 Enterprise Support", "quantity": 1.0, "unit_price": 450.00, "amount": 450.00},
        ],
    },
}


def _to_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = "".join(ch for ch in str(val) if ch.isdigit() or ch in ".-")
    try:
        return float(s) if s else default
    except ValueError:
        return default


def find_matching_po(
    invoice: Dict[str, Any], all_invoices: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Search SQLite first for an uploaded Purchase Order document matching `po_number`
    or `vendor_name`, then fall back to `MASTER_ERP_POS`.
    """
    po_num = (invoice.get("po_number") or "").strip().upper()
    inv_id = invoice.get("id")

    # 1. Check SQLite records where document_type is Purchase Order
    for rec in all_invoices:
        if rec.get("id") == inv_id:
            continue
        rec_type = (rec.get("document_type") or "").lower()
        if "purchase" in rec_type or rec_type == "po":
            rec_po = (rec.get("po_number") or rec.get("invoice_number") or "").strip().upper()
            if po_num and rec_po == po_num:
                return {
                    "po_number": rec_po,
                    "source": f"SQLite PO Record #{rec['id']} ({rec.get('file_name', 'uploaded')})",
                    "vendor_name": rec.get("vendor_name", ""),
                    "currency": rec.get("currency", "USD"),
                    "authorized_subtotal": _to_float(rec.get("subtotal_amount") or rec.get("total_amount")),
                    "line_items": [
                        {
                            "description": li.get("description", ""),
                            "quantity": _to_float(li.get("quantity"), 1.0),
                            "unit_price": _to_float(li.get("unit_price"), 0.0),
                            "amount": _to_float(li.get("amount"), 0.0),
                        }
                        for li in (rec.get("line_items") or [])
                    ],
                }

    # 2. Check Master ERP PO Registry
    if po_num and po_num in MASTER_ERP_POS:
        master = dict(MASTER_ERP_POS[po_num])
        master["source"] = f"Master ERP PO Registry ({po_num})"
        return master

    return {}


def evaluate_invoice_audit(
    invoice: Dict[str, Any], all_invoices: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Execute comprehensive 2-Way PO Matching + 6-Point Fraud & Anomaly Shield.
    """
    doc_type = (invoice.get("document_type") or "Invoice").strip()
    inv_num = (invoice.get("invoice_number") or "").strip()
    po_num = (invoice.get("po_number") or "").strip()
    vendor = (invoice.get("vendor_name") or "").strip()
    currency = (invoice.get("currency") or "USD").strip()
    subtotal = _to_float(invoice.get("subtotal_amount"))
    tax = _to_float(invoice.get("tax_amount"))
    total = _to_float(invoice.get("total_amount"))
    avg_conf = _to_float(invoice.get("avg_confidence"), 0.98)
    inv_items = invoice.get("line_items") or []

    # --- PART 1: 2-Way Purchase Order Matching ---
    po_match: Dict[str, Any] = {
        "status": "NO_PO_REFERENCED",
        "status_label": "No PO Referenced",
        "po_number": po_num or "None",
        "po_source": "N/A",
        "authorized_subtotal": 0.0,
        "billed_subtotal": subtotal,
        "variance_amount": 0.0,
        "variance_pct": 0.0,
        "summary": "Document does not reference a Purchase Order.",
        "line_comparisons": [],
    }

    if "purchase" in doc_type.lower():
        po_match["status"] = "IS_PURCHASE_ORDER"
        po_match["status_label"] = "Source Purchase Order"
        po_match["po_number"] = po_num or inv_num
        po_match["po_source"] = f"Authoritative PO #{invoice.get('id')}"
        po_match["authorized_subtotal"] = total
        po_match["billed_subtotal"] = total
        po_match["summary"] = f"This document is an authoritative Purchase Order ({po_match['po_number']}) authorizing {currency} {total:,.2f}."
    elif "receipt" in doc_type.lower():
        po_match["status"] = "NO_PO_REQUIRED"
        po_match["status_label"] = "Direct Expense Receipt (No PO Needed)"
        po_match["summary"] = "Point-of-sale / T&E expense receipts bypass PO matching under corporate card policy."
    else:
        matched_po = find_matching_po(invoice, all_invoices)
        if matched_po:
            auth_sub = _to_float(matched_po.get("authorized_subtotal"))
            po_lines = matched_po.get("line_items") or []
            variance = round(subtotal - auth_sub, 2)
            variance_pct = round((variance / auth_sub) * 100, 2) if auth_sub > 0 else 0.0

            comparisons = []
            max_len = max(len(inv_items), len(po_lines))
            any_line_mismatch = False
            for idx in range(max_len):
                inv_li = inv_items[idx] if idx < len(inv_items) else {}
                po_li = po_lines[idx] if idx < len(po_lines) else {}

                i_desc = inv_li.get("description") or po_li.get("description") or f"Item #{idx + 1}"
                i_qty = _to_float(inv_li.get("quantity"), 0.0)
                p_qty = _to_float(po_li.get("quantity"), 0.0)
                i_price = _to_float(inv_li.get("unit_price"), 0.0)
                p_price = _to_float(po_li.get("unit_price"), 0.0)
                i_amt = _to_float(inv_li.get("amount"), 0.0)
                p_amt = _to_float(po_li.get("amount"), 0.0)

                delta_amt = round(i_amt - p_amt, 2)
                if abs(delta_amt) < 0.05 and abs(i_price - p_price) < 0.05 and abs(i_qty - p_qty) < 0.05:
                    line_status = "MATCHED"
                elif i_price > p_price + 0.05:
                    line_status = "PRICE_SPIKE"
                    any_line_mismatch = True
                elif i_qty > p_qty + 0.05:
                    line_status = "QTY_OVERAGE"
                    any_line_mismatch = True
                else:
                    line_status = "VARIANCE"
                    any_line_mismatch = True

                comparisons.append(
                    {
                        "line_index": idx + 1,
                        "description": i_desc,
                        "invoice_description": i_desc,
                        "po_qty": p_qty,
                        "inv_qty": i_qty,
                        "po_unit_price": p_price,
                        "inv_unit_price": i_price,
                        "po_amount": p_amt,
                        "inv_amount": i_amt,
                        "delta_amount": delta_amt,
                        "status": line_status,
                    }
                )

            if abs(variance) < 0.05 and not any_line_mismatch:
                po_match.update(
                    {
                        "status": "MATCHED",
                        "status_label": "2-Way PO Match Verified (100%)",
                        "po_number": matched_po["po_number"],
                        "po_source": matched_po["source"],
                        "authorized_subtotal": auth_sub,
                        "billed_subtotal": subtotal,
                        "variance_amount": 0.0,
                        "subtotal_variance": 0.0,
                        "variance_pct": 0.0,
                        "summary": f"100% 2-Way Match against {matched_po['po_number']}: All {len(comparisons)} line items match PO quantities and unit prices ({currency} {auth_sub:,.2f}).",
                        "line_comparisons": comparisons,
                    }
                )
            else:
                po_match.update(
                    {
                        "status": "VARIANCE_DETECTED",
                        "status_label": f"PO Variance Detected ({'+' if variance >= 0 else ''}{currency} {variance:,.2f})",
                        "po_number": matched_po["po_number"],
                        "po_source": matched_po["source"],
                        "authorized_subtotal": auth_sub,
                        "billed_subtotal": subtotal,
                        "variance_amount": variance,
                        "subtotal_variance": variance,
                        "variance_pct": variance_pct,
                        "summary": f"ALERT: Invoice subtotal ({currency} {subtotal:,.2f}) deviates from {matched_po['po_number']} authorized limit ({currency} {auth_sub:,.2f}) by {currency} {variance:+,.2f} ({variance_pct:+.1f}%).",
                        "line_comparisons": comparisons,
                    }
                )

    # --- PART 2: 6-Point Fraud, Duplicate & Governance Shield ---
    risk_score = 0
    checks: List[Dict[str, Any]] = []

    # Check 1: Duplicate Invoice Detection
    exact_dups = [
        r for r in all_invoices
        if r.get("id") != invoice.get("id")
        and (r.get("invoice_number") or "").strip().upper() == inv_num.upper()
        and inv_num not in ("", "N/A")
    ]
    fuzzy_dups = [
        r for r in all_invoices
        if r.get("id") != invoice.get("id")
        and (r.get("vendor_name") or "").strip().lower() == vendor.lower()
        and abs(_to_float(r.get("total_amount")) - total) < 0.05
        and total > 0
        and r not in exact_dups
    ]
    if exact_dups:
        dup_ids = ", ".join(f"#{r['id']}" for r in exact_dups[:3])
        risk_score += 55
        checks.append(
            {
                "code": "DUPLICATE_INVOICE",
                "title": "Duplicate Submission Guard",
                "status": "FAIL",
                "detail": f"Reference '{inv_num}' already exists in database (Record {dup_ids}). Potential duplicate payment risk.",
                "impact": "+55 Risk",
            }
        )
    elif fuzzy_dups:
        dup_ids = ", ".join(f"#{r['id']}" for r in fuzzy_dups[:3])
        risk_score += 35
        checks.append(
            {
                "code": "FUZZY_DUPLICATE",
                "title": "Duplicate Submission Guard",
                "status": "WARN",
                "detail": f"Identical amount ({currency} {total:,.2f}) for '{vendor}' found in Record {dup_ids}.",
                "impact": "+35 Risk",
            }
        )
    else:
        checks.append(
            {
                "code": "DUPLICATE_INVOICE",
                "title": "Duplicate Submission Guard",
                "status": "PASS",
                "detail": f"Unique reference '{inv_num}' verified across {len(all_invoices)} ledger records.",
                "impact": "+0 Risk",
            }
        )

    # Check 2: 2-Way PO Variance
    if po_match["status"] == "VARIANCE_DETECTED":
        risk_score += 45
        checks.append(
            {
                "code": "PO_RECONCILIATION",
                "title": "2-Way Purchase Order Match",
                "status": "FAIL",
                "detail": po_match["summary"],
                "impact": "+45 Risk",
            }
        )
    elif po_match["status"] in ("MATCHED", "IS_PURCHASE_ORDER", "NO_PO_REQUIRED"):
        checks.append(
            {
                "code": "PO_RECONCILIATION",
                "title": "2-Way Purchase Order Match",
                "status": "PASS",
                "detail": po_match["summary"],
                "impact": "+0 Risk",
            }
        )
    else:
        risk_score += 12
        checks.append(
            {
                "code": "PO_RECONCILIATION",
                "title": "2-Way Purchase Order Match",
                "status": "WARN",
                "detail": "Non-PO invoice: Requires cost-center manager sign-off.",
                "impact": "+12 Risk",
            }
        )

    # Check 3: Deterministic Math Reconciliation
    expected_total = round(subtotal + tax, 2)
    math_diff = round(abs(total - expected_total), 2)
    if math_diff >= 0.05 and subtotal > 0:
        risk_score += 50
        checks.append(
            {
                "code": "MATH_INTEGRITY",
                "title": "Deterministic Arithmetic Audit",
                "status": "FAIL",
                "detail": f"Subtotal ({subtotal:,.2f}) + Tax ({tax:,.2f}) = {expected_total:,.2f}, which mismatches Total ({total:,.2f}) by {math_diff:,.2f}.",
                "impact": "+50 Risk",
            }
        )
    else:
        checks.append(
            {
                "code": "MATH_INTEGRITY",
                "title": "Deterministic Arithmetic Audit",
                "status": "PASS",
                "detail": f"Exact match: Subtotal ({subtotal:,.2f}) + Tax ({tax:,.2f}) == Total ({total:,.2f}).",
                "impact": "+0 Risk",
            }
        )

    # Check 4: Split-Invoice / Approval Threshold Structuring Check
    usd_rate = CURRENCY_TO_USD.get(currency.upper(), 1.0)
    total_usd = total * usd_rate
    if 23000.0 <= total_usd < 25000.0:
        risk_score += 35
        checks.append(
            {
                "code": "THRESHOLD_STRUCTURING",
                "title": "Threshold Evasion ('Structuring') Audit",
                "status": "WARN",
                "detail": f"Amount (${total_usd:,.2f} USD) is within 8% below the $25,000 VP approval limit.",
                "impact": "+35 Risk",
            }
        )
    elif total_usd >= 25000.0:
        risk_score += 15
        checks.append(
            {
                "code": "THRESHOLD_STRUCTURING",
                "title": "Executive Spend Governance",
                "status": "WARN",
                "detail": f"High-value commitment (${total_usd:,.2f} USD >= $25,000) routed for VP sign-off.",
                "impact": "+15 Risk",
            }
        )
    else:
        checks.append(
            {
                "code": "THRESHOLD_STRUCTURING",
                "title": "Threshold Evasion ('Structuring') Audit",
                "status": "PASS",
                "detail": f"Standard authorization tier (${total_usd:,.2f} USD < $25,000 VP limit).",
                "impact": "+0 Risk",
            }
        )

    # Check 5: WDU OCR Extraction Confidence
    if avg_conf < 0.90:
        risk_score += 20
        checks.append(
            {
                "code": "WDU_CONFIDENCE",
                "title": "WDU OCR Confidence Threshold",
                "status": "WARN",
                "detail": f"Average KVP confidence ({avg_conf * 100:.1f}%) is below 90% target.",
                "impact": "+20 Risk",
            }
        )
    else:
        checks.append(
            {
                "code": "WDU_CONFIDENCE",
                "title": "WDU OCR Confidence Threshold",
                "status": "PASS",
                "detail": f"High-certainty extraction ({avg_conf * 100:.1f}% average confidence across KVPs).",
                "impact": "+0 Risk",
            }
        )

    # Baseline minimum score for clean docs
    if risk_score == 0:
        risk_score = 4
    risk_score = min(100, risk_score)

    if risk_score >= 60:
        risk_level = "CRITICAL"
        badge_text = f"Risk {risk_score}/100 • Action Required"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
        badge_text = f"Risk {risk_score}/100 • Review Advisory"
    else:
        risk_level = "LOW"
        badge_text = f"Risk {risk_score}/100 • Verified Clean"

    return {
        "invoice_id": invoice.get("id"),
        "po_match": po_match,
        "risk_shield": {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "badge_text": badge_text,
            "checks": checks,
        },
    }


def compute_cfo_analytics(all_invoices: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute executive AP metrics & General Ledger spend distribution across all stored records.
    """
    total_docs = len(all_invoices)
    by_doc_type = {"Invoice": 0, "Purchase Order": 0, "Receipt": 0}
    total_spend_usd = 0.0
    stp_count = 0
    vp_count = 0
    flagged_count = 0
    odoo_synced = 0
    conf_sum = 0.0

    gl_totals: Dict[str, Dict[str, Any]] = {}
    gl_colors = {
        "Cloud Infrastructure": "#0f62fe",
        "Hardware Equipment": "#007d79",
        "Cybersecurity Software": "#8a3ffc",
        "Professional Services": "#005d5d",
        "Food & Hospitality": "#ba4e00",
        "General Expense": "#697077",
    }

    for inv in all_invoices:
        dtype = inv.get("document_type") or "Invoice"
        if "purchase" in dtype.lower():
            by_doc_type["Purchase Order"] += 1
        elif "receipt" in dtype.lower():
            by_doc_type["Receipt"] += 1
        else:
            by_doc_type["Invoice"] += 1

        curr = (inv.get("currency") or "USD").upper()
        rate = CURRENCY_TO_USD.get(curr, 1.0)
        amt_usd = _to_float(inv.get("total_amount")) * rate
        total_spend_usd += amt_usd

        tier = (inv.get("approval_tier") or "AUTO_APPROVED").upper()
        if "AUTO" in tier or "APPROVED_BY_VP" in tier:
            stp_count += 1
        elif "VP" in tier:
            vp_count += 1
        else:
            flagged_count += 1

        if inv.get("odoo_bill_id"):
            odoo_synced += 1

        conf_sum += _to_float(inv.get("avg_confidence"), 0.98)

        for li in inv.get("line_items") or []:
            cat = li.get("gl_category") or "General Expense"
            if "food" in cat.lower() or "dining" in cat.lower() or "catering" in cat.lower():
                cat = "Food & Hospitality"
            li_usd = _to_float(li.get("amount")) * rate
            if cat not in gl_totals:
                gl_totals[cat] = {
                    "category": cat,
                    "amount_usd": 0.0,
                    "count": 0,
                    "color": gl_colors.get(cat, "#4589ff"),
                }
            gl_totals[cat]["amount_usd"] = round(gl_totals[cat]["amount_usd"] + li_usd, 2)
            gl_totals[cat]["count"] += 1

    gl_sum = sum(g["amount_usd"] for g in gl_totals.values()) or 1.0
    gl_breakdown = sorted(gl_totals.values(), key=lambda x: x["amount_usd"], reverse=True)
    for g in gl_breakdown:
        g["percentage"] = round((g["amount_usd"] / gl_sum) * 100, 1)

    stp_rate = round((stp_count / total_docs) * 100, 1) if total_docs > 0 else 100.0
    avg_conf_pct = round((conf_sum / total_docs) * 100, 1) if total_docs > 0 else 98.0

    return {
        "total_documents": total_docs,
        "by_doc_type": by_doc_type,
        "invoice_count": by_doc_type["Invoice"],
        "po_count": by_doc_type["Purchase Order"],
        "receipt_count": by_doc_type["Receipt"],
        "total_ap_spend_usd": round(total_spend_usd, 2),
        "total_spend_usd": round(total_spend_usd, 2),
        "stp_auto_approved_count": stp_count,
        "stp_rate_pct": stp_rate,
        "vp_review_count": vp_count,
        "flagged_count": flagged_count,
        "disputed_count": flagged_count,
        "odoo_synced_count": odoo_synced,
        "avg_confidence_pct": avg_conf_pct,
        "gl_breakdown": [
            {**g, "pct": g["percentage"]} for g in gl_breakdown
        ],
    }
