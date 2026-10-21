"""
Generate high-resolution sample invoice PNG and PDF documents for testing the
watsonx Orchestrate IDP (docproc) pipeline.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"

INVOICE_TEMPLATES = [
    {
        "filename": "invoice_acme_cloud_0042.png",
        "pdf_filename": "invoice_acme_cloud_0042.pdf",
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
        "filename": "invoice_pacific_cyber_2045.png",
        "pdf_filename": "invoice_pacific_cyber_2045.pdf",
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


def render_invoice(template: dict, output_dir: Path = SAMPLES_DIR) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    width, height = 1240, 1600
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_title = _load_font(44, bold=True)
    font_h2 = _load_font(26, bold=True)
    font_bold = _load_font(22, bold=True)
    font_reg = _load_font(21, bold=False)
    font_small = _load_font(18, bold=False)

    # Top header bar
    draw.rectangle([(0, 0), (width, 18)], fill=(15, 98, 254))

    # Vendor block (top-left)
    draw.text((80, 65), template["vendor_name"], fill=(15, 23, 42), font=font_h2)
    draw.text((80, 102), template["vendor_address"], fill=(71, 85, 105), font=font_reg)
    draw.text((80, 134), template["vendor_email"], fill=(100, 116, 139), font=font_small)

    # INVOICE title (top-right)
    draw.text((900, 60), "INVOICE", fill=(15, 98, 254), font=font_title)

    # Divider
    draw.line([(80, 190), (width - 80, 190)], fill=(203, 213, 225), width=2)

    # Bill To section (left)
    draw.text((80, 220), "BILL TO:", fill=(15, 98, 254), font=font_bold)
    draw.text((80, 255), template["buyer_name"], fill=(15, 23, 42), font=font_bold)
    draw.text((80, 288), template["buyer_address"], fill=(51, 65, 85), font=font_reg)

    # Invoice Metadata box (right)
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

    # Line items table header
    table_top = 465
    draw.rectangle([(80, table_top), (width - 80, table_top + 52)], fill=(241, 245, 249))
    draw.line([(80, table_top), (width - 80, table_top)], fill=(148, 163, 184), width=2)
    draw.line([(80, table_top + 52), (width - 80, table_top + 52)], fill=(148, 163, 184), width=2)

    col_desc = 100
    col_qty = 740
    col_unit = 870
    col_amt = 1030

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

    # Totals block
    totals_y = row_y + 30
    totals_x_label = 760
    totals_x_val = 1015

    draw.text((totals_x_label, totals_y), "Subtotal:", fill=(71, 85, 105), font=font_bold)
    draw.text(
        (totals_x_val, totals_y),
        f"{template['currency']} {template['subtotal_amount']}",
        fill=(15, 23, 42),
        font=font_reg,
    )

    draw.text((totals_x_label, totals_y + 42), f"{template['tax_label']}:", fill=(71, 85, 105), font=font_bold)
    draw.text(
        (totals_x_val, totals_y + 42),
        f"{template['currency']} {template['tax_amount']}",
        fill=(15, 23, 42),
        font=font_reg,
    )

    draw.rectangle(
        [(totals_x_label - 20, totals_y + 88), (width - 80, totals_y + 148)],
        fill=(239, 246, 255),
        outline=(15, 98, 254),
        width=2,
    )
    draw.text((totals_x_label, totals_y + 104), "Total Amount:", fill=(15, 98, 254), font=font_h2)
    draw.text(
        (totals_x_val - 15, totals_y + 104),
        f"{template['currency']} {template['total_amount']}",
        fill=(15, 98, 254),
        font=font_h2,
    )

    # Footer payment instructions
    footer_y = totals_y + 210
    draw.line([(80, footer_y), (width - 80, footer_y)], fill=(203, 213, 225), width=1)
    draw.text(
        (80, footer_y + 24),
        f"Payment Instructions: Please remit payment within {template['payment_terms']} referencing Invoice {template['invoice_number']} and PO {template['po_number']}.",
        fill=(100, 116, 139),
        font=font_small,
    )

    png_path = output_dir / template["filename"]
    pdf_path = output_dir / template["pdf_filename"]
    img.save(png_path, format="PNG")
    img.save(pdf_path, format="PDF", resolution=150.0)
    return png_path, pdf_path


def render_purchase_order(template: dict, output_dir: Path = SAMPLES_DIR) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    width, height = 1240, 1500
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_title = _load_font(42, bold=True)
    font_h2 = _load_font(26, bold=True)
    font_bold = _load_font(22, bold=True)
    font_reg = _load_font(21, bold=False)
    font_small = _load_font(18, bold=False)

    # Top header bar (Teal for Purchase Orders)
    draw.rectangle([(0, 0), (width, 18)], fill=(0, 125, 121))

    # Buyer issuing PO (top-left)
    draw.text((80, 65), template["buyer_name"], fill=(15, 23, 42), font=font_h2)
    draw.text((80, 102), f"Ship To: {template['shipping_address']}", fill=(71, 85, 105), font=font_reg)

    # PURCHASE ORDER title (top-right)
    draw.text((730, 60), "PURCHASE ORDER", fill=(0, 125, 121), font=font_title)

    draw.line([(80, 175), (width - 80, 175)], fill=(203, 213, 225), width=2)

    # Vendor block (left)
    draw.text((80, 205), "VENDOR / SUPPLIER:", fill=(0, 125, 121), font=font_bold)
    draw.text((80, 240), template["vendor_name"], fill=(15, 23, 42), font=font_bold)
    draw.text((80, 273), template["vendor_address"], fill=(51, 65, 85), font=font_reg)

    # PO Metadata (right)
    meta_x = 700
    meta_y = 205
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

    # Table header
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
    draw.rectangle(
        [(700, totals_y + 20), (width - 80, totals_y + 84)],
        fill=(240, 253, 250),
        outline=(0, 125, 121),
        width=2,
    )
    draw.text((720, totals_y + 38), "Total Authorized Amount:", fill=(0, 125, 121), font=font_bold)
    draw.text(
        (1010, totals_y + 36),
        f"{template['currency']} {template['total_authorized_amount']}",
        fill=(0, 125, 121),
        font=font_h2,
    )

    draw.text(
        (80, totals_y + 140),
        f"Authorized Purchase Order {template['po_number']} — Please reference this PO on all invoices and shipping manifests.",
        fill=(100, 116, 139),
        font=font_small,
    )

    png_path = output_dir / template["filename"]
    pdf_path = output_dir / template["pdf_filename"]
    img.save(png_path, format="PNG")
    img.save(pdf_path, format="PDF", resolution=150.0)
    return png_path, pdf_path


def render_receipt(template: dict, output_dir: Path = SAMPLES_DIR) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    width, height = 900, 1250
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_title = _load_font(36, bold=True)
    font_h2 = _load_font(24, bold=True)
    font_bold = _load_font(20, bold=True)
    font_reg = _load_font(20, bold=False)

    draw.rectangle([(0, 0), (width, 16)], fill=(138, 63, 252))
    draw.text((80, 55), "PAYMENT RECEIPT", fill=(138, 63, 252), font=font_title)
    draw.text((80, 110), f"Merchant Name: {template['merchant_name']}", fill=(15, 23, 42), font=font_h2)
    draw.text((80, 145), f"Merchant Address: {template['merchant_address']}", fill=(71, 85, 105), font=font_reg)

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

    draw.rectangle([(480, totals_y + 82), (width - 80, totals_y + 136)], fill=(243, 232, 255), outline=(138, 63, 252), width=2)
    draw.text((500, totals_y + 96), "Total Paid:", fill=(138, 63, 252), font=font_h2)
    draw.text((680, totals_y + 96), f"{template['currency']} {template['total_amount']}", fill=(138, 63, 252), font=font_h2)

    png_path = output_dir / template["filename"]
    pdf_path = output_dir / template["pdf_filename"]
    img.save(png_path, format="PNG")
    img.save(pdf_path, format="PDF", resolution=150.0)
    return png_path, pdf_path


PO_TEMPLATES = [
    {
        "filename": "po_global_logistics_8812.png",
        "pdf_filename": "po_global_logistics_8812.pdf",
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
    }
]

RECEIPT_TEMPLATES = [
    {
        "filename": "receipt_cloud_summit_9041.png",
        "pdf_filename": "receipt_cloud_summit_9041.pdf",
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
    }
]


def generate_all_samples() -> list[dict]:
    created = []
    for tpl in INVOICE_TEMPLATES:
        png_path, pdf_path = render_invoice(tpl)
        created.append(
            {
                "doc_type": "Invoice",
                "invoice_number": tpl["invoice_number"],
                "vendor_name": tpl["vendor_name"],
                "total_amount": tpl["total_amount"],
                "currency": tpl["currency"],
                "png_path": str(png_path),
                "pdf_path": str(pdf_path),
                "png_filename": png_path.name,
                "pdf_filename": pdf_path.name,
            }
        )
    for tpl in PO_TEMPLATES:
        png_path, pdf_path = render_purchase_order(tpl)
        created.append(
            {
                "doc_type": "PurchaseOrder",
                "invoice_number": tpl["po_number"],
                "vendor_name": tpl["vendor_name"],
                "total_amount": tpl["total_authorized_amount"],
                "currency": tpl["currency"],
                "png_path": str(png_path),
                "pdf_path": str(pdf_path),
                "png_filename": png_path.name,
                "pdf_filename": pdf_path.name,
            }
        )
    for tpl in RECEIPT_TEMPLATES:
        png_path, pdf_path = render_receipt(tpl)
        created.append(
            {
                "doc_type": "Receipt",
                "invoice_number": tpl["receipt_number"],
                "vendor_name": tpl["merchant_name"],
                "total_amount": tpl["total_amount"],
                "currency": tpl["currency"],
                "png_path": str(png_path),
                "pdf_path": str(pdf_path),
                "png_filename": png_path.name,
                "pdf_filename": pdf_path.name,
            }
        )
    return created


if __name__ == "__main__":
    results = generate_all_samples()
    for r in results:
        print(f"Generated: {r['png_path']} and {r['pdf_path']}")
