# Agentic Accounts Payable for India — IBM watsonx Orchestrate + ERP

An AI agent that takes a supplier invoice from receipt to ERP posting. It applies the India-specific
controls that generic AP tools leave to humans: GST regime and GSTIN validation, e-invoice IRN, TDS under
the Income-tax Act 2025, GRN-based 3-way match, duplicate detection and vendor bank-account verification.
Clean invoices post **touchless**. Exceptions are held in the ERP with a review task and a recommended
action. Two conversational agents serve the AP team and suppliers from the same live ERP data.

Odoo is the reference ERP (vendor master, POs, goods receipts, vendor bills). The ERP layer is a thin
client (`app/odoo.py`, `wxo/tools/erp.py`), so it can be replaced with SAP S/4HANA OData without touching
the flow or the agents.

## The business problem

A typical Indian manufacturer receives 100–200 supplier invoices a day. Global AP suites handle capture and
PO matching, but these steps usually stay manual:

| Gap | What goes wrong | What the agent does |
|---|---|---|
| **GRN validation** | Invoices are paid for goods not yet received | Billed qty ≤ received − already billed, read live from ERP receipts; proposes "post received qty + request credit note" |
| **TDS** | Wrong section or rate, missed deduction | Nature of payment classified by an LLM, cross-checked against the vendor-master TDS section; rate, thresholds and FY aggregate computed; Odoo withholding tax applied on the bill |
| **GST compliance** | CGST/SGST charged on inter-state supplies, wrong buyer GSTIN, ITC lost | GSTIN check digit, state-code vs place-of-supply regime check, slab check, buyer GSTIN check |
| **E-invoicing** | Invoices without an IRN from mandated suppliers | IRN required when the vendor is tagged *E-invoice applicable* |
| **Payment fraud** | "Please note our new bank details" | Remittance account compared with the verified vendor-master account; exception cannot be approved by the Copilot |
| **Duplicates** | The same invoice re-sent as a scan | Blocked against all non-cancelled ERP bills before any bill is created |
| **Visibility** | Suppliers email AP asking "when will I be paid?" | Supplier Desk agent answers status, TDS withheld and expected payment date, scoped to the caller's GSTIN |

## Architecture

```
 Intake            watsonx Orchestrate: ap_invoice_processing_flow                                    Odoo
 ──────            ────────────────────────────────────────────────                                   ────
 Gmail AP inbox ┐  extract_invoice   docproc · WDU OCR + GST invoice schema, bounding boxes
 Upload / API ──┼▶ statutory_checks  script · GSTIN check digit, GST regime, slab, arithmetic
 AP Copilot ────┘  classify_payment  prompt · nature of payment for TDS (the only LLM step)
                   erp_controls      tool · vendor, buyer GSTIN, duplicate, bank, IRN, PO/GRN, TDS ◀── live data
                   route_invoice     decision table · AP routing policy
                   route ── touchless → post_bill   tool · bill POSTED with GST + TDS              ──▶ bill
                         ├ exception → hold_bill   tool · DRAFT bill + review task + chatter      ──▶ bill
                         └ blocked   → end         duplicate, no bill

 Workbench (Carbon UI): live progress, document viewer, approve / reject / email supplier, governance
 Agents: AP Copilot (internal) · Supplier Desk (external), on the same Odoo tools
 Control plane: guardrails, PII and IFSC masking, secrets detection, tool rate limits, model fallback
```

**Why the work is split this way**

- **The process is a flow, not an agent.** Every invoice runs the same steps in the same order, so it is a
  flow with typed nodes. Agents are used only where conversation is the job: the AP team's questions and
  approvals, and supplier status queries.
- **Deterministic where it matters.** Numbers, GSTINs, tax regimes and ERP matches are checked in code (a
  script node and an Odoo tool node). The LLM classifies only what needs judgement: the nature of payment
  for TDS.
- **Policy is a decision table.** Routing (duplicate → block, any failed control → review, above the
  ₹25 lakh touchless limit → sign-off, otherwise post) is a decision-table node that AP can change in the
  flow editor without code.
- **One engine.** `wxo/tools/apcore` (India rules, Odoo client, controls, booking) is deployed with the
  tools and imported by the workbench for reviewer actions, so the rules never diverge.
- **The ERP is the system of record.** Bills, review tasks (`mail.activity`) and the agent's control log
  (chatter) live in Odoo. Approvals made through the Copilot or directly in Odoo sync back to the workbench.
- **Governed agents.** Least-privilege tools (the Supplier Desk is read-only and GSTIN-scoped), with
  control-plane policies on top that apply whatever the prompt says.

## Governance (watsonx Orchestrate control plane)

Defined in `wxo/controls/*.yaml`, imported by `deploy.sh`, and shown live on the workbench's
**Governance** page.

| Control | Type | Applies to | Runs at | Why |
|---|---|---|---|---|
| Supplier Desk · content guardrails | Content Guardrails | `supplier_desk_agent` | input | External channel: blocks jailbreaks and abuse before the agent sees them |
| Supplier Desk · PII masking | PII Filter | `supplier_desk_agent` | output | Bank accounts, emails and phone numbers never reach a supplier |
| Supplier Desk · IFSC and account redaction | Regex Pattern | `supplier_desk_agent` | output | India identifiers the generic PII filter does not know |
| Supplier tools · rate limit | Rate Limiter | supplier status tools | tool call | 20 calls a minute stops GSTIN or invoice enumeration |
| AP Copilot · approval rate limit | Rate Limiter | `approve_ap_exception` | tool call | Caps the blast radius of the only write tool |
| AP Copilot · secrets detector | Secrets Detector | `ap_copilot_agent` | input + output | Staff paste portal text; credentials are redacted |
| Model policy `ap_gpt_oss_fallback` | Fallback | both agents | model | Groq primary, the same model on Bedrock on 429 / 5xx |

A blocked run returns `USER_CONFIGURED_CONTROL_BLOCKED`, which the chat shows as **Blocked by control**.
Model-level controls on the tenant bind to custom (virtual) models, so the fallback is a model policy.

## Repository

| Path | Purpose |
|---|---|
| `wxo/flows/ap_invoice_processing_flow.py` | The process: docproc → script → prompt → ERP tool → decision table → post / hold |
| `wxo/tools/apcore/` | Shared engine: India rules, Odoo client, ERP controls, bill booking (standard library only) |
| `wxo/tools/` | Flow process tools and agent tools; Odoo credentials come from the `odoo_erp` key-value connection |
| `wxo/controls/` | Control-plane policies (guardrails, PII, regex, rate limits, secrets) |
| `wxo/agents/` | `ap_copilot_agent` (internal) and `supplier_desk_agent` (external) |
| `wxo/deploy.sh` | Creates the connection and imports tools, flow, model policy, agents and controls |
| `app/` | FastAPI workbench (`pipeline.py`, `wxo.py`, `mail.py`, `store.py`) and the Carbon UI in `static/` |
| `scripts/setup_odoo.py` | Idempotent ERP provisioning: apps, GST/TDS taxes, buyer, vendors, products, POs, GRNs |
| `scripts/demo_data.py` | One spec for the demo world, shared by the ERP seed and the invoice generator |
| `scripts/generate_samples.py` | Renders the GST tax invoices in `samples/` |

## Setup

```bash
uv venv -p 3.12 .venv && uv pip install -p .venv -r requirements.txt
cp .env.example .env            # fill in wxO, Odoo and (optionally) Gmail

# 1. ERP: works on any Odoo 18+ database with Indian localisation (a free trial is fine)
.venv/bin/python scripts/setup_odoo.py

# 2. watsonx Orchestrate
.venv/bin/orchestrate env add -n ap-demo -u "$WXO_INSTANCE_URL" --type ibm_iam
.venv/bin/orchestrate env activate ap-demo --api-key "$WXO_API_KEY"
ORCH=.venv/bin/orchestrate ./wxo/deploy.sh

# 3. Run
.venv/bin/uvicorn app.main:app --port 8090      # http://localhost:8090
```

**Gmail (optional):** create the AP mailbox, enable 2-Step Verification, create an app password, and set
`GMAIL_USER` / `GMAIL_APP_PASSWORD`. Use **Check AP inbox**, or set `GMAIL_POLL_SECONDS`, to ingest
attachments. Suppliers get an acknowledgement with the outcome, and reviewers can send correction requests
drafted from the failed controls. Set `VENDOR_EMAIL_OVERRIDE` during demos so no real vendor is emailed.

## Five-minute demo

Use the reset icon in the header first; it removes the bills the agent created so every run starts clean.

1. **Touchless:** process `01_sahyadri…`. The 3-way match passes against GRN WH/IN/00001 and BILL/… posts
   in Odoo with CGST + SGST. Open the bill in Odoo to show the agent's control log in the chatter.
2. **TDS:** `02_kaveri…`. The LLM classifies a HAZOP study as professional fees. Sec 393(1) Sl.6(iii)(b)
   (formerly 194J) @ 10% = ₹41,200 is applied as an Odoo withholding tax.
3. **GRN shortage:** `03_narmada…`. 10 t billed, 8 t received, backorder open. **Approve & post → received
   quantity only** books ₹13,40,480 and updates the PO's billed quantity.
4. **Fraud + GST:** `04_coromandel…`. A changed bank account and CGST/SGST charged on an inter-state supply
   (red boxes on the document). Show **Email supplier** with the supplier-safe draft.
5. **Price + IRN:** `05_konkan…`. Unit price 7.1% above the PO and no IRN from an e-invoice-mandated vendor.
6. **Duplicate:** `06_…_scan.png`, a skewed, noisy phone scan of invoice 01, is blocked before a bill exists.
7. **Governance:** open the Governance page, then **Try a jailbreak on Supplier Desk**; the content
   guardrail blocks it before the agent runs.
8. **Assistants:** *"What needs my attention today?"* (Copilot), then the Supplier Desk with
   *"Status of KPA/26-27/073? GSTIN 29AAQFK2209M1ZU"*, then the same question with another supplier's GSTIN.

## Notes

- TDS sections follow the Income-tax Act, 2025 numbering used by Odoo's `l10n_in` taxes, with legacy 1961
  references shown alongside. Rates and thresholds in `app/india.py` are demo defaults; confirm them with
  your tax team.
- GST slabs follow GST 2.0 (5 / 18 / 40%).
- All companies, GSTINs and bank accounts in the samples are fictional.
