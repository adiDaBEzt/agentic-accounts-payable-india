# Build an agentic accounts-payable system for India with watsonx Orchestrate and Odoo

*A hands-on guide to processing any AP document, from GST supplier invoices to employee taxi receipts, with an
agentic flow, decision tables, governed agents and a live ERP.*

By Aditya Krishnan

Accounts payable teams in India still key in most of what lands in their inbox. A mid-sized manufacturer gets
100 to 200 supplier invoices a day. It also gets employees' taxi and hotel receipts, signed purchase-order
copies and the delivery challans that arrive with goods. Generic capture tools read the text, but the India-specific
checks stay manual:

- Is GST charged under the right regime for the place of supply?
- Which TDS section applies?
- Did the goods actually arrive?
- Is the "new bank account" on the invoice genuine?

This tutorial shows how to build an agent that takes any of those documents from receipt to the right action in
the ERP. It uses [IBM watsonx Orchestrate](https://www.ibm.com/products/watsonx-orchestrate) for document
processing, the process flow, conversational agents and governance. It uses [Odoo](https://www.odoo.com) as the
ERP of record. You build the process as an **agentic flow** with document, script, prompt, tool, decision-table
and branch nodes. Agents are used only where conversation is the job.

By the end of this tutorial, you will have a working system:
- It recognises five kinds of document.
- It posts clean supplier invoices to Odoo without a human touch.
- It holds exceptions as draft bills with a review task.
- It books expense claims and goods receipts.
- It answers the AP team and suppliers through two governed agents.

## Accounts payable use case

Meridian Specialty Chemicals is a fictional chemicals manufacturer in Navi Mumbai. Its AP team wants to drop any
document into one place and have it handled:

> "Here's Coromandel's invoice, Ananya's taxi receipt from yesterday, and the challan for Narmada's balance two
> tonnes. Book what's clean and tell me what needs me."

The system does the following:

1. Reads the document and works out what it is: a supplier invoice, an expense receipt, a PO copy, a delivery
   challan, or something it doesn't handle.
2. Runs the checks that apply to that type against live Odoo data:
   - **Invoices:** GST, arithmetic, 3-way match, bank account, duplicate and TDS checks.
   - **Receipts:** expense-policy checks.
   - **PO copies and challans:** matching against the purchase order.
3. Routes the document with a decision table that the AP team owns.
4. Acts in Odoo:
   - posts a vendor bill, or holds it as a draft with a review task;
   - approves or holds an expense;
   - books a goods receipt;
   - blocks a duplicate.
5. Explains every decision. Each Odoo record carries the agent's control log, and the workbench highlights the
   fields that failed.

### Architecture of the solution

![Architecture: intake channels feed the ap_document_processing_flow in watsonx Orchestrate, which branches by document type and acts on Odoo; a Carbon workbench, two agents and the control plane sit on top.](images/architecture.png)

The solution has five components:

1. **Document flow** (`ap_document_processing_flow`): the process itself, built with the watsonx Orchestrate ADK.
   - A *document processing* node runs OCR and extracts key-value pairs and tables with bounding boxes. It is
     given four schemas (GST tax invoice, expense receipt, purchase order, delivery challan) and reports which one
     the document matches.
   - A *branch* sends each type down its own path of script, prompt, tool and decision-table nodes.
2. **Shared AP engine** (`wxo/tools/apcore`): standard-library Python for the India rules, the Odoo client, the
   controls and the booking logic. It is deployed to watsonx Orchestrate inside the tool package, and the
   workbench imports the same code, so the rules never diverge.
3. **Odoo ERP**: the system of record for the vendor master, purchase orders, goods receipts, vendor bills and
   expenses. Tools reach it over XML-RPC with credentials from an Orchestrate *connection*.
4. **Agents**:
   - The *AP Copilot* serves the finance team and can approve a held bill after confirmation.
   - The *Supplier Desk* serves suppliers. It is read-only and scoped to the caller's GSTIN.
5. **Control plane**: guardrails, PII and IFSC masking, a secrets detector, tool rate limits and a model fallback
   policy. They are attached to the agents and tools in watsonx Orchestrate.

A typical run looks like this:

1. A document arrives by upload, email or chat. The workbench stores it in the tenant's object storage with
   `POST /v1/orchestrate/upload-to-s3` and starts the flow with the returned URL.
2. The flow reads the document, picks its type, and runs that type's nodes. The LLM is used only for judgement:
   the nature of payment for TDS, and the expense category.
3. A decision table routes the result, and a tool node writes to Odoo.
4. The workbench polls the flow instance and shows each node as it completes. It also overlays the extracted
   fields on the document.

LLM-assisted judgement sits inside a deterministic process: every number, GSTIN, policy limit and ERP match is
checked in code. That makes each decision reproducible and auditable, which matters to an auditor.

### Prerequisites

- An [IBM watsonx Orchestrate](https://www.ibm.com/products/watsonx-orchestrate) instance (a trial is fine) and
  an API key for it.
- Python 3.12 and [uv](https://docs.astral.sh/uv/).
- The [watsonx Orchestrate ADK](https://developer.watson-orchestrate.ibm.com/). This tutorial was tested with ADK
  version 2.18.
- An Odoo 18 or later database with the Indian localisation. A free [Odoo trial](https://www.odoo.com/trial)
  works, and the setup script installs the apps it needs.
- Optional: a Gmail account with an app password, for email intake.

### Step 1. Set up the project

In this step, you clone the repository and configure your credentials.

1. Clone the repository and create the virtual environment:

       git clone https://github.com/adiDaBEzt/ImageProcessingPipeline.git
       cd ImageProcessingPipeline
       uv venv -p 3.12 .venv && uv pip install -p .venv -r requirements.txt

2. Copy `.env.example` to `.env` and fill in your Orchestrate instance URL and API key, and your Odoo URL,
   database, user and password. `.env` is git-ignored. Odoo credentials reach Orchestrate only through a
   connection, never through tool code.

3. Connect the ADK to your instance:

       .venv/bin/orchestrate env add -n ap-demo -u "$WXO_INSTANCE_URL" --type ibm_iam
       .venv/bin/orchestrate env activate ap-demo --api-key "$WXO_API_KEY"

### Step 2. Provision the ERP

In this step, you seed Odoo with a small but realistic world for the agent to check against. The script is
idempotent, so you can run it again on a fresh database.

    .venv/bin/python scripts/setup_odoo.py

The script does the following:
- Installs Purchase, Inventory, Employees and Expenses.
- Activates the Indian GST and TDS taxes.
- Configures the buyer company.
- Creates five vendors, each tagged with its TDS section and e-invoicing status and holding a verified bank
  account.
- Creates five purchase orders with goods receipts. One has a deliberate 2-tonne shortage.
- Creates four employees, three with corporate cards, and five expense categories with policy limits.

All of the data comes from one file, `scripts/demo_data.py`. The sample generator, `scripts/generate_samples.py`,
reads the same file, so the 13 sample documents always agree with the ERP.

### Step 3. Build the document flow

In this step, you look at how the flow is assembled with the ADK flow builder. The full source is in
`wxo/flows/ap_document_processing_flow.py`.

1. **Read and classify in one node.** Give the document processing node every schema, and don't force one. It
   extracts the fields and records the matching schema in `metadata.pages_metadata[0].document_type`:

       read = aflow.docproc(
           name="read_document",
           task="text_extraction",
           output_format=DocProcOutputFormat.object,
           enable_hw=True,
           kvp_schemas=[GST_INVOICE_SCHEMA, RECEIPT_SCHEMA, PO_SCHEMA, CHALLAN_SCHEMA],
           kvp_enable_text_hints=True,
       )

   The `document_description` on each schema drives the choice, so be explicit about what each type is *not*.
   Our first taxi receipt was titled "Tax invoice" and was read as a supplier invoice. Describing receipts as
   coming from "a cab operator, hotel, restaurant or merchant … even when titled 'tax invoice'" fixed it.

2. **Branch on the type.** A script node (`identify_document`) maps the detected schema to a type and normalises
   the fields. A branch then routes each type:

       by_type = aflow.branch(name="document_type",
                              evaluator='flow["identify_document"].output.doc_type')
       (by_type.case("supplier_invoice", checks).case("expense_receipt", category)
        .case("purchase_order", verify).case("delivery_challan", receive).case("other", END))

3. **Keep the checks deterministic.** For invoices:
   - a script node runs the GSTIN check digit, the CGST/SGST-versus-IGST regime check and the slab and
     arithmetic checks;
   - a prompt node classifies the nature of payment for TDS;
   - a tool node, `ap_erp_controls`, checks the vendor master, the bank account, duplicates, the IRN, PO price
     and GRN quantity, and computes TDS against live Odoo data.

4. **Put the policy in a decision table.** The table reads the tool's counts and sets the route. The first
   matching rule wins:

       rule("erp_controls", ("duplicates", DecisionsCondition().greater_than(0)), "blocked", "Duplicate invoice")
       rule("erp_controls", ("exceptions", DecisionsCondition().greater_than(0)), "exception", "")
       rule("erp_controls", ("invoice_total", DecisionsCondition().greater_than(2_500_000)), "exception",
            "Above ₹25 lakh touchless limit")

   ![The AP routing policy decision table in the watsonx Orchestrate flow builder.](images/wxo-decision-table.png)

   The AP team can change thresholds such as the ₹25 lakh touchless limit in the flow editor without touching
   code.

5. **Act through tool nodes.** A second branch sends `touchless` to `post_bill`, `exception` to `hold_bill`, and
   `blocked` to the end. The expense path follows the same shape with its own prompt, tool and decision table.

   ![The complete ap_document_processing_flow in the watsonx Orchestrate flow builder, with one lane per document type.](images/wxo-flow-canvas.png)

### Step 4. Deploy to watsonx Orchestrate

In this step, you deploy everything with one script:

    ORCH=.venv/bin/orchestrate ./wxo/deploy.sh

The script does the following, in order:
1. Creates the `odoo_erp` key-value connection.
2. Imports the Python tools. The flow's process tools come first, because the flow resolves their schemas at
   import time.
3. Imports the flow.
4. Adds the `ap_gpt_oss_fallback` model policy.
5. Imports and deploys the two agents.
6. Imports the controls from `wxo/controls/*.yaml`.

Each tool declares the connection it needs, so no credentials appear in tool code:

    @tool(name="ap_erp_controls", permission=ToolPermission.READ_ONLY, expected_credentials=ODOO_CREDENTIALS)
    def ap_erp_controls(invoice: Invoice, payment_nature: PaymentNature, data: dict | None = None) -> ControlOutcome:

**Note:** The parameters use typed Pydantic models rather than `dict`. The tool also accepts an unused `data`
argument, because the flow runtime passes the previous node's output under that name.

### Step 5. Run the workbench and process invoices

In this step, you start the AP workbench and run the supplier-invoice scenarios.

1. Start the app and open http://localhost:8090:

       .venv/bin/uvicorn app.main:app --port 8090

   ![The AP workbench overview: touchless rate, value processed, open exceptions, duplicates blocked, TDS and cycle time.](images/ui-overview.png)

2. Click **Process document**. Drop in any document, or pick a sample scenario and click **Process**.

   ![The Process a document dialog with sample scenarios grouped by document type.](images/ui-process-dialog.png)

3. Process `01_sahyadri…`. The 3-way match passes against the goods receipt, and the bill posts in Odoo with
   CGST and SGST and no human touch.

4. Process `02_kaveri…`. The prompt node classifies a HAZOP study as professional fees. The tool applies TDS under
   Sec 393(1) Sl.6(iii)(b) (formerly 194J) at 10%, ₹41,200, as an Odoo withholding tax.

   ![The Kaveri invoice posted touchless with TDS of ₹41,200 to be withheld at payment.](images/ui-invoice-tds.png)

   The audit trail shows every flow node and how long it took:

   ![Processing trail for the Kaveri invoice, listing each flow node and its duration.](images/ui-flow-trail.png)

5. Process `04_coromandel…`. The supplier charged CGST and SGST on an inter-state supply and changed its bank
   account on the invoice. Both checks fail, and the failing fields are outlined in red on the document.

   ![The Coromandel invoice held for review, with red boxes on the bank details and tax lines.](images/ui-invoice-exception.png)

6. Process `03_narmada…`. Ten tonnes are billed but only eight were received. The **3-way match** tab shows where
   the variance comes from.

   ![3-way match for the Narmada invoice: ordered 10, received 8, quantity variance.](images/ui-three-way-match.png)

7. Process `06_…_scan.png`, a noisy phone scan of invoice 01. It is blocked as a duplicate before any bill exists.

### Step 6. Process receipts, PO copies and challans

In this step, you run the other document types through the same flow.

1. **Expense receipts.**
   - `07_receipt_cityride_taxi` matches Ananya's corporate card ··4821 and is approved without a human touch.
   - `08_receipt_hotel_sabarmati` is ₹9,912 a night against a ₹6,000 limit, so it is held for her manager.
   - `09_receipt_coastal_kitchen` stays within the per-person meals limit.

   The tool also checks GST input-credit eligibility:
   - Food is blocked credit under s.17(5).
   - A Gujarat hotel's GST can't be claimed by a company registered only in Maharashtra.

   ![The hotel receipt held for the manager: ₹9,912 per night against a ₹6,000 limit.](images/ui-expense-hotel.png)

2. **Duplicate claims.** `10_…_photo.jpg` is the same taxi receipt, photographed and submitted by Rahul. It fails
   two checks: it is a duplicate, and the card on it isn't his.

   ![A re-submitted taxi receipt blocked as a duplicate, with the card-owner check failing.](images/ui-expense-duplicate.png)

3. **PO copy.** `11_po_copy…` is a supplier-signed copy of MSC-PO-26-0161. It is verified line by line against
   Odoo, and the result is logged on the PO.

4. **Delivery challan.** `12_challan_narmada…` brings Narmada's missing two tonnes. The agent books the goods
   receipt in Odoo and adds a note to the held Narmada bill: the shortage is resolved, so AP can approve it as
   invoiced.

   ![The delivery challan processed: goods receipt WH/IN/00005 validated and the held bill flagged for release.](images/ui-challan.png)

5. **Anything else.** `13_letter…`, a price-revision letter, matches none of the schemas. It is marked unsupported
   and nothing changes in Odoo.

   ![The Documents list showing every document type and its outcome in Odoo.](images/ui-documents.png)

### Step 7. Review the results in Odoo

In this step, you open the records the agent created. Every one carries the agent's control log as a chatter
note, with failed checks first.

1. Open a posted bill. Odoo shows the GST and TDS taxes on each line, and the agent's control log in the
   chatter.

   ![A vendor bill in Odoo posted touchless with IGST and a 10% TDS withholding tax, with the agent's control log in the chatter.](images/odoo-posted-bill-tds.png)

2. Open a held bill. The review task names the exceptions, and the note lists each check with its detail.

   ![A draft bill in Odoo with the AP exception review task and the agent's control log.](images/odoo-held-bill.png)

3. Open **Expenses**:
   - Company-card spend is approved and settled.
   - Reimbursable spend shows as approved once the manager signs off.

   ![Odoo expenses created by the agent for three employees.](images/odoo-expenses.png)

4. Open the goods receipt booked from the challan. The agent's note records the four receiving checks.

   ![Goods receipt WH/IN/00005 in Odoo with the agent's receiving checks.](images/odoo-goods-receipt.png)

**Note:** When you post chatter notes over XML-RPC, pass `body_is_html=True` to `message_post`. Without it, Odoo
escapes the HTML and the chatter shows raw tags.

### Step 8. Talk to the agents

In this step, you use the two agents. Both are standard watsonx Orchestrate agents that use the same Odoo tools,
with different permissions.

1. In the workbench, open **Assistants**, select the **AP Copilot** and ask:

       Which expense claims are waiting for manager approval, and what is on hold in AP?

   The Copilot calls `expense_claims` and `ap_exception_worklist` and answers with a table and next steps. It can
   approve a held bill, but only after you confirm. It refuses to approve a changed bank account or a duplicate.

   ![The AP Copilot listing held bills with amounts, exceptions and links to Odoo.](images/ui-copilot.png)

2. The same agent works in the Orchestrate agent builder. Note the model: `ap_gpt_oss_fallback`, a model policy
   that uses Groq and falls back to the same model on Bedrock on 429 or 5xx errors.

   ![The AP Copilot in the watsonx Orchestrate agent builder, answering in the preview chat.](images/wxo-agent-builder.png)

3. Select the **Supplier Desk** and ask as a supplier:

       What is the status of invoice KPA/26-27/073? Our GSTIN is 29AAQFK2209M1ZU

   It answers with status, TDS withheld and the expected payment date. It answers only for the GSTIN that owns
   the invoice.

   ![The Supplier Desk answering a supplier's status question.](images/ui-supplier-status.png)

### Step 9. Govern the agents with the control plane

In this step, you look at the controls that apply to every agent call, whatever the prompt says.

1. The controls are defined as YAML in `wxo/controls/` and imported by the deploy script. For example, the
   external channel is screened before the agent sees a message:

       spec_version: v1
       kind: control
       control:
         artifact_name: Content Guardrails
         name: supplier_content_guardrails
         hooks: [agent_pre_invoke]
         agent_names: [supplier_desk_agent]
         config:
           enabled: {jailbreak: true, hap: true, harm: true}
           block_message: I can only help with invoice and payment status for your company.

   ![The Supplier Desk controls on the watsonx Orchestrate Controls page.](images/wxo-controls.png)

2. Open **Governance** in the workbench. It reads the controls from the tenant and shows where each one runs: on
   input, on tool calls, on output, or at the model.

   ![The workbench Governance page showing the active controls and where each runs.](images/ui-governance.png)

3. Click **Try a jailbreak on Supplier Desk**. The guardrail blocks the message before the agent runs, and the
   chat marks the reply **Blocked by control**.

   ![A jailbreak attempt on the Supplier Desk blocked by the content guardrail.](images/ui-guardrail-blocked.png)

**Note:** The guardrail screens the whole conversation. Once a thread contains a jailbreak attempt, later messages
in that thread are blocked too, so the user needs to start a new conversation.

### Lessons from building it

- **The detected type is in the metadata.** With several KVP schemas and no forced schema, document processing
  reports the match in `metadata.pages_metadata[0].document_type`.
- **Qualify decision-table variables.** Conditions take `flow["node"].output.field`. Actions write to an existing
  variable such as `flow.output.route`, and the branch evaluates that same variable.
- **Map every flow output explicitly.** If a branch doesn't set an output, the runtime tries to map it
  automatically, and that can fail. Give each output an explicit map with a default value.
- **Use a non-zero temperature for near-greedy output.** A prompt node's temperature of `0` is dropped as falsy.
  Use `0.01`.
- **Model fallback is a model policy.** Model-level controls bind to custom models, so the fallback is set up with
  `orchestrate models policy add`, and the agents reference `virtual-policy/<name>`.

### Summary and next steps

You built an accounts-payable agent that:
- recognises five kinds of document;
- runs the India-specific checks that usually stay manual;
- acts in Odoo through one auditable flow.

Agents do the conversational work for the AP team and suppliers, and the control plane governs them without
changing their prompts. In our runs a document went from upload to an Odoo decision in about 30 to 40 seconds.

You can extend the solution in the following ways:

- **Another ERP:** replace the Odoo client in `apcore/odoo.py` with SAP S/4HANA OData calls. The flow,
  decision tables and agents stay the same.
- **More document types:** add a schema to the document processing node and a lane to the branch. Credit notes
  and debit notes are natural next steps.
- **Human in the loop inside the flow:** route exceptions to a user-activity node, so approvals happen in
  Orchestrate chat.
- **Payment runs:** add a scheduled flow that proposes the payment batch, with TDS already withheld on each bill.

The complete source, sample documents and Odoo provisioning script are in the
[GitHub repository](https://github.com/adiDaBEzt/ImageProcessingPipeline).
