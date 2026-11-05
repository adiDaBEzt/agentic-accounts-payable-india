"""watsonx Orchestrate agentic flow: a GST supplier invoice from document to Odoo bill.

    START -> extract_invoice   (Document processing: WDU OCR + GST invoice KVP schema, bounding boxes)
          -> statutory_checks  (Script: normalisation, GSTIN check digit, GST regime, slab, arithmetic)
          -> classify_payment  (Prompt: the LLM judges the nature of payment for TDS)
          -> erp_controls      (Tool: vendor, duplicate, bank, IRN, PO/GRN 3-way match, TDS on live Odoo)
          -> route_invoice     (Decision table: AP routing policy)
          -> route branch ─ touchless → post_bill   (Tool: create + post the Odoo bill)
                          ├ exception → hold_bill   (Tool: draft bill + review task)
                          └ blocked   → END         (duplicate: no bill)

Only the payment classification uses an LLM; every number, GSTIN and ERP check is deterministic, and the
routing policy is a decision table that AP can change in the flow editor without code. The same flow runs
from the workbench API, email intake or the AP Copilot.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

# Import flows before types (circular-import quirk in the ADK).
from ibm_watsonx_orchestrate.flow_builder.flows import END, START, Flow, flow
from ibm_watsonx_orchestrate.flow_builder.types import (
    DocProcField,
    DocProcInput,
    DocProcKVPSchema,
    DocProcOutputFormat,
    DocProcTable,
    DecisionsCondition,
    DecisionsRule,
    NodeErrorHandlerConfig,
)

TOUCHLESS_LIMIT_INR = 2_500_000  # delegation of authority: above ₹25 lakh a person signs off


def _f(description: str, example: str) -> DocProcField:
    return DocProcField(description=description, default="", example=example)


GST_INVOICE_SCHEMA = DocProcKVPSchema(
    document_type="GSTTaxInvoice",
    document_description="An Indian GST tax invoice issued by a supplier to a registered business buyer.",
    fields={
        "supplier_name": _f("Legal name of the supplier issuing the invoice (top of page)", "Sahyadri Drums & Containers Pvt. Ltd."),
        "supplier_gstin": _f("15-character GSTIN of the supplier", "27AAHCS7314P1ZR"),
        "supplier_address": _f("Address of the supplier", "Gat No. 312, Chakan MIDC Phase II, Pune - 410501"),
        "buyer_name": _f("Name of the buyer in the Bill To section", "Meridian Specialty Chemicals India Pvt. Ltd."),
        "buyer_gstin": _f("GSTIN of the buyer in the Bill To section", "27AAJCM4821K1Z7"),
        "place_of_supply": _f("Place of supply state with state code", "Maharashtra (27)"),
        "invoice_number": _f("Supplier invoice number", "SDC/26-27/0418"),
        "invoice_date": _f("Invoice date", "2026-10-28"),
        "po_number": _f("Buyer's purchase order / order number", "MSC-PO-26-0147"),
        "irn": _f("64-character e-invoice Invoice Reference Number (IRN), if printed", "b66715466c35dae003a57b13096a66275dfd63fb64184cb174a555c59541b9a8"),
        "taxable_value": _f("Total taxable value before GST", "304200.00"),
        "cgst_amount": _f("Total CGST amount, if charged", "27378.00"),
        "sgst_amount": _f("Total SGST / UTGST amount, if charged", "27378.00"),
        "igst_amount": _f("Total IGST amount, if charged", "54756.00"),
        "total_amount": _f("Total invoice value including tax", "358956.00"),
        "bank_name": _f("Supplier bank name for remittance", "HDFC Bank"),
        "bank_account": _f("Supplier bank account number for remittance", "50200041873310"),
        "bank_ifsc": _f("IFSC code of the supplier bank branch", "HDFC0001267"),
        "line_items": DocProcTable(
            type="array",
            description="Invoice line items table",
            columns={
                "description": _f("Description of goods or services", "HDPE Open-Top Drum 200 L"),
                "hsn_sac": _f("HSN or SAC code", "39231090"),
                "quantity": _f("Quantity", "120"),
                "uom": _f("Unit of measure", "Nos"),
                "unit_price": _f("Rate per unit", "2450.00"),
                "amount": _f("Taxable value of the line", "294000.00"),
            },
        ),
    },
)


class LineItem(BaseModel):
    description: str = ""
    hsn_sac: str = ""
    quantity: float = 0.0
    uom: str = ""
    unit_price: float = 0.0
    amount: float = 0.0


class StatutoryCheck(BaseModel):
    code: str
    category: str
    status: str = Field(description="pass | warn | fail | info")
    title: str
    detail: str = ""


class InvoiceRecord(BaseModel):
    supplier_name: str = ""
    supplier_gstin: str = ""
    supplier_address: str = ""
    buyer_name: str = ""
    buyer_gstin: str = ""
    place_of_supply: str = ""
    invoice_number: str = ""
    invoice_date: str = ""
    po_number: str = ""
    irn: str = ""
    taxable_value: float = 0.0
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    igst_amount: float = 0.0
    total_amount: float = 0.0
    bank_name: str = ""
    bank_account: str = ""
    bank_ifsc: str = ""
    line_items: List[LineItem] = Field(default_factory=list)
    lines_text: str = Field(default="", description="Line items as plain text, for the classifier")
    checks: List[StatutoryCheck] = Field(default_factory=list)


class ClassifierInput(BaseModel):
    supplier_name: str = ""
    lines_text: str = ""


class PaymentNature(BaseModel):
    nature: str = Field(description="One of: goods, professional, technical, contract, rent, other")
    confidence: float = Field(description="0.0 - 1.0")
    rationale: str = Field(description="One sentence explaining the classification")


class FlowOutput(BaseModel):
    invoice: InvoiceRecord
    payment_nature: PaymentNature
    kvps: Optional[List[dict]] = None
    metadata: Optional[dict] = None
    extracted_text: str = ""
    route: str = ""
    route_reason: str = ""
    controls: Optional[dict] = None
    posted: Optional[dict] = None  # set by whichever booking node ran
    held: Optional[dict] = None


STATUTORY_CHECKS_SCRIPT = r'''
CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
SLABS = [0.0, 5.0, 18.0, 40.0]

def num(v):
    s = "".join(ch for ch in str(v or "") if ch.isdigit() or ch in ".-")
    try:
        return round(float(s), 2) if s not in ("", ".", "-") else 0.0
    except Exception:
        return 0.0

def iso_date(v):
    s = str(v or "").strip().replace("/", "-").replace(".", "-")
    p = s.split("-")
    if len(p) == 3 and len(p[0]) == 4:
        return s
    if len(p) == 3 and len(p[2]) == 4:
        return p[2] + "-" + p[1].zfill(2) + "-" + p[0].zfill(2)
    return s

def gstin_ok(g):
    g = (g or "").strip().upper()
    if len(g) != 15 or not g[:2].isdigit() or g[13] != "Z":
        return False
    for ch in g:
        if ch not in CHARS:
            return False
    total = 0
    for i in range(14):
        prod = CHARS.index(g[i]) * (2 if i % 2 else 1)
        total += prod // 36 + prod % 36
    return CHARS[(36 - total % 36) % 36] == g[14]

def attr(o, k):
    if isinstance(o, dict):
        return o.get(k)
    return getattr(o, k, None)

node_out = flow["extract_invoice"].output
raw_kvps = attr(node_out, "kvps") or []

fields = {}
rows = {}
for item in raw_kvps:
    k = attr(item, "key")
    v = attr(item, "value")
    label = attr(k, "semantic_label") if k is not None else ""
    val = (attr(v, "normalized_text") or attr(v, "raw_text") or "") if v is not None else ""
    if not label:
        continue
    if "." in label and attr(item, "table_row_index") is not None:
        idx = attr(item, "table_row_index")
        rows.setdefault(idx, {})[label.split(".", 1)[1]] = val
    else:
        fields[label] = val

lines = []
for idx in sorted(rows.keys()):
    r = rows[idx]
    lines.append({
        "description": str(r.get("description", "")).strip(),
        "hsn_sac": "".join(ch for ch in str(r.get("hsn_sac", "")) if ch.isdigit()),
        "quantity": num(r.get("quantity")),
        "uom": str(r.get("uom", "")).strip(),
        "unit_price": num(r.get("unit_price")),
        "amount": num(r.get("amount")),
    })

sup_gstin = str(fields.get("supplier_gstin", "")).replace(" ", "").upper()
buy_gstin = str(fields.get("buyer_gstin", "")).replace(" ", "").upper()
pos = str(fields.get("place_of_supply", ""))
pos_code = "".join(ch for ch in pos if ch.isdigit())[:2] or buy_gstin[:2]
taxable = num(fields.get("taxable_value"))
cgst = num(fields.get("cgst_amount"))
sgst = num(fields.get("sgst_amount"))
igst = num(fields.get("igst_amount"))
total = num(fields.get("total_amount"))
irn = str(fields.get("irn", "")).strip().lower().replace(" ", "")
line_sum = round(sum(l["amount"] for l in lines), 2)
if taxable == 0.0:
    taxable = line_sum

checks = []
def add(code, cat, status, title, detail):
    checks.append({"code": code, "category": cat, "status": status, "title": title, "detail": detail})

missing = [n for n in ["invoice_number", "invoice_date", "supplier_gstin", "total_amount"] if not fields.get(n)]
add("DOC-01", "Document", "fail" if missing else "pass", "Mandatory invoice particulars",
    ("Missing: " + ", ".join(missing)) if missing else "Invoice no., date, supplier GSTIN and total present")
no_hsn = [str(i + 1) for i, l in enumerate(lines) if len(l["hsn_sac"]) < 4]
add("DOC-02", "Document", "warn" if no_hsn else "pass", "HSN / SAC on every line",
    ("No valid HSN/SAC on line(s) " + ", ".join(no_hsn)) if no_hsn else str(len(lines)) + " line(s) carry HSN/SAC codes")

add("GST-01", "GST", "pass" if gstin_ok(sup_gstin) else "fail", "Supplier GSTIN valid",
    sup_gstin + (" passes format and check-digit validation" if gstin_ok(sup_gstin) else " fails format / check-digit validation"))
add("GST-02", "GST", "pass" if gstin_ok(buy_gstin) else "fail", "Buyer GSTIN valid",
    buy_gstin + (" passes format and check-digit validation" if gstin_ok(buy_gstin) else " fails format / check-digit validation"))

intra = sup_gstin[:2] == pos_code
if intra:
    ok = igst == 0.0 and cgst > 0 and abs(cgst - sgst) <= 0.5
    add("GST-03", "GST", "pass" if ok else "fail", "Tax regime matches place of supply",
        "Intra-state supply (" + sup_gstin[:2] + " to " + pos_code + "): expects CGST + SGST" + ("" if ok else "; invoice charges IGST " + str(igst)))
else:
    ok = cgst == 0.0 and sgst == 0.0 and igst > 0
    add("GST-03", "GST", "pass" if ok else "fail", "Tax regime matches place of supply",
        "Inter-state supply (" + sup_gstin[:2] + " to " + pos_code + "): expects IGST" + ("" if ok else "; invoice charges CGST " + str(cgst) + " + SGST " + str(sgst) + " instead"))

tax_total = round(cgst + sgst + igst, 2)
eff = round(tax_total * 100.0 / taxable, 2) if taxable else 0.0
slab = min(SLABS, key=lambda s: abs(s - eff))
add("GST-04", "GST", "pass" if abs(slab - eff) <= 0.1 else "warn", "GST rate is a notified slab",
    "Effective rate " + str(eff) + "% (nearest slab " + str(slab) + "%)")

bad_lines = [str(i + 1) for i, l in enumerate(lines) if l["quantity"] and l["unit_price"] and abs(round(l["quantity"] * l["unit_price"], 2) - l["amount"]) > 1.0]
add("MATH-01", "Arithmetic", "fail" if bad_lines or abs(line_sum - taxable) > 1.0 else "pass", "Line items add up",
    (("Qty x rate mismatch on line(s) " + ", ".join(bad_lines) + ". ") if bad_lines else "") +
    "Sum of lines " + str(line_sum) + " vs taxable value " + str(taxable))
diff = round(taxable + tax_total - total, 2)
add("MATH-02", "Arithmetic", "pass" if abs(diff) <= 1.0 else "fail", "Taxable value + GST = invoice total",
    str(taxable) + " + " + str(tax_total) + " = " + str(round(taxable + tax_total, 2)) + " vs total " + str(total))

irn_ok = len(irn) == 64 and all(ch in "0123456789abcdef" for ch in irn)
add("EINV-01", "E-invoice", "pass" if irn_ok else "info", "IRN printed on invoice",
    "Valid 64-character IRN found" if irn_ok else "No IRN on the document")

self.output.supplier_name = str(fields.get("supplier_name", "")).strip()
self.output.supplier_gstin = sup_gstin
self.output.supplier_address = str(fields.get("supplier_address", "")).strip()
self.output.buyer_name = str(fields.get("buyer_name", "")).strip()
self.output.buyer_gstin = buy_gstin
self.output.place_of_supply = pos
self.output.invoice_number = str(fields.get("invoice_number", "")).strip()
self.output.invoice_date = iso_date(fields.get("invoice_date"))
self.output.po_number = str(fields.get("po_number", "")).strip()
self.output.irn = irn if irn_ok else ""
self.output.taxable_value = taxable
self.output.cgst_amount = cgst
self.output.sgst_amount = sgst
self.output.igst_amount = igst
self.output.total_amount = total
self.output.bank_name = str(fields.get("bank_name", "")).strip()
self.output.bank_account = "".join(ch for ch in str(fields.get("bank_account", "")) if ch.isalnum())
self.output.bank_ifsc = str(fields.get("bank_ifsc", "")).replace(" ", "").upper()
self.output.line_items = lines
self.output.lines_text = "\n".join("- " + l["description"] + " (HSN/SAC " + l["hsn_sac"] + ", qty " + str(l["quantity"]) + " " + l["uom"] + ")" for l in lines)
self.output.checks = checks
'''


@flow(
    name="ap_invoice_processing_flow",
    display_name="AP invoice processing (GST · 3-way match · TDS → Odoo)",
    description=(
        "Processes an Indian GST supplier invoice end to end: extracts it with bounding boxes, runs GST, "
        "arithmetic, vendor, duplicate, bank, e-invoice, PO/GRN 3-way match and TDS controls against Odoo, "
        "then posts the bill touchless, holds it for AP review, or blocks a duplicate. Input: the invoice document."
    ),
    input_schema=DocProcInput,
    output_schema=FlowOutput,
)
def build_ap_invoice_processing_flow(aflow: Flow = None) -> Flow:
    extract = aflow.docproc(
        name="extract_invoice",
        display_name="Extract invoice (WDU)",
        description="OCR and GST invoice key-value / table extraction with bounding boxes.",
        task="text_extraction",
        output_format=DocProcOutputFormat.object,
        enable_hw=True,
        kvp_schemas=[GST_INVOICE_SCHEMA],
        kvp_force_schema_name="GSTTaxInvoice",
        kvp_enable_text_hints=True,
        error_handler_config=NodeErrorHandlerConfig(
            error_message="Document extraction failed.", max_retries=1, retry_interval=1000
        ),
    )
    extract.map_input(input_variable="document_ref", expression="flow.input.document_ref")

    checks = aflow.script(
        name="statutory_checks",
        display_name="GST & arithmetic checks",
        description="Normalises extracted values and runs deterministic GSTIN, GST regime, slab and arithmetic checks.",
        output_schema=InvoiceRecord,
        script=STATUTORY_CHECKS_SCRIPT,
    )

    classify = aflow.prompt(
        name="classify_payment",
        display_name="Classify nature of payment (TDS)",
        description="Classifies what is being paid for, which drives the TDS section.",
        system_prompt=[
            "You are an Indian accounts-payable tax specialist.",
            "Classify the nature of payment on a supplier invoice for TDS purposes under the Income-tax Act, 2025.",
            "Choose exactly one nature:",
            "goods - purchase of goods or materials;",
            "professional - professional or consultancy fees (engineering, legal, audit, safety studies, advisory);",
            "technical - fees for technical services (software support, testing, technical assistance);",
            "contract - contract work (maintenance contracts, AMC, repairs, labour, transport, job work, catering);",
            "rent - rent of land, building, plant or machinery;",
            "other - none of the above.",
            "SAC codes starting 99 indicate services; HSN codes indicate goods.",
            "Return the nature, your confidence between 0 and 1, and a one-sentence rationale.",
        ],
        user_prompt="Supplier: {supplier_name}\nLine items:\n{lines_text}",
        llm="groq/openai/gpt-oss-120b",
        input_schema=ClassifierInput,
        output_schema=PaymentNature,
    )
    classify.map_input("supplier_name", 'flow["statutory_checks"].output.supplier_name')
    classify.map_input("lines_text", 'flow["statutory_checks"].output.lines_text')

    erp = aflow.tool("ap_erp_controls", name="erp_controls", display_name="ERP controls (Odoo)",
                     error_handler_config=NodeErrorHandlerConfig(error_message="ERP controls failed.", max_retries=1,
                                                                 retry_interval=2000))
    erp.map_input("invoice", 'flow["statutory_checks"].output')
    erp.map_input("payment_nature", 'flow["classify_payment"].output')

    def rule(when: tuple[str, DecisionsCondition], route: str, reason: str) -> DecisionsRule:
        return (DecisionsRule().condition(f'flow["erp_controls"].output.{when[0]}', when[1])
                .action("flow.output.route", route).action("flow.output.route_reason", reason))

    decide = aflow.decisions(
        name="route_invoice",
        display_name="AP routing policy",
        description="First matching rule wins: duplicates are blocked, any failed control goes to review, and "
                    "clean invoices above the touchless limit need a person's sign-off.",
        rules=[
            rule(("duplicates", DecisionsCondition().greater_than(0)), "blocked", "Duplicate invoice"),
            rule(("exceptions", DecisionsCondition().greater_than(0)), "exception", ""),
            rule(("invoice_total", DecisionsCondition().greater_than(TOUCHLESS_LIMIT_INR)), "exception",
                 "Above ₹25 lakh touchless limit"),
        ],
        default_actions={"flow.output.route": "touchless", "flow.output.route_reason": ""},
    )

    post = aflow.tool("ap_post_bill", name="post_bill", display_name="Post bill in Odoo")
    hold = aflow.tool("ap_hold_bill", name="hold_bill", display_name="Hold for AP review")
    for node in (post, hold):
        node.map_input("invoice", 'flow["statutory_checks"].output')
        node.map_input("control_result", 'flow["erp_controls"].output.result')
    hold.map_input("reason", "flow.output.route_reason")

    route = aflow.branch(name="route", display_name="Route", evaluator="flow.output.route")
    route.case("touchless", post).case("exception", hold).case("blocked", END)

    aflow.sequence(START, extract, checks, classify, erp, decide, route)
    aflow.edge(post, END)
    aflow.edge(hold, END)

    aflow.map_output(output_variable="invoice", expression='flow["statutory_checks"].output')
    aflow.map_output(output_variable="payment_nature", expression='flow["classify_payment"].output')
    aflow.map_output(output_variable="kvps", expression='flow["extract_invoice"].output.kvps')
    aflow.map_output(output_variable="metadata", expression='flow["extract_invoice"].output.metadata')
    aflow.map_output(output_variable="extracted_text", expression='flow["extract_invoice"].output.text')
    aflow.map_output(output_variable="controls", expression='flow["erp_controls"].output.result')
    aflow.map_output(output_variable="posted", expression='flow["post_bill"].output')
    aflow.map_output(output_variable="held", expression='flow["hold_bill"].output')
    return aflow
