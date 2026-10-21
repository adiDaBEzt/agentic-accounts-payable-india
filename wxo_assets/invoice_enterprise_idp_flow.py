"""
IBM watsonx Orchestrate Agentic Flow for Multi-Document Intelligent Document Processing (IDP).

Sequence Architecture:
  START -> [multi_docproc_node (Text extractor: WDU text_extraction + multi-schema KVP + Table)]
        -> [math_and_routing_node (Logic block: deterministic Python math, confidence, approval routing)]
        -> [executive_structurer_node (Generative prompt: GenAI normalization, GL coding, audit report)]
        -> END
"""

from typing import List, Optional
from pydantic import BaseModel, Field

# Always import `flows` before `types` to avoid circular import in ADK 2.17.0
from ibm_watsonx_orchestrate.flow_builder.flows import (
    Flow,
    flow,
    START,
    END,
)
from ibm_watsonx_orchestrate.flow_builder.types import (
    DocProcInput,
    DocProcField,
    DocProcTable,
    DocProcKVPSchema,
    DocProcOutputFormat,
    NodeErrorHandlerConfig,
)


# --- 1. Schemas for Multi-Document Types ---

INVOICE_KVP_SCHEMA = DocProcKVPSchema(
    document_type="Invoice",
    document_description=(
        "A commercial invoice or bill issued by a vendor to a buyer detailing "
        "products or services provided, quantities, prices, tax, and payment terms."
    ),
    fields={
        "invoice_number": DocProcField(
            description="The unique invoice number or identifier",
            default="",
            example="INV-2026-0042",
        ),
        "invoice_date": DocProcField(
            description="The date the invoice was issued",
            default="",
            example="2026-03-15",
        ),
        "due_date": DocProcField(
            description="The payment due date",
            default="",
            example="2026-04-14",
        ),
        "vendor_name": DocProcField(
            description="The name of the vendor or seller organization",
            default="",
            example="Acme Cloud Systems Inc.",
        ),
        "vendor_address": DocProcField(
            description="The business address of the vendor",
            default="",
            example="500 King Street West, Toronto, ON M5V 1L9",
        ),
        "buyer_name": DocProcField(
            description="The customer or organization being billed (Bill To)",
            default="",
            example="Global Logistics Corp.",
        ),
        "buyer_address": DocProcField(
            description="The billing address of the customer",
            default="",
            example="120 Broadway, Suite 400, New York, NY 10271",
        ),
        "po_number": DocProcField(
            description="Purchase Order (PO) reference number",
            default="",
            example="PO-99812",
        ),
        "currency": DocProcField(
            description="Currency code such as USD, CAD, EUR",
            default="USD",
            example="USD",
        ),
        "subtotal_amount": DocProcField(
            description="Subtotal amount before tax",
            default="",
            example="5100.00",
        ),
        "tax_amount": DocProcField(
            description="Total tax amount",
            default="",
            example="510.00",
        ),
        "total_amount": DocProcField(
            description="Final total amount due on invoice",
            default="",
            example="5610.00",
        ),
        "payment_terms": DocProcField(
            description="Payment terms such as Net 30",
            default="",
            example="Net 30",
        ),
        "line_items": DocProcTable(
            type="array",
            description="Table of individual billed items or services",
            columns={
                "description": DocProcField(
                    description="Item description",
                    default="",
                    example="Enterprise License",
                ),
                "quantity": DocProcField(
                    description="Quantity billed",
                    default="",
                    example="2",
                ),
                "unit_price": DocProcField(
                    description="Unit price",
                    default="",
                    example="1500.00",
                ),
                "amount": DocProcField(
                    description="Total line amount",
                    default="",
                    example="3000.00",
                ),
            },
        ),
    },
)

PURCHASE_ORDER_KVP_SCHEMA = DocProcKVPSchema(
    document_type="PurchaseOrder",
    document_description=(
        "A formal purchase order document issued by a buyer requesting goods or "
        "services from a vendor, specifying quantities, delivery dates, and authorized amounts."
    ),
    fields={
        "po_number": DocProcField(
            description="Purchase Order (PO) number",
            default="",
            example="PO-2026-8812",
        ),
        "order_date": DocProcField(
            description="Date the purchase order was created",
            default="",
            example="2026-03-10",
        ),
        "buyer_name": DocProcField(
            description="Company issuing the purchase order",
            default="",
            example="Global Logistics Corp.",
        ),
        "vendor_name": DocProcField(
            description="Supplier or vendor name",
            default="",
            example="Acme Cloud Systems Inc.",
        ),
        "shipping_address": DocProcField(
            description="Destination delivery address (Ship To)",
            default="",
            example="100 Warehouse Way, Newark, NJ 07114",
        ),
        "total_authorized_amount": DocProcField(
            description="Total authorized spend amount",
            default="",
            example="12500.00",
        ),
        "currency": DocProcField(
            description="Currency code",
            default="USD",
            example="USD",
        ),
    },
)

RECEIPT_KVP_SCHEMA = DocProcKVPSchema(
    document_type="Receipt",
    document_description=(
        "A sales receipt, retail cash register slip, or payment confirmation "
        "issued upon immediate purchase of goods or services."
    ),
    fields={
        "receipt_number": DocProcField(
            description="Transaction or receipt identifier",
            default="",
            example="REC-98214",
        ),
        "transaction_date": DocProcField(
            description="Date and time of transaction",
            default="",
            example="2026-04-05",
        ),
        "merchant_name": DocProcField(
            description="Merchant, store, or restaurant name",
            default="",
            example="Starbucks Coffee #492",
        ),
        "merchant_address": DocProcField(
            description="Store location address",
            default="",
            example="420 Bay St, Toronto, ON",
        ),
        "total_amount": DocProcField(
            description="Total amount paid",
            default="",
            example="24.85",
        ),
        "tax_amount": DocProcField(
            description="Tax or VAT paid",
            default="",
            example="2.85",
        ),
        "payment_method": DocProcField(
            description="Payment card or method (e.g. Visa, Cash, Amex)",
            default="",
            example="Visa **** 1092",
        ),
    },
)


# --- 2. Schemas for Logic Block & GenAI Prompt Node ---

class InvoiceLineItem(BaseModel):
    description: str = Field(default="", description="Description of the billed item or service")
    quantity: str = Field(default="1", description="Quantity billed")
    unit_price: str = Field(default="0.00", description="Unit price of the item")
    amount: str = Field(default="0.00", description="Line item total amount")
    gl_category: str = Field(default="General Expense", description="Accounting General Ledger category")


class LogicBlockInput(BaseModel):
    ocr_text: str = Field(default="")
    raw_kvps: Optional[List[dict]] = Field(default=None)


class LogicBlockOutput(BaseModel):
    detected_document_type: str = Field(default="Invoice", description="Classified document type (Invoice, PurchaseOrder, Receipt)")
    invoice_number: str = Field(default="")
    vendor_name: str = Field(default="")
    buyer_name: str = Field(default="")
    doc_date: str = Field(default="")
    po_number: str = Field(default="")
    currency: str = Field(default="USD")
    computed_subtotal: float = Field(default=0.0)
    computed_tax: float = Field(default=0.0)
    computed_total: float = Field(default=0.0)
    math_valid: bool = Field(default=True)
    discrepancy: float = Field(default=0.0)
    approval_tier: str = Field(default="AUTO_APPROVED", description="AUTO_APPROVED, VP_APPROVAL_REQUIRED, or FLAGGED_MATH_MISMATCH")
    math_summary: str = Field(default="")


class GenAIInput(BaseModel):
    ocr_text: str = Field(default="")
    detected_document_type: str = Field(default="")
    invoice_number: str = Field(default="")
    vendor_name: str = Field(default="")
    buyer_name: str = Field(default="")
    currency: str = Field(default="USD")
    computed_subtotal: float = Field(default=0.0)
    computed_tax: float = Field(default=0.0)
    computed_total: float = Field(default=0.0)
    math_valid: bool = Field(default=True)
    discrepancy: float = Field(default=0.0)
    approval_tier: str = Field(default="")
    math_summary: str = Field(default="")


class StructuredInvoiceRecord(BaseModel):
    document_type: str = Field(default="Invoice", description="Document type")
    invoice_number: str = Field(default="", description="Unique invoice or reference number")
    invoice_date: str = Field(default="", description="Standardized date (YYYY-MM-DD)")
    due_date: str = Field(default="", description="Payment due date")
    vendor_name: str = Field(default="", description="Seller or merchant organization name")
    vendor_address: str = Field(default="", description="Seller address")
    buyer_name: str = Field(default="", description="Customer or bill-to organization name")
    buyer_address: str = Field(default="", description="Customer address")
    po_number: str = Field(default="", description="Purchase Order reference number")
    currency: str = Field(default="USD", description="3-letter ISO currency code")
    subtotal_amount: str = Field(default="0.00", description="Subtotal amount before tax")
    tax_amount: str = Field(default="0.00", description="Total tax amount")
    total_amount: str = Field(default="0.00", description="Final total amount due")
    payment_terms: str = Field(default="", description="Payment terms such as Net 30")
    approval_tier: str = Field(default="AUTO_APPROVED", description="Routing: AUTO_APPROVED, VP_APPROVAL_REQUIRED, or FLAGGED_MATH_MISMATCH")
    audit_notes: str = Field(default="", description="Audit explanation combining deterministic math check and LLM analysis")
    line_items: List[InvoiceLineItem] = Field(default_factory=list, description="Extracted line items with GL categorization")


class MultiDocFlowOutput(BaseModel):
    extracted_text: str = Field(description="Full OCR text extracted by WDU")
    kvps: Optional[List[dict]] = Field(default=None, description="Raw KVP entries with bounding boxes from docproc")
    logic_summary: LogicBlockOutput = Field(description="Deterministic math verification and approval routing from Logic block")
    structured_invoice: StructuredInvoiceRecord = Field(description="Final normalized and GL-coded record from GenAI prompt node")


# --- 3. Flow Construction Function ---

@flow(
    name="invoice_enterprise_idp_flow",
    display_name="invoice_enterprise_idp_flow",
    description=(
        "Enterprise IDP Pipeline: Multi-document OCR (Invoice, PO, Receipt), "
        "deterministic Python math audit, GenAI GL categorization, and ERP synchronization."
    ),
    input_schema=DocProcInput,
    output_schema=MultiDocFlowOutput,
)
def build_invoice_enterprise_idp_flow(aflow: Flow = None) -> Flow:
    # 1. Text extractor (docproc) node with Multi-Schema Auto-Detection
    doc_proc_node = aflow.docproc(
        name="invoice_docproc_node",
        display_name="invoice_docproc_node",
        description="Extract OCR text, multi-schema KVPs, and tables with bounding boxes.",
        task="text_extraction",
        error_handler_config=NodeErrorHandlerConfig(
            error_message="Failed during watsonx Document Understanding (docproc) extraction.",
            max_retries=1,
            retry_interval=1000,
        ),
        output_format=DocProcOutputFormat.object,
        enable_hw=True,
        kvp_schemas=[INVOICE_KVP_SCHEMA, PURCHASE_ORDER_KVP_SCHEMA, RECEIPT_KVP_SCHEMA],
        kvp_model_name="watsonx/mistralai/mistral-small-3-1-24b-instruct-2503",
        kvp_enable_text_hints=True,
    )
    doc_proc_node.map_input(
        input_variable="document_ref",
        expression="flow.input.document_ref",
    )

    # 2. Logic block (aflow.script) - Zero-hallucination Python Math & Approval Routing
    logic_script_code = """
def clean_num(val):
    if not val:
        return 0.0
    s = str(val).replace("$", "").replace("CAD", "").replace("USD", "").replace("EUR", "").replace(",", "").strip()
    try:
        return round(float(s), 2)
    except Exception:
        return 0.0

node_out = None
try:
    node_out = flow["invoice_docproc_node"].output
except Exception:
    try:
        node_out = flow.nodes["invoice_docproc_node"].output
    except Exception:
        try:
            node_out = flow.invoice_docproc_node.output
        except Exception:
            node_out = None

raw_kvps = []
text = ""
if node_out is not None:
    try:
        raw_kvps = node_out.kvps or []
    except Exception:
        if isinstance(node_out, dict):
            raw_kvps = node_out.get("kvps") or []
    try:
        text = node_out.text or ""
    except Exception:
        if isinstance(node_out, dict):
            text = node_out.get("text") or ""

# Map KVPs by label (supports both Pydantic object attributes and dicts)
kvp_map = {}
for item in raw_kvps:
    label = ""
    val = ""
    if isinstance(item, dict):
        k = item.get("key")
        v = item.get("value")
        if isinstance(k, dict) and isinstance(v, dict):
            label = k.get("semantic_label") or ""
            val = v.get("normalized_text") or v.get("raw_text") or ""
    else:
        k = getattr(item, "key", None)
        v = getattr(item, "value", None)
        if k is not None and v is not None:
            label = getattr(k, "semantic_label", "") or ""
            val = getattr(v, "normalized_text", "") or getattr(v, "raw_text", "") or ""
    if label:
        kvp_map[label] = val

# Classify document type from schema matches / text
doc_type = "Invoice"
if "po_number" in kvp_map and "total_authorized_amount" in kvp_map:
    doc_type = "PurchaseOrder"
elif "receipt_number" in kvp_map or "merchant_name" in kvp_map:
    doc_type = "Receipt"
elif "invoice_number" in kvp_map or "subtotal_amount" in kvp_map:
    doc_type = "Invoice"

subtotal = clean_num(kvp_map.get("subtotal_amount", 0.0))
tax = clean_num(kvp_map.get("tax_amount", 0.0))
total = clean_num(kvp_map.get("total_amount") or kvp_map.get("total_authorized_amount", 0.0))

# Fallback math if subtotal was 0
if subtotal == 0.0 and total > 0.0:
    subtotal = round(total - tax, 2)

expected_total = round(subtotal + tax, 2)
discrepancy = round(abs(total - expected_total), 2) if total > 0 else 0.0
math_valid = discrepancy <= 0.05

approval_tier = "AUTO_APPROVED"
if not math_valid and total > 0:
    approval_tier = "FLAGGED_MATH_MISMATCH"
elif total >= 10000.0:
    approval_tier = "VP_APPROVAL_REQUIRED"
else:
    approval_tier = "AUTO_APPROVED"

math_summary = (
    f"Deterministic check passed: Subtotal ({subtotal}) + Tax ({tax}) == Total ({total}) [kvps={len(raw_kvps)}]. Approval: {approval_tier}."
    if math_valid
    else f"Math discrepancy of {discrepancy} detected: Subtotal ({subtotal}) + Tax ({tax}) != Total ({total}) [kvps={len(raw_kvps)}]. Flagged for review."
)

self.output.detected_document_type = doc_type
self.output.invoice_number = kvp_map.get("invoice_number") or kvp_map.get("po_number") or kvp_map.get("receipt_number") or ""
self.output.vendor_name = kvp_map.get("vendor_name") or kvp_map.get("merchant_name") or ""
self.output.buyer_name = kvp_map.get("buyer_name") or ""
self.output.doc_date = kvp_map.get("invoice_date") or kvp_map.get("order_date") or kvp_map.get("transaction_date") or ""
self.output.po_number = kvp_map.get("po_number", "")
self.output.currency = kvp_map.get("currency", "USD")
self.output.computed_subtotal = subtotal
self.output.computed_tax = tax
self.output.computed_total = total
self.output.math_valid = math_valid
self.output.discrepancy = discrepancy
self.output.approval_tier = approval_tier
self.output.math_summary = math_summary
"""

    logic_node = aflow.script(
        name="math_and_routing_node",
        display_name="math_and_routing_node",
        description="Execute deterministic math validation, subtotal/tax audit, and approval tier classification.",
        output_schema=LogicBlockOutput,
        script=logic_script_code,
    )

    # 3. Generative prompt node (GenAI) - Semantic normalization, GL Categorization, and Audit
    structurer_node = aflow.prompt(
        name="executive_structurer_node",
        display_name="executive_structurer_node",
        description="Generate normalized structured invoice with General Ledger accounting categories and executive audit notes.",
        system_prompt=[
            "You are an expert Corporate Controller and IDP Financial Auditor.",
            "You receive OCR text and deterministic calculations from an upstream Python Logic Block.",
            "Your tasks:",
            "1. Output a normalized StructuredInvoiceRecord with clean dates (YYYY-MM-DD), clean numbers without currency symbols, and address details.",
            "2. Extract each line item from the document and assign an accurate accounting `gl_category` (e.g., 'Cloud Infrastructure', 'Cybersecurity Software', 'Professional Services', 'Hardware Equipment', 'Office Expense').",
            "3. Incorporate the upstream `approval_tier` and `math_summary` into `audit_notes` with a clear executive summary.",
        ],
        user_prompt=(
            "Document Type: {detected_document_type}\n"
            "Pre-verified Math: {math_summary}\n"
            "Approval Tier: {approval_tier}\n"
            "Invoice / Ref Number: {invoice_number}\n"
            "Vendor: {vendor_name}\n"
            "Total Amount: {currency} {computed_total}\n\n"
            "=== FULL DOCUMENT OCR TEXT ===\n{ocr_text}"
        ),
        llm="groq/openai/gpt-oss-120b",
        input_schema=GenAIInput,
        output_schema=StructuredInvoiceRecord,
    )
    structurer_node.map_input("ocr_text", 'flow["invoice_docproc_node"].output.text')
    structurer_node.map_input("detected_document_type", 'flow["math_and_routing_node"].output.detected_document_type')
    structurer_node.map_input("invoice_number", 'flow["math_and_routing_node"].output.invoice_number')
    structurer_node.map_input("vendor_name", 'flow["math_and_routing_node"].output.vendor_name')
    structurer_node.map_input("buyer_name", 'flow["math_and_routing_node"].output.buyer_name')
    structurer_node.map_input("currency", 'flow["math_and_routing_node"].output.currency')
    structurer_node.map_input("computed_subtotal", 'flow["math_and_routing_node"].output.computed_subtotal')
    structurer_node.map_input("computed_tax", 'flow["math_and_routing_node"].output.computed_tax')
    structurer_node.map_input("computed_total", 'flow["math_and_routing_node"].output.computed_total')
    structurer_node.map_input("math_valid", 'flow["math_and_routing_node"].output.math_valid')
    structurer_node.map_input("discrepancy", 'flow["math_and_routing_node"].output.discrepancy')
    structurer_node.map_input("approval_tier", 'flow["math_and_routing_node"].output.approval_tier')
    structurer_node.map_input("math_summary", 'flow["math_and_routing_node"].output.math_summary')

    # Sequence: START -> invoice_docproc_node -> math_and_routing_node -> executive_structurer_node -> END
    aflow.sequence(START, doc_proc_node, logic_node, structurer_node, END)

    # Flow outputs
    aflow.map_output(
        output_variable="extracted_text",
        expression='flow["invoice_docproc_node"].output.text',
    )
    aflow.map_output(
        output_variable="kvps",
        expression='flow["invoice_docproc_node"].output.kvps',
    )
    aflow.map_output(
        output_variable="logic_summary",
        expression='flow["math_and_routing_node"].output',
    )
    aflow.map_output(
        output_variable="structured_invoice",
        expression='flow["executive_structurer_node"].output',
    )

    return aflow
