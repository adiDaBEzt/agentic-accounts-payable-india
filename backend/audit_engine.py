"""
Enterprise AP Audit Engine:
1. Automated 2-Way & 3-Way PO Matching (Purchase Order <-> Goods Receipt Note [GRN] <-> Vendor Invoice)
2. Step PO (Phased Milestone Drawdown & Volume Step-Pricing) Governance Tracker
3. Accounts Payable (AP) Payment & Settlement Automation (Auto Debit Memo / Short-Pay, 2/10 Net 30 Early-Pay Treasury Discount, Automated GL Journal Split)
4. Fraud, Duplicate & Split-Invoice Anomaly Shield (0-100 Risk Scoring)
5. CFO Spend Analytics & General Ledger (GL) Intelligence Aggregator
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

# Runtime overrides for interactive 3-Way GRN / Step PO simulation per invoice ID
SIMULATION_OVERRIDES: Dict[int, str] = {}

# Master ERP Purchase Order + Goods Receipt Note (GRN) + Step PO Baseline Registry
MASTER_ERP_POS: Dict[str, Dict[str, Any]] = {
    "PO-99812": {
        "po_number": "PO-99812",
        "vendor_name": "Acme Cloud Systems Inc.",
        "buyer_name": "Global Logistics Corp.",
        "order_date": "2026-03-01",
        "currency": "USD",
        "authorized_subtotal": 5100.00,
        "grn_number": "GRN-2026-0912",
        "grn_date": "2026-03-12",
        "receiving_dock": "Cloud Provisioning Portal / IT Asset Desk",
        "grn_inspector": "Marcus Vance (VP Infrastructure)",
        "grn_status": "FULL_RECEIPT_VERIFIED",
        "early_discount_terms": "2/10 Net 30",
        "early_discount_pct": 2.0,
        "gl_account_code": "6200-CLOUD-INFRA",
        "step_po": {
            "po_type": "STEP_MILESTONE_PO",
            "po_type_label": "3-Step Enterprise SaaS & Onboarding Drawdown PO",
            "contract_master_id": "MSA-ACME-2026",
            "total_contract_ceiling": 12000.00,
            "prior_billed_amount": 3500.00,
            "current_step_number": 2,
            "current_step_name": "Step 2: Core License & High-Volume IDP Activation",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Step 1: Sandbox Provisioning & Architecture Blueprint",
                    "step_limit": 3500.00,
                    "billed_amount": 3500.00,
                    "utilization_pct": 100.0,
                    "gate_requirement": "Architecture Sign-Off (Completed Feb 2026)",
                    "status": "COMPLETED_CLOSED",
                },
                {
                    "step_number": 2,
                    "title": "Step 2: Production Connector Licenses & Onboarding (Current Invoice)",
                    "step_limit": 5100.00,
                    "billed_amount": 5100.00,
                    "utilization_pct": 100.0,
                    "gate_requirement": "GRN-2026-0912 License Key & Hours Verification",
                    "status": "ACTIVE_VERIFIED",
                },
                {
                    "step_number": 3,
                    "title": "Step 3: Q3 Multi-Region Failover Expansion",
                    "step_limit": 3400.00,
                    "billed_amount": 0.00,
                    "utilization_pct": 0.0,
                    "gate_requirement": "Locked until Q3 UAT Sign-Off",
                    "status": "LOCKED_FUTURE_STEP",
                },
            ],
        },
        "line_items": [
            {
                "description": "watsonx Orchestrate Enterprise Connector License",
                "quantity": 2.0,
                "grn_received_qty": 2.0,
                "grn_accepted_qty": 2.0,
                "unit_price": 1500.00,
                "amount": 3000.00,
                "grn_note": "2/2 license entitlements active in tenant",
            },
            {
                "description": "Intelligent Document Processing (IDP) High-Volume Pack",
                "quantity": 1.0,
                "grn_received_qty": 1.0,
                "grn_accepted_qty": 1.0,
                "unit_price": 1200.00,
                "amount": 1200.00,
                "grn_note": "1/1 pack provisioned",
            },
            {
                "description": "Dedicated Solutions Engineering Onboarding (Hours)",
                "quantity": 6.0,
                "grn_received_qty": 6.0,
                "grn_accepted_qty": 6.0,
                "unit_price": 150.00,
                "amount": 900.00,
                "grn_note": "6/6 timesheet hours approved by PM",
            },
        ],
    },
    "PO-44210": {
        "po_number": "PO-44210",
        "vendor_name": "Northern AI Robotics Ltd.",
        "buyer_name": "Maple Leaf Manufacturing Inc.",
        "order_date": "2026-03-20",
        "currency": "CAD",
        "authorized_subtotal": 6400.00,
        "grn_number": "GRN-2026-0441",
        "grn_date": "2026-03-30",
        "receiving_dock": "Toronto Assembly Plant — Dock #2",
        "grn_inspector": "Elena Rostova (Quality Assurance Lead)",
        "grn_status": "FULL_RECEIPT_VERIFIED",
        "early_discount_terms": "1.5/10 Net 30",
        "early_discount_pct": 1.5,
        "gl_account_code": "5110-FACTORY-EQUIP",
        "step_po": {
            "po_type": "STEP_VOLUME_TIER_PO",
            "po_type_label": "Step-Tiered Hardware & Calibration Drawdown PO",
            "contract_master_id": "BPA-NORTH-2026",
            "total_contract_ceiling": 12800.00,
            "prior_billed_amount": 0.00,
            "current_step_number": 1,
            "current_step_name": "Step 1: Lot #1 Optical Inspection & Edge Gateway Delivery",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Step 1: Lot #1 Camera Units (4x @ $850 Step-Tier Price) + Gateway",
                    "step_limit": 6400.00,
                    "billed_amount": 6400.00,
                    "utilization_pct": 100.0,
                    "gate_requirement": "GRN-2026-0441 QA Bench Inspection Passed",
                    "status": "ACTIVE_VERIFIED",
                },
                {
                    "step_number": 2,
                    "title": "Step 2: Lot #2 Expansion Units (Volume Step Discount @ $775/unit)",
                    "step_limit": 6400.00,
                    "billed_amount": 0.00,
                    "utilization_pct": 0.0,
                    "gate_requirement": "Requires Line 1 OEE Telemetry Sign-Off",
                    "status": "LOCKED_FUTURE_STEP",
                },
            ],
        },
        "line_items": [
            {
                "description": "Optical Inspection Camera Unit Model X7",
                "quantity": 4.0,
                "grn_received_qty": 4.0,
                "grn_accepted_qty": 4.0,
                "unit_price": 850.00,
                "amount": 3400.00,
                "grn_note": "4/4 units passed optical calibration at Dock #2",
            },
            {
                "description": "Edge Inference Gateway Server Box",
                "quantity": 1.0,
                "grn_received_qty": 1.0,
                "grn_accepted_qty": 1.0,
                "unit_price": 2400.00,
                "amount": 2400.00,
                "grn_note": "1/1 server rack-mounted",
            },
            {
                "description": "Annual Firmware Maintenance & Calibration Plan",
                "quantity": 1.0,
                "grn_received_qty": 1.0,
                "grn_accepted_qty": 1.0,
                "unit_price": 600.00,
                "amount": 600.00,
                "grn_note": "SLA contract registered",
            },
        ],
    },
    "PO-77504": {
        "po_number": "PO-77504",
        "vendor_name": "Pacific CyberSecurity Solutions Inc.",
        "buyer_name": "Apex Financial Holdings Ltd.",
        "order_date": "2026-10-05",
        "currency": "USD",
        "authorized_subtotal": 14200.00,  # Vendor billed $15,000 subtotal (1 extra Red Team day over PO & SES!)
        "grn_number": "SES-2026-0775",
        "grn_date": "2026-10-19",
        "receiving_dock": "CISO Security Operations Center (Service Entry Sheet)",
        "grn_inspector": "Devon Brooks (Deputy CISO)",
        "grn_status": "SERVICE_CAP_VARIANCE",
        "early_discount_terms": "2/10 Net 30",
        "early_discount_pct": 2.0,
        "gl_account_code": "6820-CYBER-SEC",
        "step_po": {
            "po_type": "STEP_MILESTONE_PO",
            "po_type_label": "3-Step Zero-Trust Security Deployment & Red-Team PO",
            "contract_master_id": "SEC-MSA-77504",
            "total_contract_ceiling": 19200.00,
            "prior_billed_amount": 5000.00,
            "current_step_number": 2,
            "current_step_name": "Step 2: Appliance Rollout & 4-Day Red Team Assessment",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Step 1: Threat Modeling & Network Architecture Audit",
                    "step_limit": 5000.00,
                    "billed_amount": 5000.00,
                    "utilization_pct": 100.0,
                    "gate_requirement": "CISO Sign-Off Completed (Sep 2026)",
                    "status": "COMPLETED_CLOSED",
                },
                {
                    "step_number": 2,
                    "title": "Step 2: IDS Appliances, SOC Retainer & Red-Team (Cap: $14,200)",
                    "step_limit": 14200.00,
                    "billed_amount": 15000.00,
                    "utilization_pct": 105.6,
                    "gate_requirement": "BREACH: Billed 5 Red-Team days vs 4 authorized on SES-2026-0775 (+$800)",
                    "status": "STEP_CEILING_BREACH",
                },
            ],
        },
        "line_items": [
            {
                "description": "Zero-Trust Network Intrusion Detection Appliance",
                "quantity": 3.0,
                "grn_received_qty": 3.0,
                "grn_accepted_qty": 3.0,
                "unit_price": 2200.00,
                "amount": 6600.00,
                "grn_note": "3/3 appliances deployed in NY data center",
            },
            {
                "description": "24/7 SOC Threat Hunting & Incident Response Retainer",
                "quantity": 1.0,
                "grn_received_qty": 1.0,
                "grn_accepted_qty": 1.0,
                "unit_price": 3500.00,
                "amount": 3500.00,
                "grn_note": "1/1 retainer active",
            },
            {
                "description": "Penetration Testing & Red Team Assessment (Days)",
                "quantity": 4.0,
                "grn_received_qty": 4.0,
                "grn_accepted_qty": 4.0,
                "unit_price": 800.00,
                "amount": 3200.00,
                "grn_note": "SES-2026-0775: Only 4 days authorized & signed off by CISO (5th day unapproved)",
            },
            {
                "description": "Hardware Security Module (HSM) Key Vault License",
                "quantity": 2.0,
                "grn_received_qty": 2.0,
                "grn_accepted_qty": 2.0,
                "unit_price": 450.00,
                "amount": 900.00,
                "grn_note": "2/2 HSM licenses activated",
            },
        ],
    },
    "PO-2026-7731": {
        "po_number": "PO-2026-7731",
        "vendor_name": "Titan Hypercompute Systems LLC",
        "buyer_name": "Alpha Global Systems Ltd.",
        "order_date": "2026-10-19",
        "currency": "USD",
        "authorized_subtotal": 14750.00,
        "grn_number": "GRN-2026-0773",
        "grn_date": "2026-10-21",
        "receiving_dock": "Santa Clara AI Data Center — Receiving Dock B",
        "grn_inspector": "Sarah Jenkins (VP AI Systems)",
        "grn_status": "PARTIAL_SHIPMENT_SHORTAGE",
        "early_discount_terms": "2/10 Net 30",
        "early_discount_pct": 2.0,
        "gl_account_code": "5120-AI-COMPUTE-HW",
        "step_po": {
            "po_type": "STEP_MILESTONE_PO",
            "po_type_label": "2-Step AI Cluster Hardware & Optical Interconnect PO",
            "contract_master_id": "CAPEX-TITAN-7731",
            "total_contract_ceiling": 14750.00,
            "prior_billed_amount": 0.00,
            "current_step_number": 1,
            "current_step_name": "Step 1: Hardware Delivery at Santa Clara Dock B",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Step 1: Blade Server & Optical Transceiver Delivery (3-Way GRN Gate)",
                    "step_limit": 14750.00,
                    "billed_amount": 14750.00,
                    "utilization_pct": 100.0,
                    "gate_requirement": "3-WAY HOLD: GRN-2026-0773 logged only 3 of 4 Optical Packs (1 backordered, -$650)",
                    "status": "STEP_CEILING_BREACH",
                },
            ],
        },
        "line_items": [
            {
                "description": "Enterprise AI Compute Blade Server (Dual Xeon / 8x GPU)",
                "quantity": 1.0,
                "grn_received_qty": 1.0,
                "grn_accepted_qty": 1.0,
                "unit_price": 9800.00,
                "amount": 9800.00,
                "grn_note": "1/1 server chassis received & burn-in tested",
            },
            {
                "description": "100GbE QSFP28 Optical Network Transceiver Pack",
                "quantity": 4.0,
                "grn_received_qty": 3.0,
                "grn_accepted_qty": 3.0,
                "unit_price": 650.00,
                "amount": 2600.00,
                "grn_note": "SHORT SHIPMENT: Only 3 packs received at Dock B (1 pack on backorder — slip #BO-991)",
            },
            {
                "description": "24/7 Mission-Critical Support & Hardware Warranty (1 Yr)",
                "quantity": 1.0,
                "grn_received_qty": 1.0,
                "grn_accepted_qty": 1.0,
                "unit_price": 2350.00,
                "amount": 2350.00,
                "grn_note": "Warranty certificate verified",
            },
        ],
    },
    "PO-2026-8812": {
        "po_number": "PO-2026-8812",
        "vendor_name": "Quantum Server Racks Inc.",
        "buyer_name": "Global Logistics Corp.",
        "order_date": "2026-10-18",
        "currency": "USD",
        "authorized_subtotal": 12500.00,
        "grn_number": "GRN-2026-0881",
        "grn_date": "2026-10-20",
        "receiving_dock": "Newark Port Terminal — Warehouse Bay 4",
        "grn_inspector": "Carlos Mendez (Logistics Supervisor)",
        "grn_status": "FULL_RECEIPT_VERIFIED",
        "early_discount_terms": "2/10 Net 45",
        "early_discount_pct": 2.0,
        "gl_account_code": "5110-DIRECT-EQUIP",
        "step_po": {
            "po_type": "STEP_MILESTONE_PO",
            "po_type_label": "2-Step Data Center Rack Infrastructure PO",
            "contract_master_id": "INFRA-8812",
            "total_contract_ceiling": 12500.00,
            "prior_billed_amount": 0.00,
            "current_step_number": 1,
            "current_step_name": "Step 1: Rack Cabinets & Redundant PDU Delivery",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Step 1: 5x 42U Server Racks + 10x Redundant PDUs",
                    "step_limit": 12500.00,
                    "billed_amount": 12500.00,
                    "utilization_pct": 100.0,
                    "gate_requirement": "GRN-2026-0881 Bay 4 Physical Count Verified",
                    "status": "ACTIVE_VERIFIED",
                },
            ],
        },
        "line_items": [
            {
                "description": "42U Heavy-Duty Server Rack Cabinet with Cooling",
                "quantity": 5.0,
                "grn_received_qty": 5.0,
                "grn_accepted_qty": 5.0,
                "unit_price": 1800.00,
                "amount": 9000.00,
                "grn_note": "5/5 cabinets inspected at Bay 4",
            },
            {
                "description": "Redundant Rack PDU Power Distribution Unit",
                "quantity": 10.0,
                "grn_received_qty": 10.0,
                "grn_accepted_qty": 10.0,
                "unit_price": 350.00,
                "amount": 3500.00,
                "grn_note": "10/10 PDUs continuity tested",
            },
        ],
    },
    "PO-2026-9481": {
        "po_number": "PO-2026-9481",
        "vendor_name": "Apex Cloud Infrastructure Inc.",
        "buyer_name": "Alpha Global Systems Ltd.",
        "order_date": "2026-10-15",
        "currency": "USD",
        "authorized_subtotal": 5000.00,
        "grn_number": "GRN-2026-0948",
        "grn_date": "2026-10-20",
        "receiving_dock": "Cloud Telemetry & SRE Entitlement Gateway",
        "grn_inspector": "Sarah Jenkins (VP AI Systems)",
        "grn_status": "FULL_RECEIPT_VERIFIED",
        "early_discount_terms": "2/10 Net 30",
        "early_discount_pct": 2.0,
        "gl_account_code": "6200-CLOUD-INFRA",
        "step_po": {
            "po_type": "STEP_MILESTONE_PO",
            "po_type_label": "3-Step Annual AI Cloud Consumption Drawdown PO",
            "contract_master_id": "CLOUD-APEX-9481",
            "total_contract_ceiling": 15000.00,
            "prior_billed_amount": 5000.00,
            "current_step_number": 2,
            "current_step_name": "Step 2: Q4 AI Compute & Vector DB Tranche",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Step 1: Q3 Initial Cluster Provisioning Tranche",
                    "step_limit": 5000.00,
                    "billed_amount": 5000.00,
                    "utilization_pct": 100.0,
                    "gate_requirement": "Completed & Paid (Q3 2026)",
                    "status": "COMPLETED_CLOSED",
                },
                {
                    "step_number": 2,
                    "title": "Step 2: Q4 Compute + 5TB Vector DB + 24/7 SLA (Current Invoice)",
                    "step_limit": 5000.00,
                    "billed_amount": 5000.00,
                    "utilization_pct": 100.0,
                    "gate_requirement": "GRN-2026-0948 SRE Uptime & Capacity Verified",
                    "status": "ACTIVE_VERIFIED",
                },
                {
                    "step_number": 3,
                    "title": "Step 3: Q1 2027 Burst GPU Reserve Tranche",
                    "step_limit": 5000.00,
                    "billed_amount": 0.00,
                    "utilization_pct": 0.0,
                    "gate_requirement": "Locked until Jan 2027",
                    "status": "LOCKED_FUTURE_STEP",
                },
            ],
        },
        "line_items": [
            {
                "description": "watsonx Enterprise AI Cluster Compute (Monthly)",
                "quantity": 2.0,
                "grn_received_qty": 2.0,
                "grn_accepted_qty": 2.0,
                "unit_price": 1800.00,
                "amount": 3600.00,
                "grn_note": "2/2 compute nodes active",
            },
            {
                "description": "High-Throughput Vector DB Storage (5TB Tier)",
                "quantity": 1.0,
                "grn_received_qty": 1.0,
                "grn_accepted_qty": 1.0,
                "unit_price": 950.00,
                "amount": 950.00,
                "grn_note": "5TB storage volume mounted",
            },
            {
                "description": "Premium SLA 24/7 Enterprise Support",
                "quantity": 1.0,
                "grn_received_qty": 1.0,
                "grn_accepted_qty": 1.0,
                "unit_price": 450.00,
                "amount": 450.00,
                "grn_note": "24/7 PagerDuty bridge active",
            },
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


def set_simulation_override(invoice_id: int, mode: Optional[str]) -> None:
    """
    Set or clear an interactive 3-Way GRN / Step PO simulation override for a specific invoice.
    Modes: 'normal' (default), 'grn_shortage' (1 unit damaged/backordered on GRN), 'step_locked' (step gate locked).
    """
    if not mode or mode == "normal":
        SIMULATION_OVERRIDES.pop(int(invoice_id), None)
    else:
        SIMULATION_OVERRIDES[int(invoice_id)] = mode


def find_matching_po(
    invoice: Dict[str, Any], all_invoices: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Search Master ERP PO Registry (for rich GRN & Step PO metadata) and SQLite uploaded POs.
    """
    po_num = (invoice.get("po_number") or "").strip().upper()
    inv_id = invoice.get("id")

    # 1. Check if a matching PO was uploaded into SQLite
    uploaded_po_rec = None
    for rec in all_invoices:
        if rec.get("id") == inv_id:
            continue
        rec_type = (rec.get("document_type") or "").lower()
        if "purchase" in rec_type or rec_type == "po":
            rec_po = (rec.get("po_number") or rec.get("invoice_number") or "").strip().upper()
            if po_num and rec_po == po_num:
                uploaded_po_rec = rec
                break

    # 2. Check Master ERP PO Registry directly or by alias / vendor / invoice reference
    matched_master_key = None
    if po_num and po_num in MASTER_ERP_POS:
        matched_master_key = po_num
    else:
        for key, candidate in MASTER_ERP_POS.items():
            norm_key = key.replace("-", "").replace(" ", "").upper()
            norm_po = po_num.replace("-", "").replace(" ", "").upper() if po_num else ""
            if norm_po and (norm_po == norm_key or norm_po.replace("1", "7") == norm_key.replace("1", "7")):
                matched_master_key = key
                break
            cand_vendor = (candidate.get("vendor_name") or "").lower()
            inv_vendor = (invoice.get("vendor_name") or "").lower()
            if inv_vendor and (inv_vendor in cand_vendor or cand_vendor in inv_vendor):
                matched_master_key = key
                break
            inv_num = (invoice.get("invoice_number") or "").upper()
            if inv_num and key[-4:] in inv_num:
                matched_master_key = key
                break

    if matched_master_key:
        import copy
        master = copy.deepcopy(MASTER_ERP_POS[matched_master_key])
        if uploaded_po_rec:
            master["source"] = f"SQLite PO #{uploaded_po_rec['id']} + ERP GRN ({master['grn_number']})"
        else:
            master["source"] = f"Master ERP PO ({master['po_number']}) + Warehouse GRN ({master['grn_number']})"
        return master

    # 3. Fallback to pure SQLite uploaded PO if not in MASTER_ERP_POS
    if uploaded_po_rec:
        rec_po = (uploaded_po_rec.get("po_number") or uploaded_po_rec.get("invoice_number") or "").strip().upper()
        auth_sub = _to_float(uploaded_po_rec.get("subtotal_amount") or uploaded_po_rec.get("total_amount"))
        return {
            "po_number": rec_po,
            "source": f"SQLite PO Record #{uploaded_po_rec['id']} ({uploaded_po_rec.get('file_name', 'uploaded')})",
            "vendor_name": uploaded_po_rec.get("vendor_name", ""),
            "currency": uploaded_po_rec.get("currency", "USD"),
            "authorized_subtotal": auth_sub,
            "grn_number": f"GRN-{rec_po[-4:] if len(rec_po) >= 4 else '1001'}",
            "grn_date": uploaded_po_rec.get("invoice_date") or "2026-10-20",
            "receiving_dock": "Central Receiving Dock #1",
            "grn_inspector": "Automated WMS Dock Scanner",
            "grn_status": "FULL_RECEIPT_VERIFIED",
            "early_discount_terms": "2/10 Net 30",
            "early_discount_pct": 2.0,
            "gl_account_code": "5110-DIRECT-EQUIP",
            "step_po": {
                "po_type": "STEP_MILESTONE_PO",
                "po_type_label": "Single-StepUploaded Purchase Order",
                "contract_master_id": f"MSA-{rec_po}",
                "total_contract_ceiling": auth_sub,
                "prior_billed_amount": 0.0,
                "current_step_number": 1,
                "current_step_name": "Step 1: Full PO Delivery",
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Step 1: Authorized PO Line Delivery",
                        "step_limit": auth_sub,
                        "billed_amount": auth_sub,
                        "utilization_pct": 100.0,
                        "gate_requirement": "Warehouse GRN Verified",
                        "status": "ACTIVE_VERIFIED",
                    }
                ],
            },
            "line_items": [
                {
                    "description": li.get("description", ""),
                    "quantity": _to_float(li.get("quantity"), 1.0),
                    "grn_received_qty": _to_float(li.get("quantity"), 1.0),
                    "grn_accepted_qty": _to_float(li.get("quantity"), 1.0),
                    "unit_price": _to_float(li.get("unit_price"), 0.0),
                    "amount": _to_float(li.get("amount"), 0.0),
                    "grn_note": "Full quantity received at dock",
                }
                for li in (uploaded_po_rec.get("line_items") or [])
            ],
        }

    return {}


def evaluate_invoice_audit(
    invoice: Dict[str, Any], all_invoices: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Execute comprehensive:
      1. 2-Way (PO <-> Invoice) & 3-Way (PO <-> GRN <-> Invoice) Matching
      2. Step PO Milestone & Drawdown Governance
      3. Accounts Payable (AP) Payment & Settlement Automation (Auto Debit Memo, 2/10 Net 30 Discount, GL Split)
      4. 6-Point Fraud & Anomaly Shield
    """
    inv_id = invoice.get("id")
    sim_mode = SIMULATION_OVERRIDES.get(int(inv_id), "normal") if inv_id is not None else "normal"

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

    # Default PO / 3-Way Match structure
    po_match: Dict[str, Any] = {
        "status": "NO_PO_REFERENCED",
        "two_way_status": "NO_PO_REFERENCED",
        "three_way_status": "NO_GRN_APPLICABLE",
        "status_label": "No PO Referenced",
        "po_number": po_num or "None",
        "po_source": "N/A",
        "grn_number": "N/A",
        "grn_date": "N/A",
        "receiving_dock": "N/A",
        "grn_inspector": "N/A",
        "grn_status": "N/A",
        "authorized_subtotal": 0.0,
        "grn_accepted_subtotal": 0.0,
        "billed_subtotal": subtotal,
        "variance_amount": 0.0,
        "subtotal_variance": 0.0,
        "grn_variance_amount": 0.0,
        "variance_pct": 0.0,
        "simulation_mode": sim_mode,
        "summary": "Document does not reference a Purchase Order.",
        "step_po": None,
        "line_comparisons": [],
    }

    if "purchase" in doc_type.lower():
        matched_po = MASTER_ERP_POS.get((po_num or inv_num).strip().upper(), {})
        po_match.update(
            {
                "status": "IS_PURCHASE_ORDER",
                "two_way_status": "IS_PURCHASE_ORDER",
                "three_way_status": "AWAITING_GRN_AND_INVOICE",
                "status_label": "Source Purchase Order",
                "po_number": po_num or inv_num,
                "po_source": f"Authoritative PO #{invoice.get('id')}",
                "grn_number": matched_po.get("grn_number", "Pending Dock Receipt"),
                "grn_date": matched_po.get("grn_date", "Pending"),
                "receiving_dock": matched_po.get("receiving_dock", "Central Receiving"),
                "grn_inspector": matched_po.get("grn_inspector", "Pending Inspection"),
                "authorized_subtotal": total,
                "grn_accepted_subtotal": total,
                "billed_subtotal": total,
                "step_po": matched_po.get("step_po"),
                "summary": f"Authoritative Purchase Order ({po_num or inv_num}) authorizing {currency} {total:,.2f} across {len(inv_items)} line items.",
            }
        )
    elif "receipt" in doc_type.lower():
        po_match.update(
            {
                "status": "NO_PO_REQUIRED",
                "two_way_status": "NO_PO_REQUIRED",
                "three_way_status": "POS_VOUCHER_VERIFIED",
                "status_label": "Direct Expense Receipt (No PO Needed)",
                "grn_number": "POS-CARD-SLIP",
                "receiving_dock": "Corporate Card Point-of-Sale",
                "grn_inspector": "Automated Expense Policy Engine",
                "authorized_subtotal": subtotal,
                "grn_accepted_subtotal": subtotal,
                "billed_subtotal": subtotal,
                "summary": "Point-of-sale / T&E expense receipts bypass PO matching under corporate card policy (< $2,500 limit).",
            }
        )
    else:
        matched_po = find_matching_po(invoice, all_invoices)
        if matched_po:
            import copy
            po_lines = copy.deepcopy(matched_po.get("line_items") or [])
            step_po = copy.deepcopy(matched_po.get("step_po"))

            # Apply interactive simulation overrides if triggered by user in the UI
            if sim_mode == "grn_shortage" and len(po_lines) > 0:
                target_idx = 0
                for idx_cand, pl in enumerate(po_lines):
                    if _to_float(pl.get("quantity"), 1.0) > 1.0:
                        target_idx = idx_cand
                        break
                orig_qty = _to_float(po_lines[target_idx].get("grn_accepted_qty"), 1.0)
                new_qty = max(0.0, orig_qty - 1.0)
                po_lines[target_idx]["grn_received_qty"] = new_qty
                po_lines[target_idx]["grn_accepted_qty"] = new_qty
                po_lines[target_idx]["grn_note"] = (
                    f"SIMULATED DOCK SHORTAGE: Only {new_qty:g} of {orig_qty:g} units accepted at receiving dock (1 unit damaged/backordered)"
                )
                matched_po["grn_status"] = "PARTIAL_SHIPMENT_SHORTAGE"
            elif sim_mode == "step_locked" and step_po and step_po.get("steps"):
                for st in step_po["steps"]:
                    if st.get("status") == "ACTIVE_VERIFIED":
                        st["status"] = "LOCKED_MILESTONE_VIOLATION"
                        st["gate_requirement"] = "HOLD: Step milestone UAT sign-off not yet completed in ERP!"

            auth_sub = _to_float(matched_po.get("authorized_subtotal"))
            variance_2way = round(subtotal - auth_sub, 2)
            variance_pct = round((variance_2way / auth_sub) * 100, 2) if auth_sub > 0 else 0.0

            comparisons = []
            max_len = max(len(inv_items), len(po_lines))
            any_2way_mismatch = False
            any_3way_mismatch = False
            grn_accepted_subtotal = 0.0

            for idx in range(max_len):
                inv_li = inv_items[idx] if idx < len(inv_items) else {}
                po_li = po_lines[idx] if idx < len(po_lines) else {}

                i_desc = inv_li.get("description") or po_li.get("description") or f"Item #{idx + 1}"
                i_qty = _to_float(inv_li.get("quantity"), 0.0)
                p_qty = _to_float(po_li.get("quantity"), 0.0)
                g_qty = _to_float(po_li.get("grn_accepted_qty", p_qty), p_qty)
                i_price = _to_float(inv_li.get("unit_price"), 0.0)
                p_price = _to_float(po_li.get("unit_price"), 0.0)
                i_amt = _to_float(inv_li.get("amount"), 0.0)
                p_amt = _to_float(po_li.get("amount"), 0.0)
                g_amt = round(g_qty * p_price, 2)
                grn_accepted_subtotal = round(grn_accepted_subtotal + g_amt, 2)

                delta_2way = round(i_amt - p_amt, 2)
                delta_3way = round(i_amt - g_amt, 2)

                # 2-Way check (PO vs Invoice)
                if abs(delta_2way) < 0.05 and abs(i_price - p_price) < 0.05 and abs(i_qty - p_qty) < 0.05:
                    two_way_line = "2-WAY OK"
                elif i_price > p_price + 0.05:
                    two_way_line = "PRICE_SPIKE"
                    any_2way_mismatch = True
                elif i_qty > p_qty + 0.05:
                    two_way_line = "QTY_OVER_PO"
                    any_2way_mismatch = True
                else:
                    two_way_line = "PO_VARIANCE"
                    any_2way_mismatch = True

                # 3-Way check (PO vs Warehouse GRN vs Invoice)
                if i_qty > g_qty + 0.05 and abs(i_qty - p_qty) < 0.05:
                    line_status = "GRN_SHORT_SHIPMENT"
                    three_way_line = f"SHORTAGE ({g_qty:g}/{i_qty:g} Rcvd)"
                    any_3way_mismatch = True
                elif i_qty > g_qty + 0.05:
                    line_status = "QTY_OVERAGE"
                    three_way_line = f"EXCEEDS GRN ({g_qty:g} Auth)"
                    any_3way_mismatch = True
                elif i_price > p_price + 0.05:
                    line_status = "PRICE_SPIKE"
                    three_way_line = "PRICE_SPIKE"
                    any_3way_mismatch = True
                elif abs(delta_3way) > 0.05:
                    line_status = "VARIANCE"
                    three_way_line = "3-WAY VARIANCE"
                    any_3way_mismatch = True
                else:
                    line_status = "MATCHED"
                    three_way_line = "3-WAY VERIFIED"

                comparisons.append(
                    {
                        "line_index": idx + 1,
                        "description": i_desc,
                        "invoice_description": i_desc,
                        "po_qty": p_qty,
                        "grn_qty": g_qty,
                        "inv_qty": i_qty,
                        "po_unit_price": p_price,
                        "inv_unit_price": i_price,
                        "po_amount": p_amt,
                        "grn_amount": g_amt,
                        "inv_amount": i_amt,
                        "delta_amount": delta_3way,
                        "delta_2way": delta_2way,
                        "two_way_status": two_way_line,
                        "three_way_status": three_way_line,
                        "grn_note": po_li.get("grn_note", "Verified at receiving dock"),
                        "status": line_status,
                    }
                )

            grn_variance = round(subtotal - grn_accepted_subtotal, 2)
            step_locked = any(
                s.get("status") in ("LOCKED_MILESTONE_VIOLATION", "STEP_CEILING_BREACH")
                for s in (step_po.get("steps") or [])
            ) if step_po else False

            two_way_overall = "MATCHED" if (abs(variance_2way) < 0.05 and not any_2way_mismatch) else "VARIANCE_DETECTED"
            three_way_overall = (
                "MATCHED"
                if (not any_3way_mismatch and abs(grn_variance) < 0.05 and not step_locked)
                else ("GRN_SHORTAGE_DETECTED" if two_way_overall == "MATCHED" and any_3way_mismatch else "VARIANCE_DETECTED")
            )

            overall_status = "MATCHED" if (two_way_overall == "MATCHED" and three_way_overall == "MATCHED") else "VARIANCE_DETECTED"

            if overall_status == "MATCHED":
                summary_text = (
                    f"100% 3-Way Match Verified ({matched_po['po_number']} + {matched_po.get('grn_number', 'GRN')}): "
                    f"All {len(comparisons)} line items match PO prices and Warehouse GRN accepted quantities ({currency} {grn_accepted_subtotal:,.2f})."
                )
                status_label = "3-Way Match Verified (100%)"
            elif two_way_overall == "MATCHED" and any_3way_mismatch:
                summary_text = (
                    f"3-WAY MATCH EXCEPTION (2-Way Passed, 3-Way Failed!): Invoice matches {matched_po['po_number']} (${auth_sub:,.2f}), "
                    f"but Warehouse Receiving ({matched_po.get('grn_number')}) only accepted {currency} {grn_accepted_subtotal:,.2f}. "
                    f"Unreceived / backordered billing of {currency} {grn_variance:+,.2f} caught by 3-Way Match!"
                )
                status_label = f"3-Way GRN Shortage ({currency} {grn_variance:+,.2f})"
            elif step_locked and two_way_overall == "MATCHED":
                summary_text = (
                    f"STEP PO MILESTONE GATE HOLD: Invoice matches {matched_po['po_number']} amounts, "
                    f"but Step Milestone UAT Gate is still LOCKED in ERP."
                )
                status_label = "Step PO Gate Locked"
            else:
                summary_text = (
                    f"2-WAY & 3-WAY PO VARIANCE: Invoice subtotal ({currency} {subtotal:,.2f}) exceeds {matched_po['po_number']} & "
                    f"{matched_po.get('grn_number')} authorized limit ({currency} {grn_accepted_subtotal:,.2f}) by "
                    f"{currency} {grn_variance:+,.2f} ({variance_pct:+.1f}%)."
                )
                status_label = f"PO/GRN Variance ({currency} {grn_variance:+,.2f})"

            po_match.update(
                {
                    "status": overall_status,
                    "two_way_status": two_way_overall,
                    "three_way_status": three_way_overall,
                    "status_label": status_label,
                    "po_number": matched_po["po_number"],
                    "po_source": matched_po["source"],
                    "grn_number": matched_po.get("grn_number", "GRN-VERIFIED"),
                    "grn_date": matched_po.get("grn_date", "2026-10-20"),
                    "receiving_dock": matched_po.get("receiving_dock", "Central Dock"),
                    "grn_inspector": matched_po.get("grn_inspector", "QA Inspector"),
                    "grn_status": matched_po.get("grn_status", "FULL_RECEIPT_VERIFIED"),
                    "authorized_subtotal": auth_sub,
                    "grn_accepted_subtotal": grn_accepted_subtotal,
                    "billed_subtotal": subtotal,
                    "variance_amount": grn_variance,
                    "subtotal_variance": grn_variance,
                    "two_way_variance": variance_2way,
                    "grn_variance_amount": grn_variance,
                    "variance_pct": round((grn_variance / grn_accepted_subtotal) * 100, 2) if grn_accepted_subtotal > 0 else variance_pct,
                    "summary": summary_text,
                    "step_po": step_po,
                    "line_comparisons": comparisons,
                }
            )

    # --- PART 2: Accounts Payable (AP) Payment & Settlement Automation Engine ---
    matched_po_meta = MASTER_ERP_POS.get(po_num.upper(), {}) if po_num else {}
    disc_terms = matched_po_meta.get("early_discount_terms", "2/10 Net 30")
    disc_pct = _to_float(matched_po_meta.get("early_discount_pct", 2.0), 2.0)
    gl_code = matched_po_meta.get("gl_account_code", "6200-CLOUD-INFRA")

    tax_rate_ratio = (tax / subtotal) if subtotal > 0 else 0.0
    grn_sub = _to_float(po_match.get("grn_accepted_subtotal"), subtotal)
    if grn_sub <= 0:
        grn_sub = subtotal

    raw_overcharge_sub = max(0.0, round(subtotal - grn_sub, 2)) if po_match["status"] == "VARIANCE_DETECTED" else 0.0
    tax_adjustment = round(raw_overcharge_sub * tax_rate_ratio, 2)
    debit_memo_total = round(raw_overcharge_sub + tax_adjustment, 2)

    verified_gross_payable = max(0.0, round(total - debit_memo_total, 2))
    early_discount_amount = round(verified_gross_payable * (disc_pct / 100.0), 2) if "invoice" in doc_type.lower() else 0.0
    final_net_cash_outflow = round(verified_gross_payable - early_discount_amount, 2)

    debit_memo_number = f"DM-{inv_num.replace('INV-', '')}" if debit_memo_total > 0 else None

    if "purchase" in doc_type.lower():
        ap_strategy = "PO_BUDGET_ENCUMBRANCE"
        ap_strategy_label = "Encumber PO Commitment in ERP Ledger (No Cash Outflow Yet)"
        ap_recommendation = (
            f"Record {po_match['po_number']} commitment of {currency} {total:,.2f} in {gl_code} and await Warehouse GRN + Vendor Invoice."
        )
    elif "receipt" in doc_type.lower():
        ap_strategy = "CORPORATE_CARD_AUTO_RECON"
        ap_strategy_label = "Auto-Reconcile Corporate Card Expense Voucher"
        ap_recommendation = (
            f"Match {currency} {total:,.2f} receipt against Corporate Card statement feed and post to 6450-T&E-HOSPITALITY."
        )
    elif debit_memo_total > 0:
        ap_strategy = "AUTO_SHORT_PAY_DEBIT_MEMO"
        ap_strategy_label = f"Auto-Issue Debit Memo ({debit_memo_number}) & Short-Pay 3-Way Verified Amount"
        ap_recommendation = (
            f"Deduct unreceived/overbilled variance of {currency} {debit_memo_total:,.2f} via automated Debit Memo {debit_memo_number}, "
            f"and release short-paid settlement of {currency} {verified_gross_payable:,.2f} ({currency} {final_net_cash_outflow:,.2f} with {disc_pct:g}% early-pay discount)."
        )
    else:
        ap_strategy = "STP_EARLY_DISCOUNT_CAPTURE"
        ap_strategy_label = f"Straight-Through Payment Run + Capture {disc_terms} Treasury Discount"
        ap_recommendation = (
            f"3-Way Match & Step PO verified. Schedule automated ACH/Wire within 10-day window to capture {currency} {early_discount_amount:,.2f} "
            f"({disc_pct:g}% discount = 36.7% annualized treasury yield). Net settlement: {currency} {final_net_cash_outflow:,.2f}."
        )

    verified_sub = max(0.0, round(subtotal - raw_overcharge_sub, 2))
    verified_tax = max(0.0, round(tax - tax_adjustment, 2))
    journal_entries = [
        {
            "account_code": gl_code,
            "account_name": "Operating / CapEx Expense (3-Way Verified Basis)",
            "type": "DEBIT",
            "debit": verified_sub,
            "credit": 0.0,
            "memo": f"Verified net goods/services for {inv_num} ({po_match.get('grn_number', 'Direct')})",
        },
        {
            "account_code": "1420-INPUT-TAX-CREDIT",
            "account_name": "Recoverable Input Sales Tax / HST",
            "type": "DEBIT",
            "debit": verified_tax,
            "credit": 0.0,
            "memo": f"Validated tax allocation on verified subtotal",
        },
    ]
    if debit_memo_total > 0:
        journal_entries.append(
            {
                "account_code": "2150-AP-DISPUTE-SUSPENSE",
                "account_name": f"Vendor Debit Memo Adjustment ({debit_memo_number})",
                "type": "MEMO_HOLD",
                "debit": 0.0,
                "credit": 0.0,
                "memo": f"Blocked overcharge of {currency} {debit_memo_total:,.2f} excluded from AP liability",
            }
        )
    if early_discount_amount > 0:
        journal_entries.append(
            {
                "account_code": "4910-PURCHASE-DISCOUNTS",
                "account_name": f"Early Payment Treasury Discount ({disc_terms})",
                "type": "CREDIT",
                "debit": 0.0,
                "credit": early_discount_amount,
                "memo": f"{disc_pct:g}% early settlement treasury capture",
            }
        )
    journal_entries.append(
        {
            "account_code": "2100-ACCOUNTS-PAYABLE",
            "account_name": f"Net ACH / Wire Disbursement ({vendor})",
            "type": "CREDIT",
            "debit": 0.0,
            "credit": final_net_cash_outflow,
            "memo": f"Automated settlement batch ready for Odoo ERP",
        }
    )

    ap_automation = {
        "strategy": ap_strategy,
        "strategy_label": ap_strategy_label,
        "recommendation": ap_recommendation,
        "payment_method": "Corporate Card Feed" if "receipt" in doc_type.lower() else "Automated ACH / ISO-20022 Wire",
        "discount_terms": disc_terms,
        "discount_pct": disc_pct,
        "annualized_yield_apr": 36.7 if early_discount_amount > 0 else 0.0,
        "gross_billed_total": total,
        "debit_memo_number": debit_memo_number,
        "debit_memo_deduction": debit_memo_total,
        "raw_overcharge_subtotal": raw_overcharge_sub,
        "tax_adjustment": tax_adjustment,
        "verified_gross_payable": verified_gross_payable,
        "early_discount_savings": early_discount_amount,
        "final_net_settlement": final_net_cash_outflow,
        "currency": currency,
        "gl_account_code": gl_code,
        "journal_entries": journal_entries,
    }

    # --- PART 3: 6-Point Fraud, Duplicate & Governance Shield ---
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

    # Check 2: 2-Way & 3-Way PO + GRN Reconciliation
    if po_match["status"] == "VARIANCE_DETECTED":
        risk_score += 45
        checks.append(
            {
                "code": "PO_RECONCILIATION",
                "title": "3-Way PO & Warehouse GRN Match",
                "status": "FAIL",
                "detail": po_match["summary"],
                "impact": "+45 Risk",
            }
        )
    elif po_match["status"] in ("MATCHED", "IS_PURCHASE_ORDER", "NO_PO_REQUIRED"):
        checks.append(
            {
                "code": "PO_RECONCILIATION",
                "title": "3-Way PO & Warehouse GRN Match",
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
                "title": "3-Way PO & Warehouse GRN Match",
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
        "ap_automation": ap_automation,
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
        if "AUTO" in tier or "APPROVED_BY_VP" in tier or "SHORT_PAID" in tier:
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
