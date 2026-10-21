# IBM watsonx Orchestrate — Intelligent Document Processing (IDP) Client Package

A standalone, client-ready package demonstrating Intelligent Document Processing (IDP) with **IBM watsonx Orchestrate**, featuring Watson Document Understanding (WDU), Deterministic Python Logic, and Generative AI.

---

## What Is in This Package

- **`SETUP_AND_ARCHITECTURE_GUIDE.md`**: Complete, presentation-grade documentation detailing the architecture, how `docproc` OCR works, how to build and deploy the Flow and Agent, and how to acquire tenant credentials.
- **`flow/invoice_idp_flow.py`**: The original, tested Python ADK definition for `invoice_idp_flow` (Flow ID: `513e67d6-2974-4776-a0ac-5869876bee9a`).
- **`agent/invoice_agent.yaml`**: The agent configuration for `invoice_idp_agent` (Agent ID: `23215e30-2f2f-4373-974b-0d7bb89e657a`).
- **`samples/`**: 5 pre-generated test documents (Invoices, Purchase Orders, Receipts) in both PDF and PNG formats.
- **`app.py` & `frontend/`**: A lightweight, standalone web dashboard (FastAPI + Carbon Design System) with zero external ERP or email dependencies.
- **`run_demo.sh`**: One-click startup script.

---

## Quick Start (3 Steps)

### 1. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure your IBM Cloud API key and tenant URL are set in `.env`.

### 2. Launch the Application
```bash
./run_demo.sh
```
*(Or install dependencies via `pip install -r requirements.txt` and run `python app.py`).*

### 3. Open the Dashboard
Navigate to:
```
http://127.0.0.1:8000
```

Select any pre-loaded sample document (or drag & drop your own PDF) and click **"Upload to wxO S3 & Run IDP Pipeline"**.
