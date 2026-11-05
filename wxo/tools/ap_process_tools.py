"""Process tools used as nodes of ap_invoice_processing_flow: ERP controls, then post or hold the bill.
Agents do not call these directly; the flow's decision table chooses which booking node runs."""

from ibm_watsonx_orchestrate.agent_builder.tools import ToolPermission, tool
from ibm_watsonx_orchestrate.run import connections
from pydantic import BaseModel, ConfigDict, Field

from apcore import booking, controls
from apcore.odoo import Odoo
from erp import APP_ID, ODOO_CREDENTIALS


# Typed (open) inputs for the flow nodes. The flow runtime also passes the previous node's output as `data`,
# which every tool accepts and ignores.
class Invoice(BaseModel):
    model_config = ConfigDict(extra="allow")
    invoice_number: str = ""
    supplier_gstin: str = ""
    total_amount: float = 0.0
    checks: list[dict] = Field(default_factory=list)


class PaymentNature(BaseModel):
    model_config = ConfigDict(extra="allow")
    nature: str = ""
    confidence: float = 0.0
    rationale: str = ""


class ControlResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    duplicates: int = 0
    exceptions: int = 0
    checks: list[dict] = Field(default_factory=list)
    vendor: dict | None = None


class ControlOutcome(BaseModel):
    duplicates: int = Field(description="Failed duplicate-invoice controls (DUP-01)")
    exceptions: int = Field(description="Failed controls in total, including statutory checks from the flow")
    invoice_total: float = Field(description="Invoice total in INR")
    result: ControlResult = Field(description="Control results: checks, vendor, PO, matched lines, TDS, net payable")


class Booking(BaseModel):
    summary: str
    bill: dict | None = None
    controls: dict | None = Field(default=None, description="Control results, updated when a policy rule added a check")


def _plain(value) -> dict:
    return value.model_dump() if isinstance(value, BaseModel) else dict(value or {})


def _odoo() -> Odoo:
    c = connections.key_value(APP_ID)
    return Odoo(c["url"], c["db"], c["username"], c["password"])


@tool(name="ap_erp_controls", permission=ToolPermission.READ_ONLY, expected_credentials=ODOO_CREDENTIALS)
def ap_erp_controls(invoice: Invoice, payment_nature: PaymentNature, data: dict | None = None) -> ControlOutcome:
    """Run the ERP controls on an extracted GST invoice against live Odoo data: vendor master and buyer GSTIN,
    duplicates, remittance bank account, e-invoice IRN, PO price and GRN quantity (3-way match) and TDS."""
    result = controls.evaluate(_plain(invoice), _plain(payment_nature), _odoo())
    return ControlOutcome(duplicates=result["duplicates"], exceptions=result["exceptions"],
                          invoice_total=float(invoice.total_amount or 0), result=result)


@tool(name="ap_post_bill", permission=ToolPermission.READ_WRITE, expected_credentials=ODOO_CREDENTIALS)
def ap_post_bill(invoice: Invoice, control_result: ControlResult, data: dict | None = None) -> Booking:
    """Create and post the vendor bill in Odoo for an invoice that passed every control (touchless)."""
    return Booking(**booking.post(_plain(invoice), _plain(control_result), _odoo()))


@tool(name="ap_hold_bill", permission=ToolPermission.READ_WRITE, expected_credentials=ODOO_CREDENTIALS)
def ap_hold_bill(invoice: Invoice, control_result: ControlResult, reason: str = "",
                 data: dict | None = None) -> Booking:
    """Create a draft vendor bill in Odoo with a review task listing the exceptions, for AP to approve or reject."""
    return Booking(**booking.hold(_plain(invoice), _plain(control_result), _odoo(), reason))
