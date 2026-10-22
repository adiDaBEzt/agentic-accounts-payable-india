"""
Generate high-resolution sample invoice, PO, and receipt documents for testing the
watsonx Orchestrate IDP (docproc) pipeline, organized into 4 distinct subfolders:
1. clean_invoices/     - Invoices with 100% 2-Way PO match & Straight-Through Approval
2. variance_invoices/  - Invoices with PO quantity/price variances requiring HITL review
3. purchase_orders/    - Authoritative buyer Purchase Orders with line items
4. receipts/           - Corporate card payment receipts & T&E expense vouchers
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"

SUBFOLDERS = {
    "clean_invoices": SAMPLES_DIR / "clean_invoices",
    "variance_invoices": SAMPLES_DIR / "variance_invoices",
    "purchase_orders": SAMPLES_DIR / "purchase_orders",
    "receipts": SAMPLES_DIR / "receipts",
}

# 1. Clean Invoices (100% Match & STP)
CLEAN_INVOICE_TEMPLATES = [
    {
        "filename": "invoice_acme_cloud_0042.png",
        "pdf_filename": "invoice_acme_cloud_0042.pdf",
        "subfolder": "clean_invoices",
        "category": "Clean Invoices (100% 2-Way Match & STP)",
        "vendor_name": "Acme Cloud Systems Inc.",
        "vendor_address": "500 King Street West, Suite 300, Toronto, ON M5V 1L9",
        "vendor_email": "billing@acmecloud.io | Tax ID: 892-441-092",
        "invoice_number": "INV-2026-0042",
        "invoice_date": "2026-03-15",
        "due_date": "2026-04-14",
        "po_number": "PO-99812",
        "payment_terms": "Net 30",
        "currency": "USD",
        "buyer_name": "Global Logistics Corp.",
        "buyer_address": "120 Broadway, Suite 400, New York, NY 10271",
        "line_items": [
            {
                "description": "watsonx Orchestrate Enterprise Connector License",
                "quantity": "2",
                "unit_price": "1500.00",
                "amount": "3000.00",
            },
            {
                "description": "Intelligent Document Processing (IDP) High-Volume Pack",
                "quantity": "1",
                "unit_price": "1200.00",
                "amount": "1200.00",
            },
            {
                "description": "Dedicated Solutions Engineering Onboarding (Hours)",
                "quantity": "6",
                "unit_price": "150.00",
                "amount": "900.00",
            },
        ],
        "subtotal_amount": "5100.00",
        "tax_label": "Sales Tax (10%)",
        "tax_amount": "510.00",
        "total_amount": "5610.00",
    },
    {
        "filename": "invoice_northern_ai_1089.png",
        "pdf_filename": "invoice_northern_ai_1089.pdf",
        "subfolder": "clean_invoices",
        "category": "Clean Invoices (100% 2-Way Match & STP)",
        "vendor_name": "Northern AI Robotics Ltd.",
        "vendor_address": "88 Queen Street, Ottawa, ON K1P 5E9",
        "vendor_email": "accounts@northernrobotics.ca | HST: 771029381RT0001",
        "invoice_number": "INV-2026-1089",
        "invoice_date": "2026-04-02",
        "due_date": "2026-05-02",
        "po_number": "PO-44210",
        "payment_terms": "Net 30",
        "currency": "CAD",
        "buyer_name": "Maple Leaf Manufacturing Inc.",
        "buyer_address": "250 Yonge Street, Floor 18, Toronto, ON M5B 2L7",
        "line_items": [
            {
                "description": "Optical Inspection Camera Unit Model X7",
                "quantity": "4",
                "unit_price": "850.00",
                "amount": "3400.00",
            },
            {
                "description": "Edge Inference Gateway Server Box",
                "quantity": "1",
                "unit_price": "2400.00",
                "amount": "2400.00",
            },
            {
                "description": "Annual Firmware Maintenance & Calibration Plan",
                "quantity": "1",
                "unit_price": "600.00",
                "amount": "600.00",
            },
        ],
        "subtotal_amount": "6400.00",
        "tax_label": "HST (13%)",
        "tax_amount": "832.00",
        "total_amount": "7232.00",
    },
    {
        "filename": "invoice_apex_cloud_9481.png",
        "pdf_filename": "invoice_apex_cloud_9481.pdf",
        "subfolder": "clean_invoices",
        "category": "Clean Invoices (100% 2-Way Match & STP)",
        "vendor_name": "Apex Cloud Infrastructure Inc.",
        "vendor_address": "77 King Street West, Suite 4100, Toronto, ON M5K 1H1",
        "vendor_email": "invoices@apexcloud.io | GST/HST: 849201944RT0002",
        "invoice_number": "INV-2026-9481",
        "invoice_date": "2026-10-21",
        "due_date": "2026-11-20",
        "po_number": "PO-2026-9481",
        "payment_terms": "Net 30",
        "currency": "USD",
        "buyer_name": "Alpha Global Systems Ltd.",
        "buyer_address": "600 Montgomery Street, San Francisco, CA 94111",
        "line_items": [
            {
                "description": "watsonx Enterprise AI Cluster Compute (Monthly)",
                "quantity": "2",
                "unit_price": "1800.00",
                "amount": "3600.00",
            },
            {
                "description": "High-Throughput Vector DB Storage (5TB Tier)",
                "quantity": "1",
                "unit_price": "950.00",
                "amount": "950.00",
            },
            {
                "description": "Premium SLA 24/7 Enterprise Support",
                "quantity": "1",
                "unit_price": "450.00",
                "amount": "450.00",
            },
        ],
        "subtotal_amount": "5000.00",
        "tax_label": "Tax (13%)",
        "tax_amount": "650.00",
        "total_amount": "5650.00",
    },
]

# 2. Variance Invoices (PO Exceptions & HITL)
VARIANCE_INVOICE_TEMPLATES = [
    {
        "filename": "invoice_pacific_cyber_2045.png",
        "pdf_filename": "invoice_pacific_cyber_2045.pdf",
        "subfolder": "variance_invoices",
        "category": "Variance Invoices (PO Exceptions & Review)",
        "vendor_name": "Pacific CyberSecurity Solutions Inc.",
        "vendor_address": "1055 West Georgia Street, Suite 2100, Vancouver, BC V6E 3P3",
        "vendor_email": "ar@pacificcyber.io | Tax Reg: 910-883-7721",
        "invoice_number": "INV-2026-2045",
        "invoice_date": "2026-10-20",
        "due_date": "2026-11-19",
        "po_number": "PO-77504",
        "payment_terms": "Net 30",
        "currency": "USD",
        "buyer_name": "Apex Financial Holdings Ltd.",
        "buyer_address": "400 Madison Avenue, Floor 12, New York, NY 10017",
        "line_items": [
            {
                "description": "Zero-Trust Network Intrusion Detection Appliance",
                "quantity": "3",
                "unit_price": "2200.00",
                "amount": "6600.00",
            },
            {
                "description": "24/7 SOC Threat Hunting & Incident Response Retainer",
                "quantity": "1",
                "unit_price": "3500.00",
                "amount": "3500.00",
            },
            {
                "description": "Penetration Testing & Red Team Assessment (Days)",
                "quantity": "5",
                "unit_price": "800.00",
                "amount": "4000.00",
            },
            {
                "description": "Hardware Security Module (HSM) Key Vault License",
                "quantity": "2",
                "unit_price": "450.00",
                "amount": "900.00",
            },
        ],
        "subtotal_amount": "15000.00",
        "tax_label": "Sales Tax (8%)",
        "tax_amount": "1200.00",
        "total_amount": "16200.00",
    },
]

# 3. Purchase Orders (Authoritative PO Catalog)
PURCHASE_ORDER_TEMPLATES = [
    {
        "filename": "po_global_logistics_8812.png",
        "pdf_filename": "po_global_logistics_8812.pdf",
        "subfolder": "purchase_orders",
        "category": "Purchase Orders (Authoritative PO Catalog)",
        "po_number": "PO-2026-8812",
        "order_date": "2026-10-18",
        "delivery_date": "2026-11-05",
        "payment_terms": "Net 45",
        "currency": "USD",
        "buyer_name": "Global Logistics Corp.",
        "shipping_address": "100 Port Terminal Way, Dock 4, Newark, NJ 07114",
        "vendor_name": "Quantum Server Racks Inc.",
        "vendor_address": "7400 Industrial Pkwy, Austin, TX 78735",
        "line_items": [
            {
                "description": "42U Heavy-Duty Server Rack Cabinet with Cooling",
                "quantity": "5",
                "unit_price": "1800.00",
                "amount": "9000.00",
            },
            {
                "description": "Redundant Rack PDU Power Distribution Unit",
                "quantity": "10",
                "unit_price": "350.00",
                "amount": "3500.00",
            },
        ],
        "total_authorized_amount": "12500.00",
    },
    {
        "filename": "po_titan_hypercompute_7731.png",
        "pdf_filename": "po_titan_hypercompute_7731.pdf",
        "subfolder": "purchase_orders",
        "category": "Purchase Orders (Authoritative PO Catalog)",
        "po_number": "PO-2026-7731",
        "order_date": "2026-10-19",
        "delivery_date": "2026-11-15",
        "payment_terms": "Net 30",
        "currency": "USD",
        "buyer_name": "Alpha Global Systems Ltd.",
        "shipping_address": "100 Data Center Way, Santa Clara, CA 95054",
        "vendor_name": "Titan Hypercompute Systems LLC",
        "vendor_address": "2200 Innovation Drive, Austin, TX 78758",
        "line_items": [
            {
                "description": "Enterprise AI Compute Blade Server (Dual Xeon / 8x GPU)",
                "quantity": "1",
                "unit_price": "9800.00",
                "amount": "9800.00",
            },
            {
                "description": "100GbE QSFP28 Optical Network Transceiver Pack",
                "quantity": "4",
                "unit_price": "650.00",
                "amount": "2600.00",
            },
            {
                "description": "24/7 Mission-Critical Support & Hardware Warranty (1 Yr)",
                "quantity": "1",
                "unit_price": "2350.00",
                "amount": "2350.00",
            },
        ],
        "total_authorized_amount": "14750.00",
    },
    {
        "filename": "po_vertex_robotics_6022.png",
        "pdf_filename": "po_vertex_robotics_6022.pdf",
        "subfolder": "purchase_orders",
        "category": "Purchase Orders (Authoritative PO Catalog)",
        "po_number": "PO-2026-6022",
        "order_date": "2026-10-20",
        "delivery_date": "2026-11-10",
        "payment_terms": "Net 30",
        "currency": "USD",
        "buyer_name": "Maple Leaf Manufacturing Inc.",
        "shipping_address": "300 Assembly Line Blvd, Windsor, ON N9A 6J3",
        "vendor_name": "Precision Industrial Robotics Corp.",
        "vendor_address": "450 Automation Way, Detroit, MI 48202",
        "line_items": [
            {
                "description": "6-Axis Harmonic Servo Actuator Unit (Model HX-900)",
                "quantity": "2",
                "unit_price": "6800.00",
                "amount": "13600.00",
            },
            {
                "description": "Laser Vision Calibration Array & Optical Controller",
                "quantity": "1",
                "unit_price": "3200.00",
                "amount": "3200.00",
            },
            {
                "description": "On-Site Factory Commissioning & Safety Certification",
                "quantity": "1",
                "unit_price": "1650.00",
                "amount": "1650.00",
            },
        ],
        "total_authorized_amount": "18450.00",
    },
]

# 4. Expense Receipts (T&E Corporate Card)
RECEIPT_TEMPLATES = [
    {
        "filename": "receipt_cloud_summit_9041.png",
        "pdf_filename": "receipt_cloud_summit_9041.pdf",
        "subfolder": "receipts",
        "category": "Expense Receipts (T&E Corporate Card)",
        "receipt_number": "REC-2026-9041",
        "transaction_date": "2026-10-19",
        "merchant_name": "Metro Convention Tech Bar & Catering",
        "merchant_address": "255 Front Street West, Toronto, ON M5V 2W6",
        "buyer_name": "Enterprise AI Team (Corporate Card)",
        "payment_method": "Corporate Visa **** 4821",
        "currency": "CAD",
        "line_items": [
            {
                "description": "Executive Client Workshop Catering Package",
                "quantity": "1",
                "unit_price": "320.00",
                "amount": "320.00",
            },
            {
                "description": "Conference Room High-Speed AV & Adapter Kit",
                "quantity": "2",
                "unit_price": "65.00",
                "amount": "130.00",
            },
        ],
        "subtotal_amount": "450.00",
        "tax_amount": "58.50",
        "total_amount": "508.50",
    },
    {
        "filename": "receipt_bluefin_bistro_3319.png",
        "pdf_filename": "receipt_bluefin_bistro_3319.pdf",
        "subfolder": "receipts",
        "category": "Expense Receipts (T&E Corporate Card)",
        "receipt_number": "REC-2026-3319",
        "transaction_date": "2026-10-20",
        "merchant_name": "Bluefin Bistro & Oyster Bar",
        "merchant_address": "120 Harbourfront Street, Vancouver, BC V6B 2P9",
        "buyer_name": "David Miller (Director)",
        "payment_method": "Corporate Amex **** 1009",
        "currency": "USD",
        "line_items": [
            {
                "description": "Executive Client Dinner & Wine Pairing (4 Guests)",
                "quantity": "1",
                "unit_price": "385.00",
                "amount": "385.00",
            },
            {
                "description": "Service Gratuity (18%)",
                "quantity": "1",
                "unit_price": "69.30",
                "amount": "69.30",
            },
        ],
        "subtotal_amount": "454.30",
        "tax_amount": "36.34",
        "total_amount": "490.64",
    },
    {
        "filename": "receipt_summit_catering_5510.png",
        "pdf_filename": "receipt_summit_catering_5510.pdf",
        "subfolder": "receipts",
        "category": "Expense Receipts (T&E Corporate Card)",
        "receipt_number": "REC-2026-5510",
        "transaction_date": "2026-10-21",
        "merchant_name": "Summit Catering & Hospitality Group",
        "merchant_address": "400 University Ave, Toronto, ON M5G 1S5",
        "buyer_name": "Q4 AP Strategy Workshop",
        "payment_method": "Corporate Mastercard **** 7732",
        "currency": "USD",
        "line_items": [
            {
                "description": "All-Day Corporate Executive Hospitality & Lunch Buffet",
                "quantity": "1",
                "unit_price": "620.00",
                "amount": "620.00",
            },
            {
                "description": "Beverage & Espresso Service Package",
                "quantity": "1",
                "unit_price": "140.00",
                "amount": "140.00",
            },
        ],
        "subtotal_amount": "760.00",
        "tax_amount": "76.00",
        "total_amount": "836.00",
    },
]


def _load_font(size: int, bold: bool = False):
    candidates = (
        [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        if bold
        else [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    )
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_invoice(template: dict) -> tuple[Path, Path]:
    target_dir = SUBFOLDERS.get(template.get("subfolder", "clean_invoices"), SAMPLES_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)
    width, height = 1240, 1600
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_title = _load_font(44, bold=True)
    font_h2 = _load_font(26, bold=True)
    font_bold = _load_font(22, bold=True)
    font_reg = _load_font(21, bold=False)
    font_small = _load_font(18, bold=False)

    # Accent color: Deep Blue for standard, Amber/Red tint for variance
    is_variance = template.get("subfolder") == "variance_invoices"
    accent_color = (218, 30, 40) if is_variance else (15, 98, 254)

    draw.rectangle([(0, 0), (width, 18)], fill=accent_color)
    draw.text((80, 65), template["vendor_name"], fill=(15, 23, 42), font=font_h2)
    draw.text((80, 102), template["vendor_address"], fill=(71, 85, 105), font=font_reg)
    draw.text((80, 134), template["vendor_email"], fill=(100, 116, 139), font=font_small)

    title_text = "INVOICE [VARIANCE]" if is_variance else "INVOICE"
    draw.text((820 if is_variance else 900, 60), title_text, fill=accent_color, font=font_title)

    draw.line([(80, 190), (width - 80, 190)], fill=(203, 213, 225), width=2)
    draw.text((80, 220), "BILL TO:", fill=accent_color, font=font_bold)
    draw.text((80, 255), template["buyer_name"], fill=(15, 23, 42), font=font_bold)
    draw.text((80, 288), template["buyer_address"], fill=(51, 65, 85), font=font_reg)

    meta_x = 700
    meta_y = 220
    meta_rows = [
        ("Invoice Number:", template["invoice_number"]),
        ("Invoice Date:", template["invoice_date"]),
        ("Due Date:", template["due_date"]),
        ("PO Number:", template["po_number"]),
        ("Payment Terms:", template["payment_terms"]),
        ("Currency:", template["currency"]),
    ]
    for idx, (label, val) in enumerate(meta_rows):
        row_y = meta_y + idx * 34
        draw.text((meta_x, row_y), label, fill=(71, 85, 105), font=font_bold)
        draw.text((meta_x + 210, row_y), val, fill=(15, 23, 42), font=font_reg)

    table_top = 465
    draw.rectangle([(80, table_top), (width - 80, table_top + 52)], fill=(241, 245, 249))
    draw.line([(80, table_top), (width - 80, table_top)], fill=(148, 163, 184), width=2)
    draw.line([(80, table_top + 52), (width - 80, table_top + 52)], fill=(148, 163, 184), width=2)

    col_desc, col_qty, col_unit, col_amt = 100, 740, 870, 1030
    draw.text((col_desc, table_top + 14), "Description", fill=(15, 23, 42), font=font_bold)
    draw.text((col_qty, table_top + 14), "Quantity", fill=(15, 23, 42), font=font_bold)
    draw.text((col_unit, table_top + 14), "Unit Price", fill=(15, 23, 42), font=font_bold)
    draw.text((col_amt, table_top + 14), "Amount", fill=(15, 23, 42), font=font_bold)

    row_y = table_top + 68
    for item in template["line_items"]:
        draw.text((col_desc, row_y), item["description"], fill=(30, 41, 59), font=font_reg)
        draw.text((col_qty, row_y), item["quantity"], fill=(30, 41, 59), font=font_reg)
        draw.text((col_unit, row_y), f"{item['unit_price']}", fill=(30, 41, 59), font=font_reg)
        draw.text((col_amt, row_y), f"{item['amount']}", fill=(15, 23, 42), font=font_bold)
        row_y += 58
        draw.line([(80, row_y - 14), (width - 80, row_y - 14)], fill=(226, 232, 240), width=1)

    totals_y = row_y + 30
    totals_x_label, totals_x_val = 760, 1015

    draw.text((totals_x_label, totals_y), "Subtotal:", fill=(71, 85, 105), font=font_bold)
    draw.text((totals_x_val, totals_y), f"{template['currency']} {template['subtotal_amount']}", fill=(15, 23, 42), font=font_reg)
    draw.text((totals_x_label, totals_y + 42), f"{template['tax_label']}:", fill=(71, 85, 105), font=font_bold)
    draw.text((totals_x_val, totals_y + 42), f"{template['currency']} {template['tax_amount']}", fill=(15, 23, 42), font=font_reg)

    draw.rectangle([(totals_x_label - 20, totals_y + 88), (width - 80, totals_y + 148)], fill=(254, 242, 242) if is_variance else (239, 246, 255), outline=accent_color, width=2)
    draw.text((totals_x_label, totals_y + 104), "Total Amount:", fill=accent_color, font=font_h2)
    draw.text((totals_x_val - 15, totals_y + 104), f"{template['currency']} {template['total_amount']}", fill=accent_color, font=font_h2)

    footer_y = totals_y + 210
    draw.line([(80, footer_y), (width - 80, footer_y)], fill=(203, 213, 225), width=1)
    draw.text((80, footer_y + 24), f"Payment Instructions: Remit within {template['payment_terms']} referencing {template['invoice_number']} and PO {template['po_number']}.", fill=(100, 116, 139), font=font_small)

    png_path = target_dir / template["filename"]
    pdf_path = target_dir / template["pdf_filename"]
    img.save(png_path, format="PNG")
    img.save(pdf_path, format="PDF", resolution=150.0)
    return png_path, pdf_path


def render_purchase_order(template: dict) -> tuple[Path, Path]:
    target_dir = SUBFOLDERS["purchase_orders"]
    target_dir.mkdir(parents=True, exist_ok=True)
    width, height = 1240, 1500
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_title = _load_font(42, bold=True)
    font_h2 = _load_font(26, bold=True)
    font_bold = _load_font(22, bold=True)
    font_reg = _load_font(21, bold=False)
    font_small = _load_font(18, bold=False)

    accent_color = (0, 125, 121)  # Teal for Purchase Orders

    draw.rectangle([(0, 0), (width, 18)], fill=accent_color)
    draw.text((80, 65), template["buyer_name"], fill=(15, 23, 42), font=font_h2)
    draw.text((80, 102), f"Ship To: {template['shipping_address']}", fill=(71, 85, 105), font=font_reg)
    draw.text((730, 60), "PURCHASE ORDER", fill=accent_color, font=font_title)

    draw.line([(80, 175), (width - 80, 175)], fill=(203, 213, 225), width=2)
    draw.text((80, 205), "VENDOR / SUPPLIER:", fill=accent_color, font=font_bold)
    draw.text((80, 240), template["vendor_name"], fill=(15, 23, 42), font=font_bold)
    draw.text((80, 273), template["vendor_address"], fill=(51, 65, 85), font=font_reg)

    meta_x, meta_y = 700, 205
    meta_rows = [
        ("PO Number:", template["po_number"]),
        ("Order Date:", template["order_date"]),
        ("Delivery Date:", template["delivery_date"]),
        ("Payment Terms:", template["payment_terms"]),
        ("Currency:", template["currency"]),
    ]
    for idx, (label, val) in enumerate(meta_rows):
        row_y = meta_y + idx * 34
        draw.text((meta_x, row_y), label, fill=(71, 85, 105), font=font_bold)
        draw.text((meta_x + 210, row_y), val, fill=(15, 23, 42), font=font_reg)

    table_top = 425
    draw.rectangle([(80, table_top), (width - 80, table_top + 52)], fill=(240, 253, 250))
    draw.line([(80, table_top), (width - 80, table_top)], fill=(148, 163, 184), width=2)
    draw.line([(80, table_top + 52), (width - 80, table_top + 52)], fill=(148, 163, 184), width=2)

    col_desc, col_qty, col_unit, col_amt = 100, 740, 870, 1030
    draw.text((col_desc, table_top + 14), "Item Description", fill=(15, 23, 42), font=font_bold)
    draw.text((col_qty, table_top + 14), "Quantity", fill=(15, 23, 42), font=font_bold)
    draw.text((col_unit, table_top + 14), "Unit Price", fill=(15, 23, 42), font=font_bold)
    draw.text((col_amt, table_top + 14), "Amount", fill=(15, 23, 42), font=font_bold)

    row_y = table_top + 68
    for item in template["line_items"]:
        draw.text((col_desc, row_y), item["description"], fill=(30, 41, 59), font=font_reg)
        draw.text((col_qty, row_y), item["quantity"], fill=(30, 41, 59), font=font_reg)
        draw.text((col_unit, row_y), item["unit_price"], fill=(30, 41, 59), font=font_reg)
        draw.text((col_amt, row_y), item["amount"], fill=(15, 23, 42), font=font_bold)
        row_y += 58
        draw.line([(80, row_y - 14), (width - 80, row_y - 14)], fill=(226, 232, 240), width=1)

    totals_y = row_y + 30
    draw.rectangle([(700, totals_y + 20), (width - 80, totals_y + 84)], fill=(240, 253, 250), outline=accent_color, width=2)
    draw.text((720, totals_y + 38), "Total Authorized Amount:", fill=accent_color, font=font_bold)
    draw.text((1010, totals_y + 36), f"{template['currency']} {template['total_authorized_amount']}", fill=accent_color, font=font_h2)

    draw.text((80, totals_y + 140), f"Authorized Purchase Order {template['po_number']} — Reference on all invoices and shipping manifests.", fill=(100, 116, 139), font=font_small)

    png_path = target_dir / template["filename"]
    pdf_path = target_dir / template["pdf_filename"]
    img.save(png_path, format="PNG")
    img.save(pdf_path, format="PDF", resolution=150.0)
    return png_path, pdf_path


def render_receipt(template: dict) -> tuple[Path, Path]:
    target_dir = SUBFOLDERS["receipts"]
    target_dir.mkdir(parents=True, exist_ok=True)
    width, height = 900, 1250
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_title = _load_font(36, bold=True)
    font_h2 = _load_font(24, bold=True)
    font_bold = _load_font(20, bold=True)
    font_reg = _load_font(20, bold=False)

    accent_color = (138, 63, 252)  # Purple for Receipts

    draw.rectangle([(0, 0), (width, 16)], fill=accent_color)
    draw.text((80, 55), "PAYMENT RECEIPT", fill=accent_color, font=font_title)
    draw.text((80, 110), f"Merchant: {template['merchant_name']}", fill=(15, 23, 42), font=font_h2)
    draw.text((80, 145), f"Address: {template['merchant_address']}", fill=(71, 85, 105), font=font_reg)

    draw.line([(80, 195), (width - 80, 195)], fill=(203, 213, 225), width=2)

    meta_rows = [
        ("Receipt Number:", template["receipt_number"]),
        ("Transaction Date:", template["transaction_date"]),
        ("Customer / Paid By:", template["buyer_name"]),
        ("Payment Method:", template["payment_method"]),
        ("Currency:", template["currency"]),
    ]
    for idx, (label, val) in enumerate(meta_rows):
        y = 220 + idx * 34
        draw.text((80, y), label, fill=(71, 85, 105), font=font_bold)
        draw.text((330, y), val, fill=(15, 23, 42), font=font_reg)

    table_top = 420
    draw.rectangle([(80, table_top), (width - 80, table_top + 46)], fill=(243, 232, 255))
    draw.text((100, table_top + 12), "Description", fill=(15, 23, 42), font=font_bold)
    draw.text((540, table_top + 12), "Qty", fill=(15, 23, 42), font=font_bold)
    draw.text((620, table_top + 12), "Unit", fill=(15, 23, 42), font=font_bold)
    draw.text((720, table_top + 12), "Amount", fill=(15, 23, 42), font=font_bold)

    row_y = table_top + 62
    for item in template["line_items"]:
        draw.text((100, row_y), item["description"], fill=(30, 41, 59), font=font_reg)
        draw.text((540, row_y), item["quantity"], fill=(30, 41, 59), font=font_reg)
        draw.text((620, row_y), item["unit_price"], fill=(30, 41, 59), font=font_reg)
        draw.text((720, row_y), item["amount"], fill=(15, 23, 42), font=font_bold)
        row_y += 50
        draw.line([(80, row_y - 10), (width - 80, row_y - 10)], fill=(226, 232, 240), width=1)

    totals_y = row_y + 25
    draw.text((500, totals_y), "Subtotal:", fill=(71, 85, 105), font=font_bold)
    draw.text((690, totals_y), f"{template['currency']} {template['subtotal_amount']}", fill=(15, 23, 42), font=font_reg)
    draw.text((500, totals_y + 38), "Tax Amount:", fill=(71, 85, 105), font=font_bold)
    draw.text((690, totals_y + 38), f"{template['currency']} {template['tax_amount']}", fill=(15, 23, 42), font=font_reg)

    draw.rectangle([(480, totals_y + 82), (width - 80, totals_y + 136)], fill=(243, 232, 255), outline=accent_color, width=2)
    draw.text((500, totals_y + 96), "Total Paid:", fill=accent_color, font=font_h2)
    draw.text((680, totals_y + 96), f"{template['currency']} {template['total_amount']}", fill=accent_color, font=font_h2)

    png_path = target_dir / template["filename"]
    pdf_path = target_dir / template["pdf_filename"]
    img.save(png_path, format="PNG")
    img.save(pdf_path, format="PDF", resolution=150.0)
    return png_path, pdf_path


def generate_all_samples() -> list[dict]:
    for sub in SUBFOLDERS.values():
        sub.mkdir(parents=True, exist_ok=True)

    created = []

    # 1. Clean Invoices
    for tpl in CLEAN_INVOICE_TEMPLATES:
        png_path, pdf_path = render_invoice(tpl)
        sub = tpl["subfolder"]
        created.append(
            {
                "doc_type": "Invoice",
                "category": tpl["category"],
                "subfolder": sub,
                "invoice_number": tpl["invoice_number"],
                "vendor_name": tpl["vendor_name"],
                "total_amount": tpl["total_amount"],
                "currency": tpl["currency"],
                "png_path": str(png_path),
                "pdf_path": str(pdf_path),
                "png_filename": f"{sub}/{png_path.name}",
                "pdf_filename": f"{sub}/{pdf_path.name}",
                "raw_filename": png_path.name,
            }
        )

    # 2. Variance Invoices
    for tpl in VARIANCE_INVOICE_TEMPLATES:
        png_path, pdf_path = render_invoice(tpl)
        sub = tpl["subfolder"]
        created.append(
            {
                "doc_type": "Invoice",
                "category": tpl["category"],
                "subfolder": sub,
                "invoice_number": tpl["invoice_number"],
                "vendor_name": tpl["vendor_name"],
                "total_amount": tpl["total_amount"],
                "currency": tpl["currency"],
                "png_path": str(png_path),
                "pdf_path": str(pdf_path),
                "png_filename": f"{sub}/{png_path.name}",
                "pdf_filename": f"{sub}/{pdf_path.name}",
                "raw_filename": png_path.name,
            }
        )

    # 3. Purchase Orders
    for tpl in PURCHASE_ORDER_TEMPLATES:
        png_path, pdf_path = render_purchase_order(tpl)
        sub = tpl["subfolder"]
        created.append(
            {
                "doc_type": "PurchaseOrder",
                "category": tpl["category"],
                "subfolder": sub,
                "invoice_number": tpl["po_number"],
                "vendor_name": tpl["vendor_name"],
                "total_amount": tpl["total_authorized_amount"],
                "currency": tpl["currency"],
                "png_path": str(png_path),
                "pdf_path": str(pdf_path),
                "png_filename": f"{sub}/{png_path.name}",
                "pdf_filename": f"{sub}/{pdf_path.name}",
                "raw_filename": png_path.name,
            }
        )

    # 4. Receipts
    for tpl in RECEIPT_TEMPLATES:
        png_path, pdf_path = render_receipt(tpl)
        sub = tpl["subfolder"]
        created.append(
            {
                "doc_type": "Receipt",
                "category": tpl["category"],
                "subfolder": sub,
                "invoice_number": tpl["receipt_number"],
                "vendor_name": tpl["merchant_name"],
                "total_amount": tpl["total_amount"],
                "currency": tpl["currency"],
                "png_path": str(png_path),
                "pdf_path": str(pdf_path),
                "png_filename": f"{sub}/{png_path.name}",
                "pdf_filename": f"{sub}/{pdf_path.name}",
                "raw_filename": png_path.name,
            }
        )

    return created


if __name__ == "__main__":
    results = generate_all_samples()
    for r in results:
        print(f"[{r['subfolder']}] Generated: {r['png_path']}")
