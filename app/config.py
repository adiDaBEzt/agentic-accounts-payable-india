"""Runtime configuration, read once from the environment / project .env file."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "documents"
SAMPLES_DIR = ROOT / "samples"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")

WXO_INSTANCE_URL = os.environ.get("WXO_INSTANCE_URL", "").rstrip("/")
WXO_API_KEY = os.environ.get("WXO_API_KEY", "")
WXO_FLOW_NAME = os.environ.get("WXO_FLOW_NAME", "ap_invoice_extraction_flow")
WXO_COPILOT_AGENT = os.environ.get("WXO_COPILOT_AGENT", "ap_copilot_agent")
WXO_SUPPLIER_AGENT = os.environ.get("WXO_SUPPLIER_AGENT", "supplier_desk_agent")

ODOO_URL = os.environ.get("ODOO_URL", "")
ODOO_DB = os.environ.get("ODOO_DB", "")
ODOO_USERNAME = os.environ.get("ODOO_USERNAME", "")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD", "")

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
GMAIL_POLL_SECONDS = int(os.environ.get("GMAIL_POLL_SECONDS", "0") or 0)
VENDOR_EMAIL_OVERRIDE = os.environ.get("VENDOR_EMAIL_OVERRIDE", "")

# AP policy knobs
PRICE_TOLERANCE_PCT = float(os.environ.get("PRICE_TOLERANCE_PCT", "2.0"))
AMOUNT_TOLERANCE_INR = float(os.environ.get("AMOUNT_TOLERANCE_INR", "1.0"))

for d in (DATA_DIR, UPLOAD_DIR):
    d.mkdir(parents=True, exist_ok=True)
