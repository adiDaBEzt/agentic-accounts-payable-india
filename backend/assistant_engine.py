"""
Conversational Assistant Engine for watsonx Orchestrate AP & Procurement Command Center.

Enables natural language conversational querying against:
1. Master ERP Purchase Order (PO) Registry & 2-Way Variance Audit
2. Downstream SQLite Invoices & Document Database
3. Live Odoo Cloud ERP (Vendor Bills, Posting, Status)
4. CFO AP Spend Analytics & GL Category Breakdowns
5. watsonx Orchestrate Architecture & IDP Flow Diagnostics
"""

import re
from typing import Any, Dict, List, Optional
from backend.audit_engine import MASTER_ERP_POS, compute_cfo_analytics, evaluate_invoice_audit
from backend.database import get_invoice_by_id, list_invoices, update_invoice_workflow
from backend.odoo_client import OdooClient


odoo_client = OdooClient()


def process_chat_message(user_message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    msg = (user_message or "").strip()
    msg_lower = msg.lower()
    
    invoices = list_invoices(limit=100)
    enriched_invoices = []
    for inv in invoices:
        inv_copy = dict(inv)
        inv_copy["audit"] = evaluate_invoice_audit(inv, invoices)
        enriched_invoices.append(inv_copy)

    # 1. SPECIFIC PURCHASE ORDER (PO) & VARIANCE QUERIES (High Precedence)
    po_num_match = re.search(r"\bpo[-\s]?(\d+[\w-]*)\b", msg_lower)
    if po_num_match or any(k in msg_lower for k in ["purchase order", "variance", "shortage", "3-way", "2-way", "overbilling", "matching"]):
        target_po = None
        if po_num_match:
            digits = po_num_match.group(1).replace("-", "").lower()
            for k in MASTER_ERP_POS:
                k_clean = k.replace("-", "").lower()
                if digits in k_clean or k_clean in digits:
                    target_po = k
                    break

        if target_po:
            po_data = MASTER_ERP_POS[target_po]
            matched_invs = [
                inv for inv in enriched_invoices
                if target_po.lower() in (inv.get("po_number") or "").lower()
                or target_po.lower() in (inv.get("invoice_number") or "").lower()
                or (inv.get("po_number") and inv.get("po_number").replace("-", "").lower() == target_po.replace("-", "").lower())
            ]

            lines_str = "\n".join(
                f"- **{li.get('description')}**: {li.get('quantity')} units @ ${li.get('unit_price', 0):,.2f} = ${li.get('amount', 0):,.2f} "
                f"(GRN Accepted: {li.get('grn_accepted_qty', li.get('quantity'))} units)"
                for li in po_data.get("line_items", [])
            )

            inv_str = ""
            if matched_invs:
                active_inv = matched_invs[0]
                p_audit = active_inv["audit"]["po_match"]
                ap_auto = active_inv["audit"].get("ap_automation", {})
                is_variance = p_audit.get("status") == "VARIANCE_DETECTED" or p_audit.get("three_way_status") == "GRN_SHORTAGE_DETECTED"
                status_badge = "🔴 **VARIANCE / SHORTAGE DETECTED**" if is_variance else "🟢 **100% 3-WAY MATCHED**"

                debit_memo_note = ""
                if ap_auto.get("debit_memo_number"):
                    debit_memo_note = f"\n- **Auto Debit Memo Issued:** `{ap_auto.get('debit_memo_number')}` (-${ap_auto.get('debit_memo_deduction', 0):,.2f} deduction)"

                inv_str = (
                    f"\n\n### Billed Invoice Comparison:\n"
                    f"- **Invoice Reference:** `{active_inv['invoice_number']}` (ID #{active_inv['id']})\n"
                    f"- **Vendor Billed Subtotal:** `${active_inv.get('subtotal_amount', 0):,.2f}` (Total: `${active_inv['total_amount']:,.2f}`)\n"
                    f"- **Authorized PO Subtotal:** `${p_audit.get('authorized_subtotal', 0):,.2f}`\n"
                    f"- **Warehouse GRN / SES:** `{po_data.get('grn_number', 'N/A')}` ({po_data.get('receiving_dock', 'Receiving')})\n"
                    f"- **2-Way Match (PO vs Inv):** `{p_audit.get('two_way_status')}`\n"
                    f"- **3-Way Match (PO + GRN vs Inv):** `{p_audit.get('three_way_status')}`\n"
                    f"- **Reconciliation Status:** {status_badge}\n"
                    f"- **Net Variance:** `${p_audit.get('subtotal_variance', 0):+,.2f}` ({p_audit.get('variance_pct', 0):+.1f}%)\n"
                    f"- **Audit Finding:** {p_audit.get('summary', '')}"
                    f"{debit_memo_note}"
                )

            step_po_info = ""
            if po_data.get("step_po"):
                spo = po_data["step_po"]
                step_po_info = f"\n- **Step PO Contract:** `{spo.get('contract_master_id')}` (Ceiling: `${spo.get('total_contract_ceiling', 0):,.2f}`) — {spo.get('po_type_label')}"

            return {
                "reply": f"### Purchase Order Details for `{target_po}`:\n"
                         f"- **Vendor / Supplier:** {po_data.get('vendor_name')}\n"
                         f"- **Authorized Subtotal Limit:** `${po_data.get('authorized_subtotal', 0):,.2f} {po_data.get('currency', 'USD')}`\n"
                         f"- **Payment Terms:** {po_data.get('early_discount_terms', 'Net 30')}\n"
                         f"- **Warehouse Receiving Slip / SES:** `{po_data.get('grn_number')}` ({po_data.get('grn_date', 'N/A')})"
                         f"{step_po_info}\n\n"
                         f"**Authorized PO Line Items:**\n{lines_str}"
                         f"{inv_str}",
                "target_po": target_po,
            }

        # General PO variance summary
        variance_invs = [
            inv for inv in enriched_invoices
            if inv["audit"]["po_match"]["status"] == "VARIANCE_DETECTED"
            or inv["audit"]["po_match"].get("three_way_status") == "GRN_SHORTAGE_DETECTED"
        ]
        matched_invs = [
            inv for inv in enriched_invoices
            if inv["audit"]["po_match"]["status"] == "MATCHED"
            and inv["audit"]["po_match"].get("three_way_status") in ("MATCHED", "3-WAY VERIFIED")
        ]

        reply_lines = [
            f"### 3-Way Purchase Order & Warehouse GRN Reconciliation Audit\n",
            f"- **Clean 3-Way Matches:** {len(matched_invs)} documents verified 100% against ERP baselines and warehouse receiving notes.",
            f"- **Variances & Dock Shortages Flagged:** {len(variance_invs)} document(s) with price spikes, unapproved days, or unreceived dock quantities.\n",
        ]
        if variance_invs:
            reply_lines.append("**Flagged Discrepancies:**")
            for inv in variance_invs:
                p_audit = inv["audit"]["po_match"]
                ap_auto = inv["audit"].get("ap_automation", {})
                dm_str = f" &rarr; Auto Debit Memo `{ap_auto.get('debit_memo_number')}`" if ap_auto.get("debit_memo_number") else ""
                reply_lines.append(
                    f"- **{inv['invoice_number']}** ({inv['vendor_name']}): Billed `${inv['total_amount']:,.2f}` against `{p_audit.get('po_number')}`. "
                    f"**Delta: `${p_audit.get('subtotal_variance', 0):+,.2f}`**. "
                    f"Finding: *{p_audit.get('summary')}*{dm_str}"
                )
        else:
            reply_lines.append("All purchase order backed invoices are currently reconciled without variance.")

        reply_lines.append("\n*Known Master POs available to query: `PO-99812`, `PO-44210`, `PO-77504`, `PO-2026-7731`, `PO-2026-8812`, `PO-2026-9481`.*")
        return {"reply": "\n".join(reply_lines)}

    # 2. LIVE ODOO QUERIES
    if re.search(r"\b(?:odoo|vendor bills?|bill status|erp)\b", msg_lower):

    # 3. CFO SPEND, GL BREAKDOWN & ANALYTICS QUERIES
    if any(k in msg_lower for k in ["spend", "analytics", "cfo", "gl", "category", "categories", "total", "breakdown", "metrics", "stp", "debit memo", "discount", "treasury"]):
        analytics = compute_cfo_analytics(invoices)
        gl_lines = [
            f"- **{g['category']}:** ${g['amount_usd']:,.2f} USD ({g['pct']}%) across {g['count']} line items"
            for g in analytics.get("gl_breakdown", [])
        ]
        
        # Calculate debit memo and treasury early discount metrics from enriched invoices
        total_debit_memos = sum(
            inv["audit"]["ap_automation"].get("debit_memo_deduction", 0)
            for inv in enriched_invoices
            if inv.get("audit") and inv["audit"].get("ap_automation")
        )
        total_early_discounts = sum(
            inv["audit"]["ap_automation"].get("early_discount_savings", 0)
            for inv in enriched_invoices
            if inv.get("audit") and inv["audit"].get("ap_automation")
        )

        from backend.database import get_database_status
        db_stat = get_database_status()

        return {
            "reply": f"### Executive CFO Accounts Payable Spend Intelligence:\n\n"
                     f"- **Total AP Spend (USD):** `${analytics.get('total_spend_usd', 0):,.2f}` across {analytics.get('total_documents', 0)} documents\n"
                     f"- **Straight-Through Processing (STP) Rate:** **{analytics.get('stp_rate_pct', 0)}%** ({analytics.get('stp_auto_approved_count', 0)} auto-approved/posted)\n"
                     f"- **Auto Debit Memo Short-Pay Deductions:** **${total_debit_memos:,.2f} USD** (prevented warehouse overbilling leakage)\n"
                     f"- **Early-Payment Treasury Discounts:** **${total_early_discounts:,.2f} USD** captured (2/10 Net 30 = 36.7% annualized yield)\n"
                     f"- **Odoo ERP Synced Count:** {analytics.get('odoo_synced_count', 0)} / {analytics.get('total_documents', 0)} bills posted or synced\n"
                     f"- **Average WDU OCR Confidence:** **{analytics.get('avg_confidence_pct', 0)}%**\n"
                     f"- **Enterprise Cloud Database:** `{db_stat.get('engine', 'Neon PostgreSQL')}` ({db_stat.get('database', 'neondb')})\n\n"
                     f"**General Ledger (GL) Allocation Breakdown:**\n" + "\n".join(gl_lines),
            "analytics": analytics,
        }

    # 4. FRAUD, RISK & VP APPROVAL QUERIES
    if any(k in msg_lower for k in ["risk", "fraud", "duplicate", "vp approval", "flagged", "dispute", "audit"]):
        high_risk = [inv for inv in enriched_invoices if inv["audit"]["risk_shield"]["risk_score"] >= 30]
        vp_pending = [inv for inv in enriched_invoices if "VP" in (inv.get("approval_tier") or "")]
        
        lines = [
            f"### AP Governance & Risk Shield Report:\n",
            f"- **Documents Requiring VP Sign-off:** {len(vp_pending)}",
            f"- **Elevated Risk Documents (Score >= 30):** {len(high_risk)}\n",
        ]
        if high_risk:
            lines.append("**High / Medium Risk Documents:**")
            for inv in high_risk:
                r_shield = inv["audit"]["risk_shield"]
                lines.append(
                    f"- **{inv['invoice_number']}** ({inv['vendor_name']}, ${inv['total_amount']:,.2f}): **Risk {r_shield['risk_score']}/100 ({r_shield['risk_level']})** | Tier: `{inv['approval_tier']}`"
                )
                for c in r_shield.get("checks", []):
                    if c["status"] in ("FAIL", "WARN"):
                        lines.append(f"  • *{c['title']}: {c['detail']}*")
        else:
            lines.append("All active documents currently have clean risk profiles (Risk < 30).")

        return {"reply": "\n".join(lines)}

    # 5. SPECIFIC INVOICE OR VENDOR LOOKUP
    inv_num_match = re.search(r"(?:inv|rec|rcpt)[-\s]?\d+[\w-]*", msg_lower)
    if inv_num_match:
        term = inv_num_match.group(0).replace(" ", "-")
        matching = [inv for inv in enriched_invoices if term in inv.get("invoice_number", "").lower()]
        if matching:
            target = matching[0]
            audit = target["audit"]
            return {
                "reply": f"### Document Summary for `{target['invoice_number']}`:\n\n"
                         f"- **Vendor / Supplier:** {target['vendor_name']}\n"
                         f"- **Document Type:** {target['document_type']}\n"
                         f"- **Total Amount:** {target['currency']} ${target['total_amount']:,.2f}\n"
                         f"- **PO Reference:** `{target['po_number'] or 'None'}`\n"
                         f"- **2-Way PO Match:** **{audit['po_match']['status']}** ({audit['po_match']['summary']})\n"
                         f"- **Risk Score:** **{audit['risk_shield']['risk_score']}/100 ({audit['risk_shield']['risk_level']})**\n"
                         f"- **Odoo ERP Status:** Bill #{target.get('odoo_bill_id') or 'Not Synced'} ({target.get('odoo_state', 'draft')})\n"
                         f"- **Governance Tier:** `{target['approval_tier']}`\n"
                         f"- **Controller Note:** {target.get('validation_notes') or target.get('math_summary') or 'Math verified clean.'}",
                "invoice_id": target["id"],
            }

    # 6. DEFAULT INTELLIGENT AP COPILOT ASSISTANT RESPONSE
    return {
        "reply": f"I am your **watsonx Orchestrate Accounts Payable & Procurement AI Copilot**.\n\n"
                 f"I have live access to your **SQLite Document Ledger ({len(invoices)} documents)**, **Master ERP PO Registry**, and **Odoo Cloud ERP (`https://invoiceprocessing.odoo.com`)**.\n\n"
                 f"Here are a few things you can ask me:\n"
                 f"- 📊 *\"What is our total AP spend and GL breakdown?\"*\n"
                 f"- 🔍 *\"Which invoices have a PO variance or price discrepancy?\"*\n"
                 f"- 🏢 *\"Fetch the latest vendor bills from Odoo\"*\n"
                 f"- ⚠️ *\"Show documents flagged with high risk or needing VP approval\"*\n"
                 f"- 📋 *\"Check PO-77504 details and billed items\"*\n"
                 f"- ⚡ *\"Post bill #6 to Odoo\"*",
    }
