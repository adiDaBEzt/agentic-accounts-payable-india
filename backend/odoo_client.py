"""
Odoo Cloud ERP Client for Accounts Payable (Vendor Bills).

Uses Odoo's standard XML-RPC Web Services API (/xmlrpc/2/common and /xmlrpc/2/object)
to automatically create vendor partners and post vendor bills with line items.
"""

import os
import xmlrpc.client
from typing import Any, Dict, List, Optional, Tuple

# Load optional .env file if available
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r") as _ef:
        for _line in _ef:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())


class OdooClient:
    def __init__(
        self,
        url: Optional[str] = None,
        db: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.url = (url or os.environ.get("ODOO_URL", "https://invoiceprocessing.odoo.com")).rstrip("/")
        self.db = db or os.environ.get("ODOO_DB", "invoiceprocessing")
        self.username = username or os.environ.get("ODOO_USERNAME", "odoo-user@example.com")
        self.password = password or os.environ.get("ODOO_PASSWORD", "")
        self._uid: Optional[int] = None

    def get_uid(self) -> int:
        """Authenticate with Odoo and return user ID."""
        if self._uid:
            return self._uid
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        uid = common.authenticate(self.db, self.username, self.password, {})
        if not uid:
            raise RuntimeError(f"Odoo authentication failed for user '{self.username}' on db '{self.db}'")
        self._uid = uid
        return uid

    def _object_proxy(self) -> xmlrpc.client.ServerProxy:
        return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def find_or_create_partner(self, name: str, email: str = "", address: str = "") -> int:
        """Lookup existing contact or create new vendor partner."""
        name_clean = (name or "Unknown Vendor").strip()
        uid = self.get_uid()
        models = self._object_proxy()

        partner_ids = models.execute_kw(
            self.db, uid, self.password, "res.partner", "search", [[["name", "=", name_clean]]]
        )
        if partner_ids:
            return partner_ids[0]

        vals: Dict[str, Any] = {"name": name_clean, "supplier_rank": 1}
        if email:
            vals["email"] = email
        if address:
            vals["street"] = address

        new_id = models.execute_kw(self.db, uid, self.password, "res.partner", "create", [vals])
        return new_id

    def create_vendor_bill(
        self,
        invoice_number: str,
        vendor_name: str,
        invoice_date: str = "",
        due_date: str = "",
        currency: str = "USD",
        line_items: Optional[List[Dict[str, Any]]] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Post a new Vendor Bill (`account.move` with `move_type='in_invoice'`)
        including individual item lines into Odoo.
        """
        uid = self.get_uid()
        models = self._object_proxy()

        partner_id = self.find_or_create_partner(vendor_name)

        # Build Odoo line items format: (0, 0, {name, quantity, price_unit})
        lines_payload = []
        for item in line_items or []:
            desc = item.get("description") or "Item"
            qty = float(item.get("quantity") or 1.0)
            price = float(item.get("unit_price") or item.get("amount") or 0.0)
            lines_payload.append(
                (
                    0,
                    0,
                    {
                        "name": desc,
                        "quantity": qty,
                        "price_unit": price,
                    },
                )
            )

        bill_vals: Dict[str, Any] = {
            "move_type": "in_invoice",
            "partner_id": partner_id,
            "ref": invoice_number,
            "invoice_line_ids": lines_payload,
        }
        if invoice_date:
            bill_vals["invoice_date"] = invoice_date
        if due_date:
            bill_vals["invoice_date_due"] = due_date
        if notes:
            bill_vals["narration"] = notes

        bill_id = models.execute_kw(
            self.db, uid, self.password, "account.move", "create", [bill_vals]
        )

        read_res = models.execute_kw(
            self.db,
            uid,
            self.password,
            "account.move",
            "read",
            [[bill_id]],
            {"fields": ["id", "name", "ref", "amount_total", "state", "invoice_date", "partner_id"]},
        )
        bill_data = read_res[0] if read_res else {"id": bill_id}
        bill_data["odoo_url"] = f"{self.url}/web#id={bill_id}&model=account.move&view_type=form"
        return bill_data

    def list_vendor_bills(self, limit: int = 15) -> List[Dict[str, Any]]:
        """List recently created vendor bills from Odoo."""
        uid = self.get_uid()
        models = self._object_proxy()
        bills = models.execute_kw(
            self.db,
            uid,
            self.password,
            "account.move",
            "search_read",
            [[["move_type", "=", "in_invoice"]]],
            {
                "fields": [
                    "id",
                    "name",
                    "ref",
                    "partner_id",
                    "amount_total",
                    "state",
                    "invoice_date",
                    "invoice_date_due",
                    "create_date",
                ],
                "limit": limit,
                "order": "id desc",
            },
        )
        for b in bills:
            b["odoo_url"] = f"{self.url}/web#id={b['id']}&model=account.move&view_type=form"
            if isinstance(b.get("partner_id"), (list, tuple)):
                b["vendor_name"] = b["partner_id"][1]
            else:
                b["vendor_name"] = "Unknown Vendor"
        return bills

    def post_vendor_bill(self, bill_id: int, fallback_date: str = "2026-10-21") -> Dict[str, Any]:
        """
        Confirm / Post a Draft Vendor Bill in Odoo (`account.move.action_post`),
        transitioning its state from 'draft' to 'posted' and assigning an official
        accounting sequence number (e.g. BILL/26-27/10/0001).
        """
        uid = self.get_uid()
        models = self._object_proxy()

        existing = models.execute_kw(
            self.db,
            uid,
            self.password,
            "account.move",
            "read",
            [[bill_id]],
            {"fields": ["id", "state", "invoice_date"]},
        )
        if not existing:
            raise RuntimeError(f"Odoo Vendor Bill #{bill_id} not found")

        bill_info = existing[0]
        if not bill_info.get("invoice_date"):
            models.execute_kw(
                self.db,
                uid,
                self.password,
                "account.move",
                "write",
                [[bill_id], {"invoice_date": fallback_date or "2026-10-21"}],
            )

        if bill_info.get("state") == "draft":
            try:
                models.execute_kw(
                    self.db, uid, self.password, "account.move", "action_post", [[bill_id]]
                )
            except xmlrpc.client.Fault as fault:
                # Odoo XML-RPC action_post returns None in Python which may raise Marshaller Fault even when succeeded
                if "cannot marshal None" not in str(fault):
                    raise

        read_res = models.execute_kw(
            self.db,
            uid,
            self.password,
            "account.move",
            "read",
            [[bill_id]],
            {"fields": ["id", "name", "ref", "amount_total", "state", "invoice_date", "partner_id"]},
        )
        bill_data = read_res[0] if read_res else {"id": bill_id, "state": "posted"}
        bill_data["odoo_url"] = f"{self.url}/web#id={bill_id}&model=account.move&view_type=form"
        return bill_data
