"""Provision an Odoo database as the ERP backend for the AP agent. Idempotent.

    python scripts/setup_odoo.py

1. Installs Purchase + Inventory (needed for POs and goods receipts / GRNs)
2. Activates India GST (with ITC) and TDS purchase taxes shipped by l10n_in
3. Configures the buyer company (name, GSTIN, Maharashtra address)
4. Creates the vendor master: GSTIN, bank account, TDS / e-invoice policy tags
5. Creates products with HSN/SAC codes, confirms POs and books receipts (incl. a short GRN)
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import app  # noqa: E402,F401  (puts the apcore engine on the path)

from apcore.india import TAG_EINVOICE, TAG_TDS_PREFIX, TDS_RULES  # noqa: E402
from apcore.odoo import Odoo, OdooError  # noqa: E402
from app import config  # noqa: E402
from scripts.demo_data import BUYER, PRODUCTS, PURCHASE_ORDERS, VENDORS, vendor  # noqa: E402

odoo = Odoo(config.ODOO_URL, config.ODOO_DB, config.ODOO_USERNAME, config.ODOO_PASSWORD)
NO_ACTIVE_TEST = {"context": {"active_test": False}}


def step(msg):
    print(f"\n▸ {msg}")


def install_modules(names):
    for name in names:
        for attempt in range(4):
            mod = odoo.search_read("ir.module.module", [("name", "=", name)], ["state"])[0]
            if mod["state"] == "installed":
                print(f"  {name}: installed")
                break
            try:
                odoo.call("ir.module.module", "button_immediate_install", [mod["id"]])
            except OdooError as e:  # Odoo SaaS occasionally races on its registry signal table
                print(f"  {name}: retrying ({e})")
                time.sleep(5)


def activate_taxes():
    names = ["5% GST P", "18% GST P", "40% GST P", "5% IGST P", "18% IGST P", "40% IGST P"]
    names += [r["odoo_tax"] for r in TDS_RULES.values()]
    taxes = odoo.search_read("account.tax", [("name", "in", names), ("type_tax_use", "=", "purchase")],
                             ["id", "name", "children_tax_ids"], **NO_ACTIVE_TEST)
    ids = [t["id"] for t in taxes] + [c for t in taxes for c in t["children_tax_ids"]]
    odoo.call("account.tax", "write", ids, {"active": True})
    missing = set(names) - {t["name"] for t in taxes}
    print(f"  activated {len(ids)} taxes" + (f"; not found: {sorted(missing)}" if missing else ""))


def state_id(code):
    return odoo.search_read("res.country.state", [("country_id.code", "=", "IN"), ("code", "=", code)], ["id"])[0]["id"]


def india_id():
    return odoo.search_read("res.country", [("code", "=", "IN")], ["id"])[0]["id"]


def configure_company():
    company = odoo.company()
    odoo.call("res.company", "write", [company["id"]], {
        "name": BUYER["name"], "vat": BUYER["gstin"], "street": BUYER["street"], "city": BUYER["city"],
        "zip": BUYER["zip"], "state_id": state_id(BUYER["state"]), "country_id": india_id(),
        "email": BUYER["email"], "l10n_in_tds_feature": True,  # TDS withheld at payment time
    })
    print(f"  {BUYER['name']} · GSTIN {BUYER['gstin']}")


def tag(name):
    ids = odoo.call("res.partner.category", "search", [("name", "=", name)], limit=1)
    return ids[0] if ids else odoo.call("res.partner.category", "create", {"name": name})


def upsert_vendors():
    clearing = odoo.call("clearing.label", "search", [], limit=1)
    net30 = odoo.call("account.payment.term", "search", [("name", "=", "30 Days")], limit=1)
    for v in VENDORS:
        tags = []
        if v["einvoice"]:
            tags.append(tag(TAG_EINVOICE))
        if v["tds"]:
            tags.append(tag(f"{TAG_TDS_PREFIX}{TDS_RULES[v['tds']]['label']}"))
        vals = {
            "name": v["name"], "is_company": True, "vat": v["gstin"], "street": v["street"], "city": v["city"],
            "zip": v["zip"], "state_id": state_id(v["state"]), "country_id": india_id(), "email": v["email"],
            "supplier_rank": 1, "l10n_in_gst_treatment": "regular", "category_id": [(6, 0, tags)],
            "property_supplier_payment_term_id": net30[0] if net30 else False,
        }
        existing = odoo.call("res.partner", "search", [("vat", "=", v["gstin"])], limit=1)
        pid = existing[0] if existing else odoo.call("res.partner", "create", vals)
        if existing:
            odoo.call("res.partner", "write", [pid], vals)
        bank = v["bank"]
        if not odoo.call("res.partner.bank", "search", [("partner_id", "=", pid), ("account_number", "=", bank["account"])]):
            bank_vals = {"partner_id": pid, "account_number": bank["account"], "bank_name": bank["name"],
                         "bank_bic": bank["ifsc"], "allow_out_payment": True}
            try:
                odoo.call("res.partner.bank", "create", bank_vals)
            except OdooError:
                odoo.call("res.partner.bank", "create", {**bank_vals, "clearing_label_id": clearing[0]})
        v["odoo_id"] = pid
        print(f"  {v['name']} (#{pid}) · {v['gstin']} · TDS={v['tds'] or '—'} · e-invoice={v['einvoice']}")


def upsert_products():
    uoms = {u["name"]: u["id"] for u in odoo.search_read("uom.uom", [], ["name"])}
    ids = {}
    for key, (name, hsn, kind, uom, _rate) in PRODUCTS.items():
        existing = odoo.search_read("product.product", [("default_code", "=", f"MSC-{key.upper()}")], ["id"])
        vals = {
            "name": name, "default_code": f"MSC-{key.upper()}", "type": "consu" if kind == "goods" else "service",
            "purchase_method": "receive", "l10n_in_hsn_code": hsn, "uom_id": uoms.get(uom, uoms["Units"]),
            "supplier_taxes_id": [(6, 0, [])], "taxes_id": [(6, 0, [])],
        }
        if kind == "goods":
            vals["is_storable"] = True
        if existing:
            ids[key] = existing[0]["id"]
        else:
            tmpl = odoo.call("product.template", "create", vals)
            ids[key] = odoo.search_read("product.product", [("product_tmpl_id", "=", tmpl)], ["id"])[0]["id"]
    print(f"  {len(ids)} products with HSN/SAC")
    return ids


def create_purchase_orders(product_ids):
    company_state = BUYER["state"]
    for spec in PURCHASE_ORDERS:
        v = vendor(spec["vendor"])
        if not odoo.call("purchase.order", "search", [("name", "=", spec["name"])]):
            gst = odoo.tax_id("18% GST P" if v["state"] == company_state else "18% IGST P")
            po_id = odoo.call("purchase.order", "create", {
                "name": spec["name"], "partner_id": v["odoo_id"], "date_order": f"{spec['date']} 10:00:00",
                "order_line": [(0, 0, {"product_id": product_ids[p], "product_qty": qty, "price_unit": price,
                                       "tax_ids": [(6, 0, [gst])]}) for p, qty, price, _rcv in spec["lines"]],
            })
            odoo.call("purchase.order", "button_confirm", [po_id])
        po = odoo.purchase_order(spec["name"])
        received = {product_ids[p]: rcv for p, _q, _pr, rcv in spec["lines"]}

        # Services: record the accepted quantity (service entry) on the PO line.
        for line in po["lines"]:
            kind = next(PRODUCTS[k][2] for k, pid in product_ids.items() if pid == line["product_id"][0])
            if kind == "service":
                odoo.call("purchase.order.line", "write", [line["id"]], {"qty_received": received[line["product_id"][0]]})

        # Goods: validate the incoming receipt (GRN) with the physically received quantity.
        for picking in [r for r in po["receipts"] if r["state"] not in ("done", "cancel")]:
            if any(r["state"] == "done" for r in po["receipts"]):
                continue  # open backorder for the short-shipped quantity stays open
            moves = odoo.search_read("stock.move", [("picking_id.name", "=", picking["name"])], ["id", "product_id"])
            for mv in moves:
                odoo.call("stock.move", "write", [mv["id"]], {"quantity": received[mv["product_id"][0]], "picked": True})
            odoo.call("stock.picking", "button_validate", [odoo.call("stock.picking", "search", [("name", "=", picking["name"])])[0]],
                      context={"skip_backorder": True})
        po = odoo.purchase_order(spec["name"])
        summary = ", ".join(f"{l['qty_received']:g}/{l['product_qty']:g}" for l in po["lines"])
        print(f"  {spec['name']} → {v['name']} · received {summary} · GRN {[r['name'] for r in po['receipts']]}")


if __name__ == "__main__":
    print(f"Odoo: {odoo.url} / {odoo.db}")
    step("Installing Purchase + Inventory"); install_modules(["purchase", "stock"])
    step("Activating GST & TDS taxes"); activate_taxes()
    step("Configuring buyer company"); configure_company()
    step("Vendor master"); upsert_vendors()
    step("Products"); pids = upsert_products()
    step("Purchase orders & receipts"); create_purchase_orders(pids)
    print("\nDone.")
