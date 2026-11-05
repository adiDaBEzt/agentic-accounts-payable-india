#!/usr/bin/env bash
# Deploy the AP agent assets to the active watsonx Orchestrate environment.
#   orchestrate env add -n <name> -u <WXO_INSTANCE_URL> --type ibm_iam
#   orchestrate env activate <name> --api-key <WXO_API_KEY>
#   ./wxo/deploy.sh
set -euo pipefail
cd "$(dirname "$0")"
set -a; source ../.env; set +a
ORCH=${ORCH:-orchestrate}

echo "▸ Connection: odoo_erp (key-value, team credentials)"
$ORCH connections add -a odoo_erp >/dev/null 2>&1 || true
for env in draft live; do
  $ORCH connections configure -a odoo_erp --env "$env" -t team -k key_value >/dev/null
  $ORCH connections set-credentials -a odoo_erp --env "$env" \
    -e "url=$ODOO_URL" -e "db=$ODOO_DB" -e "username=$ODOO_USERNAME" -e "password=$ODOO_PASSWORD" >/dev/null
done

echo "▸ Flow: ap_invoice_extraction_flow"
$ORCH tools import -k flow -f flows/ap_invoice_extraction_flow.py

echo "▸ Tools (Odoo via connection)"
for f in ap_copilot_tools.py supplier_tools.py; do
  $ORCH tools import -k python -f "tools/$f" -p tools -r tools/requirements.txt -a odoo_erp
done

echo "▸ Agents"
$ORCH agents import -f agents/supplier_desk_agent.yaml
$ORCH agents import -f agents/ap_copilot_agent.yaml
$ORCH agents deploy -n supplier_desk_agent >/dev/null 2>&1 || true
$ORCH agents deploy -n ap_copilot_agent >/dev/null 2>&1 || true
echo "Done."
