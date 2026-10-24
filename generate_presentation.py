"""
Generates the official 2-Slide Executive Submission Pitch Deck for IBM Asset Catalog.
Widescreen 16:9 (13.333" x 7.5").
Slide 1: Problem Statement & Value Proposition
Slide 2: Enterprise Reference Architecture Deep Dive (with Gmail, SAP, and watsonx Orchestrate logos)
"""

import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

OUTPUT_PPTX = "IBM_watsonx_Orchestrate_AP_Automation.pptx"

# Color Palette (IBM Carbon Theme)
DARK_BG = RGBColor(18, 22, 31)         # #12161F
CARD_BG = RGBColor(27, 34, 48)         # #1B2230
CARD_BORDER = RGBColor(46, 56, 77)     # #2E384D
IBM_BLUE = RGBColor(15, 98, 254)       # #0F62FE
CYAN_ACCENT = RGBColor(17, 146, 232)   # #1192E8
GREEN_ACCENT = RGBColor(36, 161, 72)   # #24A148
RED_ACCENT = RGBColor(218, 30, 40)     # #DA1E28
AMBER_ACCENT = RGBColor(241, 194, 27)  # #F1C21B
WHITE = RGBColor(255, 255, 255)
GRAY_TEXT = RGBColor(198, 202, 207)    # #C6CACF
MUTED_TEXT = RGBColor(141, 149, 160)   # #8D95A0


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # SLIDE 1: PROBLEM STATEMENT & VALUE PROPOSITION
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)

    # Background
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = DARK_BG
    bg1.line.color.rgb = DARK_BG

    # Header Badge
    badge1 = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.4), Inches(4.2), Inches(0.35))
    badge1.fill.solid()
    badge1.fill.fore_color.rgb = RGBColor(15, 98, 254)
    badge1.line.color.rgb = RGBColor(15, 98, 254)
    tf_b1 = badge1.text_frame
    tf_b1.text = "IBM watsonx™ Orchestrate • Enterprise Asset Submission"
    p_b1 = tf_b1.paragraphs[0]
    p_b1.font.size = Pt(11)
    p_b1.font.bold = True
    p_b1.font.color.rgb = WHITE
    p_b1.alignment = PP_ALIGN.CENTER

    # Title & Subtitle
    title_box = slide1.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(1.1))
    tf_t1 = title_box.text_frame
    tf_t1.word_wrap = True
    p_t1 = tf_t1.paragraphs[0]
    p_t1.text = "Autonomous Accounts Payable & 3-Way Reconciliation IDP"
    p_t1.font.size = Pt(26)
    p_t1.font.bold = True
    p_t1.font.color.rgb = WHITE

    p_sub1 = tf_t1.add_paragraph()
    p_sub1.text = "Eliminating multimillion-dollar cash leakage, manual invoice entry, and procurement audit blindspots."
    p_sub1.font.size = Pt(13)
    p_sub1.font.color.rgb = GRAY_TEXT

    # Two main columns: Left = Problem Statement, Right = Solution & Value
    col_w = Inches(5.65)
    gap = Inches(0.4)
    left_x = Inches(0.8)
    right_x = left_x + col_w + gap
    card_y = Inches(2.05)
    card_h = Inches(4.0)

    # --- LEFT CONTAINER: PROBLEM STATEMENT ---
    p_card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_x, card_y, col_w, card_h)
    p_card.fill.solid()
    p_card.fill.fore_color.rgb = CARD_BG
    p_card.line.color.rgb = CARD_BORDER
    p_card.line.width = Pt(1.5)

    # Left Container Header
    tf_pc = p_card.text_frame
    tf_pc.word_wrap = True
    tf_pc.margin_left = Inches(0.3)
    tf_pc.margin_top = Inches(0.25)
    tf_pc.margin_right = Inches(0.3)

    p_pch = tf_pc.paragraphs[0]
    p_pch.text = "THE PROBLEM: Critical Flaws in Legacy AP Workflows"
    p_pch.font.size = Pt(14)
    p_pch.font.bold = True
    p_pch.font.color.rgb = RED_ACCENT

    problems = [
        ("1. Multi-Format & Unstructured Document Chaos",
         "Invoices, receipts, and POs arrive via email attachments (Gmail), scans, and portals in volatile layouts. Legacy OCR fails on tables and bounding-box coordinates, forcing costly manual re-keying."),
        ("2. The 3-Way Matching Blindspot (Billing vs Dock Shortages)",
         "Enterprises pay invoices without cross-verifying physical Goods Receipt Notes (GRN) or Service Entry Sheets (SES). Dock shortages (e.g., backorders) and unapproved Red-Team days cause massive cash leakage."),
        ("3. Complex Step PO & Volume-Tier Ceiling Breaches",
         "Multi-phase milestone contracts (Step POs) and volume-tiered BPA agreements are monitored in offline spreadsheets, allowing vendors to overbill beyond authorized step budget ceilings."),
        ("4. ERP Disconnect & Missed Treasury Discounts",
         "Manual ERP invoice entry in SAP/Odoo creates processing lag (3-5 days), causing forfeiture of 2/10 Net 30 early payment discounts (~36% annualized yield) and late-payment interest fees.")
    ]

    for title, desc in problems:
        p_pt = tf_pc.add_paragraph()
        p_pt.text = title
        p_pt.font.size = Pt(11.5)
        p_pt.font.bold = True
        p_pt.font.color.rgb = WHITE
        p_pt.space_before = Pt(8)

        p_pd = tf_pc.add_paragraph()
        p_pd.text = desc
        p_pd.font.size = Pt(10)
        p_pd.font.color.rgb = GRAY_TEXT
        p_pd.space_before = Pt(2)

    # --- RIGHT CONTAINER: THE SOLUTION & BUSINESS VALUE ---
    s_card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, right_x, card_y, col_w, card_h)
    s_card.fill.solid()
    s_card.fill.fore_color.rgb = CARD_BG
    s_card.line.color.rgb = CARD_BORDER
    s_card.line.width = Pt(1.5)

    tf_sc = s_card.text_frame
    tf_sc.word_wrap = True
    tf_sc.margin_left = Inches(0.3)
    tf_sc.margin_top = Inches(0.25)
    tf_sc.margin_right = Inches(0.3)

    p_sch = tf_sc.paragraphs[0]
    p_sch.text = "THE SOLUTION: Autonomous watsonx Orchestration"
    p_sch.font.size = Pt(14)
    p_sch.font.bold = True
    p_sch.font.color.rgb = CYAN_ACCENT

    solutions = [
        ("1. Multimodal Document Grounding & WDU Extraction",
         "watsonx Orchestrate Document Processing extracts complex nested line items, tax, and terms with visual bounding-box grounding and OCR confidence telemetry across multi-page documents."),
        ("2. Automated 2-Way & 3-Way Reconciliation Engine",
         "Deterministic Python logic cross-examines Invoice vs PO vs Warehouse Dock GRN/SES in real time. Discrepancies are trapped instantly (e.g. +$800 red-team overrun on PO-77504)."),
        ("3. Automated Short-Pay Settlement & Debit Memo Generation",
         "When shortages occur (e.g., PO-2026-7731 dock receipt shortage of 1 optical pack), AP automatically issues Debit Memo DM-2026-7731 (-$702.00) and short-pays the net amount."),
        ("4. Live SAP ERP & Neon Cloud Database Synchronization",
         "Direct XML-RPC / BAPI RFC connector automatically posts validated bills to SAP / Odoo, splits GL accounts, captures 2/10 Net 30 yields, and archives immutable audit trails in Neon PostgreSQL.")
    ]

    for title, desc in solutions:
        p_st = tf_sc.add_paragraph()
        p_st.text = title
        p_st.font.size = Pt(11.5)
        p_st.font.bold = True
        p_st.font.color.rgb = WHITE
        p_st.space_before = Pt(8)

        p_sd = tf_sc.add_paragraph()
        p_sd.text = desc
        p_sd.font.size = Pt(10)
        p_sd.font.color.rgb = GRAY_TEXT
        p_sd.space_before = Pt(2)

    # --- BOTTOM KPI STRIP ---
    kpi_y = Inches(6.18)
    kpis = [
        ("94.8%", "Straight-Through Processing (STP) Rate", GREEN_ACCENT),
        ("85%", "AP Cycle Time Reduction (3 Days → 4 Mins)", CYAN_ACCENT),
        ("$1,566.00+", "Leakage Prevented via Auto Debit Memos", AMBER_ACCENT),
        ("36.7%", "Annualized Treasury Yield (2/10 Net 30)", IBM_BLUE),
    ]
    kw = (Inches(11.7) - Inches(0.3) * 3) / 4
    for i, (metric, label, color) in enumerate(kpis):
        kx = Inches(0.8) + i * (kw + Inches(0.3))
        kbox = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, kx, kpi_y, kw, Inches(0.95))
        kbox.fill.solid()
        kbox.fill.fore_color.rgb = CARD_BG
        kbox.line.color.rgb = color
        kbox.line.width = Pt(1.5)

        tf_k = kbox.text_frame
        tf_k.word_wrap = True
        tf_k.margin_left = Inches(0.15)
        tf_k.margin_top = Inches(0.12)
        tf_k.margin_right = Inches(0.15)
        p_km = tf_k.paragraphs[0]
        p_km.text = metric
        p_km.font.size = Pt(20)
        p_km.font.bold = True
        p_km.font.color.rgb = color
        p_km.alignment = PP_ALIGN.CENTER

        p_kl = tf_k.add_paragraph()
        p_kl.text = label
        p_kl.font.size = Pt(9.5)
        p_kl.font.color.rgb = GRAY_TEXT
        p_kl.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 2: ARCHITECTURE DEEP DIVE
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)

    # Background
    bg2 = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg2.fill.solid()
    bg2.fill.fore_color.rgb = DARK_BG
    bg2.line.color.rgb = DARK_BG

    # Header Badge
    badge2 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.38), Inches(3.6), Inches(0.32))
    badge2.fill.solid()
    badge2.fill.fore_color.rgb = CYAN_ACCENT
    badge2.line.color.rgb = CYAN_ACCENT
    tf_b2 = badge2.text_frame
    tf_b2.text = "End-to-End Enterprise Reference Architecture"
    p_b2 = tf_b2.paragraphs[0]
    p_b2.font.size = Pt(10.5)
    p_b2.font.bold = True
    p_b2.font.color.rgb = WHITE
    p_b2.alignment = PP_ALIGN.CENTER

    # Title & Subtitle
    title_box2 = slide2.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.95))
    tf_t2 = title_box2.text_frame
    tf_t2.word_wrap = True
    p_t2 = tf_t2.paragraphs[0]
    p_t2.text = "IBM watsonx™ Orchestrate AP Engine & SAP Integration"
    p_t2.font.size = Pt(24)
    p_t2.font.bold = True
    p_t2.font.color.rgb = WHITE

    p_sub2 = tf_t2.add_paragraph()
    p_sub2.text = "Event-driven architecture connecting automated email/portal ingestion, deterministic rules, and enterprise systems of record."
    p_sub2.font.size = Pt(12)
    p_sub2.font.color.rgb = GRAY_TEXT

    # 4 Architecture Pillars across the slide
    pillar_w = Inches(2.7)
    pillar_gap = Inches(0.3)
    p_start_x = Inches(0.8)
    p_y = Inches(1.8)
    p_h = Inches(5.2)

    pillars_info = [
        {
            "num": "01",
            "name": "Multichannel Ingestion",
            "color": RGBColor(234, 67, 53),  # Gmail red accent
            "logo": "frontend/gmail_logo.png",
            "logo_h": Inches(0.75),
            "logo_w": Inches(0.98),
            "tag": "Inbound Feeds",
            "bullets": [
                ("Gmail IMAP / SMTP Gateway", "Automated background poller extracting raw invoice PDFs & image attachments directly from vendor emails."),
                ("Web Portal & REST Ingestion", "Carbon Design drag-and-drop workspace supporting direct multi-part uploads & ERP webhook push."),
                ("Multimodal Document Spectrum", "Supports Vendor Invoices, Step POs, Freight Bills, and Travel/Dining Receipts (e.g. Swiggy/Bluefin).")
            ]
        },
        {
            "num": "02",
            "name": "watsonx Orchestrate Core",
            "color": IBM_BLUE,
            "logo": "frontend/watsonx_orchestrate_logo_cropped.png",
            "logo_h": Inches(0.40),
            "logo_w": Inches(2.4),
            "tag": "Orchestration & AI",
            "bullets": [
                ("Watson Discovery (WDU) OCR", "Multi-model docproc extracts tabular line items, tax, and terms with spatial bounding box visual grounding."),
                ("Deterministic Python Logic Node", "Rigorous math validation (line-item sums, subtotal + tax = total, 1% tolerance checks, zero-hallucination)."),
                ("watsonx.ai GenAI Prompt Node", "Autonomous GL chart-of-accounts classification and executive audit summarization."),
                ("WXO ADK Conversational Agent", "Embedded interactive copilot with live tool access for CFO queries & bill approval.")
            ]
        },
        {
            "num": "03",
            "name": "Audit & Risk Governance",
            "color": AMBER_ACCENT,
            "tag": "Compliance Shield",
            "bullets": [
                ("3-Way PO Reconciliation Engine", "Matches Purchase Order vs. Warehouse Goods Receipt Note (GRN) vs. Vendor Invoice (catches dock shortages)."),
                ("Step PO Milestone Drawdown Tracker", "Enforces multi-phase drawdown ceilings (Step 1 -> 2 -> 3) and volume-tier BPA rate locks."),
                ("Automated Short-Pay & Debit Memos", "Auto-issues Debit Memo deduction slips (e.g., DM-2026-7731) before payment authorization."),
                ("6-Point Fraud & Risk Shield", "Real-time 0-100 risk scoring, duplicate hash detection, shell vendor verification, split-invoice audit.")
            ]
        },
        {
            "num": "04",
            "name": "System of Record & Cloud DB",
            "color": RGBColor(0, 105, 180),  # SAP blue accent
            "logo": "frontend/sap_logo.png",
            "logo_h": Inches(0.65),
            "logo_w": Inches(1.25),
            "tag": "ERP & Cloud Persistence",
            "bullets": [
                ("Enterprise ERP (SAP / Odoo)", "Live XML-RPC & BAPI RFC sync creating draft/posted Vendor Bills (account.move), GL splits, and approvals."),
                ("Treasury Early-Discount Yield", "Captures 2/10 Net 30 payment yields (36.7% annualized return) based on payment terms."),
                ("Neon Serverless PostgreSQL DB", "Primary cloud DB (PostgreSQL 18.6 on AWS) persisting line items, raw KVPs, and CFO audit telemetry."),
                ("Audit Trail & Compliance Logging", "Immutable record of all OCR extractions, supervisor overrides, and ERP posting timestamps.")
            ]
        }
    ]

    for i, p in enumerate(pillars_info):
        px = p_start_x + i * (pillar_w + pillar_gap)
        
        # Pillar Container Card
        card = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px, p_y, pillar_w, p_h)
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = CARD_BORDER
        card.line.width = Pt(1.5)

        # Header Pill / Number
        tag_box = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px + Inches(0.18), p_y + Inches(0.18), Inches(1.1), Inches(0.28))
        tag_box.fill.solid()
        tag_box.fill.fore_color.rgb = p["color"]
        tag_box.line.color.rgb = p["color"]
        tf_tb = tag_box.text_frame
        tf_tb.text = f"LAYER {p['num']}"
        tf_tb.paragraphs[0].font.size = Pt(9.5)
        tf_tb.paragraphs[0].font.bold = True
        tf_tb.paragraphs[0].font.color.rgb = WHITE
        tf_tb.paragraphs[0].alignment = PP_ALIGN.CENTER

        # Pillar Title
        tf_c = card.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = Inches(0.2)
        tf_c.margin_right = Inches(0.2)
        tf_c.margin_top = Inches(0.55)

        p_cn = tf_c.paragraphs[0]
        p_cn.text = p["name"]
        p_cn.font.size = Pt(13)
        p_cn.font.bold = True
        p_cn.font.color.rgb = WHITE

        # Logo placement inside pillar
        logo_path = p.get("logo")
        curr_y = p_y + Inches(1.05)
        if logo_path and os.path.exists(logo_path):
            lw = p["logo_w"]
            lh = p["logo_h"]
            lx = px + (pillar_w - lw) / 2
            slide2.shapes.add_picture(logo_path, lx, curr_y, lw, lh)
            text_start_offset = Inches(1.0)
        else:
            # Pillar 3: Governance shield badge representation
            shield_badge = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px + Inches(0.25), curr_y, pillar_w - Inches(0.5), Inches(0.65))
            shield_badge.fill.solid()
            shield_badge.fill.fore_color.rgb = RGBColor(38, 48, 68)
            shield_badge.line.color.rgb = AMBER_ACCENT
            tf_sb = shield_badge.text_frame
            tf_sb.text = "🛡️ 3-Way Audit & Anomaly Shield"
            tf_sb.paragraphs[0].font.size = Pt(10)
            tf_sb.paragraphs[0].font.bold = True
            tf_sb.paragraphs[0].font.color.rgb = AMBER_ACCENT
            tf_sb.paragraphs[0].alignment = PP_ALIGN.CENTER
            text_start_offset = Inches(0.85)

        # Bullets Container
        bullet_y = curr_y + text_start_offset
        bullet_box = slide2.shapes.add_textbox(px + Inches(0.12), bullet_y, pillar_w - Inches(0.24), p_h - (bullet_y - p_y) - Inches(0.15))
        tf_b = bullet_box.text_frame
        tf_b.word_wrap = True
        tf_b.margin_left = Inches(0.08)
        tf_b.margin_top = Inches(0.05)
        tf_b.margin_right = Inches(0.08)

        for b_idx, (b_title, b_desc) in enumerate(p["bullets"]):
            p_bt = tf_b.add_paragraph() if b_idx > 0 else tf_b.paragraphs[0]
            p_bt.text = f"• {b_title}"
            p_bt.font.size = Pt(10)
            p_bt.font.bold = True
            p_bt.font.color.rgb = WHITE
            if b_idx > 0:
                p_bt.space_before = Pt(6)

            p_bd = tf_b.add_paragraph()
            p_bd.text = b_desc
            p_bd.font.size = Pt(8.5)
            p_bd.font.color.rgb = GRAY_TEXT
            p_bd.space_before = Pt(1)

        # Add connecting directional arrow between pillars
        if i < 3:
            arrow_x = px + pillar_w + Inches(0.05)
            arrow_y = p_y + Inches(2.3)
            arrow_box = slide2.shapes.add_textbox(arrow_x, arrow_y, pillar_gap - Inches(0.1), Inches(0.5))
            tf_a = arrow_box.text_frame
            p_a = tf_a.paragraphs[0]
            p_a.text = "➔"
            p_a.font.size = Pt(20)
            p_a.font.bold = True
            p_a.font.color.rgb = CYAN_ACCENT
            p_a.alignment = PP_ALIGN.CENTER

    prs.save(OUTPUT_PPTX)
    print(f"Presentation saved successfully to: {OUTPUT_PPTX}")


if __name__ == "__main__":
    create_deck()
