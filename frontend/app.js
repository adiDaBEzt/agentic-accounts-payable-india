/**
 * Enterprise AP & Multi-Document IDP Command Center Controller
 *
 * Implements:
 * 1. CFO Spend Analytics & General Ledger (GL) Allocation Breakdown Bar
 * 2. Interactive WDU `docproc` Visual Bounding-Box Overlay Canvas (2-way hover highlight)
 * 3. Automated 2-Way Purchase Order (PO) vs. Invoice Line-Item Matching Engine
 * 4. 6-Point Fraud, Duplicate & Split-Invoice Risk Shield
 * 5. Human-in-the-Loop (HITL) Approval Workbench:
 *    - One-click Approve & Post Vendor Bill in Odoo (`account.move.action_post`)
 *    - Inline Field Override Editor (`<dialog closedby="any">`)
 *    - One-click Reject & Send Vendor Dispute Email via Gmail SMTP (`<dialog closedby="any">`)
 */

const state = {
  selectedFile: null,
  selectedSampleFilename: "clean_invoices/invoice_acme_cloud_0042.png",
  executionMode: "direct_flow",
  activeInvoice: null,
  invoices: [],
  analytics: null,
  healthInfo: null,
};

// DOM Elements
const tenantStatusText = document.getElementById("tenantStatusText");
const modeCardDirect = document.getElementById("modeCardDirect");
const modeCardAgent = document.getElementById("modeCardAgent");
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const dropzoneTitle = document.getElementById("dropzoneTitle");
const dropzoneHint = document.getElementById("dropzoneHint");
const sampleButtonsContainer = document.getElementById("sampleButtonsContainer");
const runPipelineBtn = document.getElementById("runPipelineBtn");
const runBtnLabel = document.getElementById("runBtnLabel");
const telemetryElapsed = document.getElementById("telemetryElapsed");
const telemetrySteps = document.getElementById("telemetrySteps");

// CFO Analytics Ribbon Elements
const kpiTotalSpend = document.getElementById("kpiTotalSpend");
const kpiDocMix = document.getElementById("kpiDocMix");
const kpiStpRate = document.getElementById("kpiStpRate");
const kpiVpCount = document.getElementById("kpiVpCount");
const kpiOdooSynced = document.getElementById("kpiOdooSynced");
const kpiAvgConf = document.getElementById("kpiAvgConf");
const glProgressBar = document.getElementById("glProgressBar");
const glLegend = document.getElementById("glLegend");

// Active Result Card & Workbench Elements
const activeInvoiceSubtitle = document.getElementById("activeInvoiceSubtitle");
const activeRiskBadge = document.getElementById("activeRiskBadge");
const activeConfidenceBadge = document.getElementById("activeConfidenceBadge");
const openInspectorModalBtn = document.getElementById("openInspectorModalBtn");
const emptyStateBox = document.getElementById("emptyStateBox");
const invoiceDetailsContainer = document.getElementById("invoiceDetailsContainer");

const hitlTierBadge = document.getElementById("hitlTierBadge");
const hitlOdooBadge = document.getElementById("hitlOdooBadge");
const approvePostOdooBtn = document.getElementById("approvePostOdooBtn");
const openEditFieldsBtn = document.getElementById("openEditFieldsBtn");
const openDisputeModalBtn = document.getElementById("openDisputeModalBtn");

const tabPoStatusPill = document.getElementById("tabPoStatusPill");
const tabApAutoPill = document.getElementById("tabApAutoPill");
const tabRiskScorePill = document.getElementById("tabRiskScorePill");

// Visual Grounding Canvas & Fields
const docPreviewImg = document.getElementById("docPreviewImg");
const docBboxSvg = document.getElementById("docBboxSvg");
const bboxHoverStatus = document.getElementById("bboxHoverStatus");
const structuredHeaderGrid = document.getElementById("structuredHeaderGrid");
const validationBanner = document.getElementById("validationBanner");
const lineItemsTbody = document.getElementById("lineItemsTbody");

// PO Matching, Step PO, AP Automation & Risk Shield Panels
const poSummaryBanner = document.getElementById("poSummaryBanner");
const poKpiStrip = document.getElementById("poKpiStrip");
const stepPoSection = document.getElementById("stepPoSection");
const poLinesTbody = document.getElementById("poLinesTbody");
const apAutoBanner = document.getElementById("apAutoBanner");
const apWaterfallGrid = document.getElementById("apWaterfallGrid");
const apActionInfo = document.getElementById("apActionInfo");
const executeApRunBtn = document.getElementById("executeApRunBtn");
const apJournalTbody = document.getElementById("apJournalTbody");
const riskOverviewHeader = document.getElementById("riskOverviewHeader");
const riskChecksGrid = document.getElementById("riskChecksGrid");

// SQLite Table
const dbRecordCount = document.getElementById("dbRecordCount");
const sqliteInvoicesTbody = document.getElementById("sqliteInvoicesTbody");

// Dialogs
const rawInspectorDialog = document.getElementById("rawInspectorDialog");
const dialogS3Url = document.getElementById("dialogS3Url");
const dialogFlowId = document.getElementById("dialogFlowId");
const dialogAgentId = document.getElementById("dialogAgentId");
const dialogThreadId = document.getElementById("dialogThreadId");
const dialogRawKvpsTbody = document.getElementById("dialogRawKvpsTbody");
const dialogOcrText = document.getElementById("dialogOcrText");

const editFieldsDialog = document.getElementById("editFieldsDialog");
const editFieldsForm = document.getElementById("editFieldsForm");
const cancelEditFieldsBtn = document.getElementById("cancelEditFieldsBtn");

const disputeDialog = document.getElementById("disputeDialog");
const disputeForm = document.getElementById("disputeForm");
const cancelDisputeBtn = document.getElementById("cancelDisputeBtn");

// Mandatory fallback for browsers without native <dialog closedby="any"> support (e.g. Safari)
[rawInspectorDialog, editFieldsDialog, disputeDialog].forEach((dlg) => {
  if (dlg && !("closedBy" in HTMLDialogElement.prototype)) {
    dlg.addEventListener("click", (event) => {
      if (event.target !== dlg) return;
      const rect = dlg.getBoundingClientRect();
      const isDialogContent =
        rect.top <= event.clientY &&
        event.clientY <= rect.top + rect.height &&
        rect.left <= event.clientX &&
        event.clientX <= rect.left + rect.width;
      if (isDialogContent) return;
      dlg.close();
    });
  }
});

// Workbench Tab Switching
document.querySelectorAll(".wb-tab").forEach((tabBtn) => {
  tabBtn.addEventListener("click", () => {
    const targetId = tabBtn.dataset.tab;
    document.querySelectorAll(".wb-tab").forEach((b) => {
      const isActive = b === tabBtn;
      b.classList.toggle("active", isActive);
      b.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    document.querySelectorAll(".wb-tab-panel").forEach((panel) => {
      const match = panel.id === targetId;
      panel.classList.toggle("active", match);
      panel.hidden = !match;
    });
  });
});

openInspectorModalBtn.addEventListener("click", () => {
  if (!state.activeInvoice) return;
  populateInspectorDialog(state.activeInvoice);
  rawInspectorDialog.showModal();
});

// Mode selector radio handling
document.querySelectorAll('input[name="execution_mode"]').forEach((radio) => {
  radio.addEventListener("change", (e) => {
    state.executionMode = e.target.value;
    modeCardDirect.classList.toggle("active", state.executionMode === "direct_flow");
    modeCardAgent.classList.toggle("active", state.executionMode === "agent_two_turn");
    runBtnLabel.textContent =
      state.executionMode === "direct_flow"
        ? "Upload to wxO S3 & Run Direct IDP Flow"
        : "Upload to wxO S3 & Run 2-Turn IDP Agent";
  });
});

// Drag & Drop / File input handling
dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    selectLocalFile(e.dataTransfer.files[0]);
  }
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files && e.target.files.length > 0) {
    selectLocalFile(e.target.files[0]);
  }
});

function selectLocalFile(file) {
  state.selectedFile = file;
  state.selectedSampleFilename = null;
  dropzoneTitle.textContent = `Selected Upload: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  dropzoneHint.textContent = "Ready to upload to /v1/orchestrate/upload-to-s3";
  document.querySelectorAll(".sample-btn").forEach((btn) => btn.classList.remove("selected"));
}

function selectSampleInvoice(filename, label) {
  state.selectedFile = null;
  state.selectedSampleFilename = filename;
  dropzoneTitle.textContent = `Selected Sample: ${filename}`;
  dropzoneHint.textContent = `${label} — Click 'Upload to wxO S3 & Run' below`;
  document.querySelectorAll(".sample-btn").forEach((btn) => {
    btn.classList.toggle("selected", btn.dataset.filename === filename);
  });
}

async function refreshInvoicesList(preserveActiveId = null) {
  const invoicesRes = await fetch("/api/invoices");
  if (!invoicesRes.ok) return;
  const { invoices, analytics } = await invoicesRes.json();
  state.invoices = invoices || [];
  if (analytics) {
    state.analytics = analytics;
    renderCfoAnalytics(analytics);
  }
  renderSqliteTable();
  if (preserveActiveId) {
    const found = state.invoices.find((x) => x.id === preserveActiveId);
    if (found) setActiveInvoice(found);
  } else if (!state.activeInvoice && state.invoices.length > 0) {
    setActiveInvoice(state.invoices[0]);
  }
}

async function initApp() {
  try {
    const [healthRes, samplesRes] = await Promise.all([
      fetch("/api/health"),
      fetch("/api/samples"),
    ]);

    if (healthRes.ok) {
      state.healthInfo = await healthRes.json();
      tenantStatusText.textContent = `Connected: ca-tor | Flow ${state.healthInfo.flow_id.slice(0, 8)}... | Odoo ERP Active`;
    }

    if (samplesRes.ok) {
      const { samples } = await samplesRes.json();
      renderSampleButtons(samples);
    }

    await refreshInvoicesList();
  } catch (err) {
    tenantStatusText.textContent = `Backend Error: ${err.message}`;
  }
}

function renderCfoAnalytics(analytics) {
  if (!analytics) return;
  const fmtUsd = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
  kpiTotalSpend.textContent = fmtUsd.format(analytics.total_spend_usd || 0);
  kpiDocMix.textContent = `${analytics.invoice_count || 0} Invoices • ${analytics.po_count || 0} POs • ${analytics.receipt_count || 0} Receipts`;
  kpiStpRate.textContent = `${analytics.stp_rate_pct || 0}%`;
  kpiVpCount.textContent = `${analytics.vp_review_count || 0} Pending Review • ${analytics.disputed_count || 0} Disputed`;
  kpiOdooSynced.textContent = `${analytics.odoo_synced_count || 0} / ${analytics.total_documents || 0} Bills`;
  kpiAvgConf.textContent = `${analytics.avg_confidence_pct || 98.5}%`;

  const breakdown = analytics.gl_breakdown || [];
  if (breakdown.length === 0) {
    glProgressBar.innerHTML = `<div class="gl-segment" style="width:100%;background:#cbd5e1;"></div>`;
    glLegend.innerHTML = `<span>No GL line-item spend recorded yet</span>`;
    return;
  }

  glProgressBar.innerHTML = breakdown
    .map(
      (g) =>
        `<div class="gl-segment" style="width:${Math.max(g.pct, 3)}%;background:${g.color};" title="${escapeHtml(g.category)}: ${fmtUsd.format(g.amount_usd)} (${g.pct}%)"></div>`
    )
    .join("");

  glLegend.innerHTML = breakdown
    .map(
      (g) => `
      <span class="gl-legend-item">
        <span class="gl-dot" style="background:${g.color};"></span>
        <span><strong>${escapeHtml(g.category)}:</strong> ${fmtUsd.format(g.amount_usd)} (${g.pct}%)</span>
      </span>
    `
    )
    .join("");
}

function renderSampleButtons(samples) {
  sampleButtonsContainer.innerHTML = "";

  // Group by category / subfolder
  const groups = {};
  samples.forEach((s) => {
    const key = s.subfolder || "clean_invoices";
    if (!groups[key]) {
      groups[key] = {
        title: s.category || key.replace(/_/g, " ").toUpperCase(),
        subfolder: key,
        items: [],
      };
    }
    groups[key].items.push(s);
  });

  const groupOrder = ["clean_invoices", "variance_invoices", "purchase_orders", "receipts"];
  const sortedKeys = Object.keys(groups).sort((a, b) => {
    const ia = groupOrder.indexOf(a);
    const ib = groupOrder.indexOf(b);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });

  sortedKeys.forEach((key) => {
    const g = groups[key];
    const groupDiv = document.createElement("div");
    groupDiv.className = "sample-group";

    let icon = "📄";
    let badgeColor = "#0f62fe";
    let badgeLabel = `${g.items.length} files`;
    if (g.subfolder === "clean_invoices") {
      icon = "✅";
      badgeColor = "#198038";
      badgeLabel = "100% PO Match & STP";
    } else if (g.subfolder === "variance_invoices") {
      icon = "⚠️";
      badgeColor = "#da1e28";
      badgeLabel = "PO Variance Exception";
    } else if (g.subfolder === "purchase_orders") {
      icon = "📋";
      badgeColor = "#007d79";
      badgeLabel = "Authoritative PO";
    } else if (g.subfolder === "receipts") {
      icon = "🧾";
      badgeColor = "#8a3ffc";
      badgeLabel = "Corporate T&E";
    }

    const titleEl = document.createElement("div");
    titleEl.className = "sample-group-title";
    titleEl.innerHTML = `
      <span>${icon} <strong>${escapeHtml(g.title)}</strong></span>
      <span class="badge-tag" style="background:${badgeColor}15;color:${badgeColor};border:1px solid ${badgeColor}40;">${badgeLabel}</span>
    `;
    groupDiv.appendChild(titleEl);

    g.items.forEach((s) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `sample-btn ${s.png_filename === state.selectedSampleFilename || s.raw_filename === state.selectedSampleFilename ? "selected" : ""}`;
      btn.dataset.filename = s.png_filename;
      const typeTag = s.doc_type || "Invoice";
      const label = `[${typeTag}] ${s.invoice_number} — ${s.vendor_name} (${s.currency} ${s.total_amount})`;
      btn.innerHTML = `
        <span><strong>${escapeHtml(s.invoice_number)}:</strong> ${escapeHtml(s.vendor_name)} <span style="color:#64748b;">(${escapeHtml(s.currency)} ${escapeHtml(s.total_amount)})</span></span>
        <a class="sample-preview-link" href="/samples/${s.png_filename}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Preview PNG</a>
      `;
      btn.addEventListener("click", () => selectSampleInvoice(s.png_filename, label));
      groupDiv.appendChild(btn);
    });

    sampleButtonsContainer.appendChild(groupDiv);
  });

  if (samples.length > 0 && state.selectedSampleFilename) {
    const target = samples.find((x) => x.png_filename === state.selectedSampleFilename) || samples[0];
    selectSampleInvoice(
      target.png_filename,
      `[${target.doc_type || "Invoice"}] ${target.invoice_number} — ${target.vendor_name} (${target.currency} ${target.total_amount})`
    );
  }
}

function setTelemetryRunning() {
  telemetryElapsed.textContent = "Running on watsonx Orchestrate...";
  const items = telemetrySteps.querySelectorAll(".step-item");
  items.forEach((li, i) => {
    li.classList.remove("completed", "running");
    if (i === 0 || i === 1 || i === 2) {
      li.classList.add("running");
    }
  });
}

function renderTelemetryResults(telemetryList) {
  if (!telemetryList || telemetryList.length === 0) return;
  const totalMs = telemetryList.reduce((acc, s) => acc + (Number(s.duration_ms) || 0), 0);
  telemetryElapsed.textContent = `Completed in ${(totalMs / 1000).toFixed(2)}s`;

  telemetrySteps.innerHTML = "";
  telemetryList.forEach((step) => {
    const li = document.createElement("li");
    li.className = `step-item ${step.status === "completed" ? "completed" : "running"}`;
    li.innerHTML = `
      <div class="step-index">&#10003;</div>
      <div class="step-body">
        <div class="step-title">${escapeHtml(step.name)} <span class="mono-badge">${step.duration_ms} ms</span></div>
        <div class="step-meta"><code>${escapeHtml(step.endpoint)}</code> — ${escapeHtml(step.detail || "")}</div>
      </div>
    `;
    telemetrySteps.appendChild(li);
  });
}

runPipelineBtn.addEventListener("click", async () => {
  if (!state.selectedFile && !state.selectedSampleFilename) {
    alert("Please drop a document file or select one of the sample documents first.");
    return;
  }

  runPipelineBtn.disabled = true;
  const originalText = runBtnLabel.textContent;
  runBtnLabel.textContent = "Uploading to wxO S3 & Extracting via docproc...";
  setTelemetryRunning();

  const formData = new FormData();
  formData.append("execution_mode", state.executionMode);
  if (state.selectedFile) {
    formData.append("file", state.selectedFile);
  } else if (state.selectedSampleFilename) {
    formData.append("sample_filename", state.selectedSampleFilename);
  }

  try {
    const resp = await fetch("/api/invoices/process", {
      method: "POST",
      body: formData,
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.detail || "Pipeline execution failed");
    }

    renderTelemetryResults(data.telemetry);
    await refreshInvoicesList(data.invoice.id);
  } catch (err) {
    telemetryElapsed.textContent = "Error";
    alert(`Pipeline Error: ${err.message}`);
  } finally {
    runPipelineBtn.disabled = false;
    runBtnLabel.textContent = originalText;
  }
});

// ============================================================================
// ACTIVE INVOICE RENDERING + INTERACTIVE BOUNDING BOXES + PO MATCH + RISK SHIELD
// ============================================================================
function setActiveInvoice(inv) {
  state.activeInvoice = inv;
  emptyStateBox.hidden = true;
  invoiceDetailsContainer.hidden = false;
  openInspectorModalBtn.disabled = false;

  const confPct = ((Number(inv.avg_confidence) || 0.98) * 100).toFixed(1);
  activeConfidenceBadge.hidden = false;
  activeConfidenceBadge.textContent = `${confPct}% WDU Confidence`;
  activeInvoiceSubtitle.textContent = `File: ${inv.file_name} | Mode: ${inv.execution_mode} | SQLite Row #${inv.id}`;

  const audit = inv.audit || {};
  const poMatch = audit.po_match || {};
  const apAuto = audit.ap_automation || {};
  const riskShield = audit.risk_shield || {};

  // Risk Pill in Top Right
  const rScore = riskShield.risk_score ?? 5;
  const rLevel = riskShield.risk_level || "LOW";
  activeRiskBadge.hidden = false;
  activeRiskBadge.textContent = `Risk: ${rScore}/100 (${rLevel})`;
  activeRiskBadge.className = `risk-pill ${rLevel === "HIGH" || rLevel === "CRITICAL" ? "high" : rLevel === "MEDIUM" ? "medium" : ""}`;

  // Tab Pills
  const threeWaySt = poMatch.three_way_status || poMatch.status || "MATCHED";
  tabPoStatusPill.textContent =
    threeWaySt === "MATCHED"
      ? "3-WAY OK"
      : threeWaySt === "GRN_SHORTAGE_DETECTED"
      ? "GRN SHORTAGE"
      : poMatch.status === "VARIANCE_DETECTED"
      ? "VARIANCE"
      : poMatch.status_label || poMatch.status || "MATCHED";
  tabPoStatusPill.style.background =
    poMatch.status === "MATCHED"
      ? "#defbe6"
      : poMatch.status === "VARIANCE_DETECTED"
      ? "#fee2e2"
      : "#e2e8f0";
  tabPoStatusPill.style.color =
    poMatch.status === "MATCHED"
      ? "#198038"
      : poMatch.status === "VARIANCE_DETECTED"
      ? "#b91c1c"
      : "#334155";

  if (tabApAutoPill) {
    const hasDebitMemo = Number(apAuto.debit_memo_deduction || 0) > 0;
    tabApAutoPill.textContent = hasDebitMemo
      ? `SHORT-PAY (${apAuto.debit_memo_number || "DM"})`
      : Number(apAuto.early_discount_savings || 0) > 0
      ? `SAVE ${inv.currency} ${Number(apAuto.early_discount_savings).toFixed(0)}`
      : "STP READY";
    tabApAutoPill.style.background = hasDebitMemo ? "#fef3c7" : "#e0f2fe";
    tabApAutoPill.style.color = hasDebitMemo ? "#b45309" : "#0369a1";
  }

  tabRiskScorePill.textContent = `${rScore}/100`;
  tabRiskScorePill.style.background =
    rLevel === "HIGH" || rLevel === "CRITICAL" ? "#fee2e2" : rLevel === "MEDIUM" ? "#fef3c7" : "#defbe6";
  tabRiskScorePill.style.color =
    rLevel === "HIGH" || rLevel === "CRITICAL" ? "#b91c1c" : rLevel === "MEDIUM" ? "#b45309" : "#198038";

  // HITL Workbench Status Badges
  const tier = inv.approval_tier || "AUTO_APPROVED";
  hitlTierBadge.textContent = tier;
  hitlTierBadge.className = `tier-badge ${
    tier.includes("VP_APPROVAL")
      ? "vp"
      : tier.includes("REJECTED") || tier.includes("MISMATCH")
      ? "rejected"
      : ""
  }`;

  const odooState = (inv.odoo_state || "draft").toLowerCase();
  if (inv.odoo_bill_id) {
    hitlOdooBadge.textContent = `Odoo Bill #${inv.odoo_bill_id} (${odooState.toUpperCase()})`;
    hitlOdooBadge.className = `odoo-state-badge ${odooState === "posted" ? "posted" : ""}`;
  } else {
    hitlOdooBadge.textContent = "Odoo: Not Synced Yet";
    hitlOdooBadge.className = "odoo-state-badge";
  }

  approvePostOdooBtn.disabled = odooState === "posted" && tier === "APPROVED_BY_VP";
  approvePostOdooBtn.innerHTML =
    odooState === "posted" && tier === "APPROVED_BY_VP"
      ? "&#10003; Approved &amp; Posted in Odoo Ledger"
      : "&#10003; Approve &amp; Post Bill in Odoo";

  if (inv.telemetry && inv.telemetry.length > 0) {
    renderTelemetryResults(inv.telemetry);
  }

  // Render Header Fields with semantic mapping to WDU KVP keys
  const headerFields = [
    { label: "Document Type", value: inv.document_type || "Invoice", kvpKey: "document_type", highlight: true },
    { label: "Invoice / Ref Number", value: inv.invoice_number, kvpKey: "invoice_number", highlight: true },
    { label: "Vendor / Merchant", value: inv.vendor_name, kvpKey: "vendor_name", highlight: true },
    { label: "Buyer (Bill To)", value: inv.buyer_name, kvpKey: "buyer_name" },
    { label: "Doc Date", value: inv.invoice_date, kvpKey: "invoice_date" },
    { label: "Due Date", value: inv.due_date, kvpKey: "due_date" },
    { label: "PO Number", value: inv.po_number, kvpKey: "po_number", highlight: true },
    { label: "Payment Terms", value: inv.payment_terms, kvpKey: "payment_terms" },
    { label: "Subtotal", value: `${inv.currency} ${Number(inv.subtotal_amount).toFixed(2)}`, kvpKey: "subtotal_amount" },
    { label: "Tax Amount", value: `${inv.currency} ${Number(inv.tax_amount).toFixed(2)}`, kvpKey: "tax_amount" },
    { label: "Total Amount Due", value: `${inv.currency} ${Number(inv.total_amount).toFixed(2)}`, kvpKey: "total_amount", highlight: true },
    { label: "Vendor Address", value: inv.vendor_address, kvpKey: "vendor_address", wide: true },
    { label: "Buyer Address", value: inv.buyer_address, kvpKey: "buyer_address", wide: true },
  ];

  structuredHeaderGrid.innerHTML = headerFields
    .map(
      (f) => `
      <div class="kvp-tile bbox-linked ${f.highlight ? "highlight" : ""} ${f.wide ? "kvp-tile-wide" : ""}" data-kvp-key="${f.kvpKey}">
        <div class="kvp-tile-label">${escapeHtml(f.label)}</div>
        <div class="kvp-tile-value">${escapeHtml(f.value || "—")}</div>
      </div>
    `
    )
    .join("");

  validationBanner.textContent =
    inv.math_summary ||
    inv.validation_notes ||
    `Validated: Subtotal (${inv.subtotal_amount}) + Tax (${inv.tax_amount}) = Total (${inv.total_amount})`;

  const items = inv.line_items || [];
  if (items.length === 0) {
    lineItemsTbody.innerHTML = `<tr><td colspan="7" class="empty-cell">No line items extracted.</td></tr>`;
  } else {
    lineItemsTbody.innerHTML = items
      .map(
        (item, idx) => `
        <tr class="line-item-row" data-row-index="${idx}" style="cursor:pointer;">
          <td>${item.line_index}</td>
          <td><strong>${escapeHtml(item.description)}</strong></td>
          <td>${escapeHtml(item.quantity)}</td>
          <td>${inv.currency} ${Number(item.unit_price).toFixed(2)}</td>
          <td><strong>${inv.currency} ${Number(item.amount).toFixed(2)}</strong></td>
          <td><span class="badge-tag">${escapeHtml(item.gl_category || "General Expense")}</span></td>
          <td><span class="confidence-pill">${((Number(item.confidence) || 0.98) * 100).toFixed(0)}%</span></td>
        </tr>
      `
      )
      .join("");
  }

  // Render Interactive Document Preview & SVG Bounding Boxes
  renderInteractiveBoundingBoxes(inv);

  // Render Tab 2: 3-Way PO + GRN Match & Step POs
  renderPoMatchingTab(inv, poMatch);

  // Render Tab 3: AP Payment Automation & GL Ledger Preview
  renderApAutomationTab(inv, apAuto, poMatch);

  // Render Tab 4: Fraud & Compliance Shield
  renderRiskShieldTab(inv, riskShield);

  renderSqliteTable();
}

function renderInteractiveBoundingBoxes(inv) {
  const previewUrl =
    inv.preview_image_url ||
    (inv.file_name ? `/samples/${inv.file_name.replace(/\.pdf$/i, ".png")}` : "/samples/invoice_acme_cloud_0042.png");
  const viewport = document.getElementById("docCanvasViewport");
  viewport.classList.remove("no-preview");
  docPreviewImg.onerror = () => {
    viewport.classList.add("no-preview");
    docBboxSvg.innerHTML = "";
  };
  docPreviewImg.src = previewUrl;

  const kvps = inv.raw_kvps || [];
  docBboxSvg.innerHTML = "";
  bboxHoverStatus.textContent = `Showing ${kvps.length} WDU bounding boxes — Hover any field or box`;

  kvps.forEach((k, idx) => {
    if (!k.bbox || k.bbox.width <= 0 || k.bbox.height <= 0) return;
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    const isLine = k.table_row_index !== null && k.table_row_index !== undefined;
    rect.setAttribute("x", k.bbox.x);
    rect.setAttribute("y", k.bbox.y);
    rect.setAttribute("width", k.bbox.width);
    rect.setAttribute("height", k.bbox.height);
    rect.setAttribute("rx", "2");
    rect.setAttribute("class", `bbox-rect ${isLine ? "bbox-line-item" : ""}`);
    rect.dataset.kvpId = k.id || `kvp_${idx}`;
    rect.dataset.kvpLabel = (k.label || "").replace(/^line_items\./, "");
    if (isLine) {
      rect.dataset.rowIndex = String(k.table_row_index);
    }

    const titleEl = document.createElementNS("http://www.w3.org/2000/svg", "title");
    titleEl.textContent = `${k.label}: ${k.value} (${Math.round((k.confidence || 0.98) * 100)}% conf)`;
    rect.appendChild(titleEl);

    rect.addEventListener("mouseenter", () => {
      rect.classList.add("active-bbox");
      bboxHoverStatus.textContent = `[WDU Node ${k.id}] ${k.label}: "${k.value}" (${Math.round((k.confidence || 0.98) * 100)}%)`;
      highlightMatchingFieldFromBbox(k);
    });

    rect.addEventListener("mouseleave", () => {
      rect.classList.remove("active-bbox");
      clearFieldHighlights();
      bboxHoverStatus.textContent = `Showing ${kvps.length} WDU bounding boxes — Hover any field or box`;
    });

    docBboxSvg.appendChild(rect);
  });

  // Wire KVP tile hover -> SVG bbox highlight
  structuredHeaderGrid.querySelectorAll(".kvp-tile").forEach((tile) => {
    const key = tile.dataset.kvpKey;
    tile.addEventListener("mouseenter", () => {
      tile.classList.add("active-kvp");
      docBboxSvg.querySelectorAll(".bbox-rect").forEach((r) => {
        if (r.dataset.kvpLabel === key) {
          r.classList.add("active-bbox");
          bboxHoverStatus.textContent = `Highlighting '${key}' on document page 1`;
        }
      });
    });
    tile.addEventListener("mouseleave", () => {
      tile.classList.remove("active-kvp");
      docBboxSvg.querySelectorAll(".bbox-rect").forEach((r) => r.classList.remove("active-bbox"));
      bboxHoverStatus.textContent = `Showing ${kvps.length} WDU bounding boxes — Hover any field or box`;
    });
  });

  // Wire Line Item Row hover -> SVG bbox highlight
  lineItemsTbody.querySelectorAll(".line-item-row").forEach((row) => {
    const rowIdx = row.dataset.rowIndex;
    row.addEventListener("mouseenter", () => {
      row.classList.add("active-line-row");
      docBboxSvg.querySelectorAll(".bbox-rect").forEach((r) => {
        if (r.dataset.rowIndex === rowIdx) {
          r.classList.add("active-bbox");
        }
      });
      bboxHoverStatus.textContent = `Highlighting Line Item #${Number(rowIdx) + 1} cells on document`;
    });
    row.addEventListener("mouseleave", () => {
      row.classList.remove("active-line-row");
      docBboxSvg.querySelectorAll(".bbox-rect").forEach((r) => r.classList.remove("active-bbox"));
      bboxHoverStatus.textContent = `Showing ${kvps.length} WDU bounding boxes — Hover any field or box`;
    });
  });
}

function highlightMatchingFieldFromBbox(k) {
  clearFieldHighlights();
  if (k.table_row_index !== null && k.table_row_index !== undefined) {
    const row = lineItemsTbody.querySelector(`.line-item-row[data-row-index="${k.table_row_index}"]`);
    if (row) row.classList.add("active-line-row");
  } else {
    const tile = structuredHeaderGrid.querySelector(`.kvp-tile[data-kvp-key="${k.label}"]`);
    if (tile) tile.classList.add("active-kvp");
  }
}

function clearFieldHighlights() {
  structuredHeaderGrid.querySelectorAll(".kvp-tile").forEach((t) => t.classList.remove("active-kvp"));
  lineItemsTbody.querySelectorAll(".line-item-row").forEach((r) => r.classList.remove("active-line-row"));
}

function renderPoMatchingTab(inv, poMatch) {
  const status = poMatch.status || "NO_PO";
  const twoWayStatus = poMatch.two_way_status || status;
  const threeWayStatus = poMatch.three_way_status || status;
  const simMode = poMatch.simulation_mode || "normal";

  // Highlight active scenario simulation button
  document.querySelectorAll(".btn-sim").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.sim === simMode);
  });

  poSummaryBanner.className = `po-summary-banner ${
    status === "VARIANCE_DETECTED" ? "variance" : status === "MATCHED" ? "" : "nopo"
  }`;
  poSummaryBanner.textContent = poMatch.summary || "No 3-Way PO/GRN comparison available.";

  const cur = inv.currency || "USD";
  const grnVariance = Number(poMatch.grn_variance ?? poMatch.subtotal_variance ?? 0);
  poKpiStrip.innerHTML = `
    <div class="kvp-tile highlight">
      <div class="kvp-tile-label">PO Reference #</div>
      <div class="kvp-tile-value">${escapeHtml(poMatch.po_number || "None")}</div>
    </div>
    <div class="kvp-tile highlight">
      <div class="kvp-tile-label">Warehouse GRN / SES #</div>
      <div class="kvp-tile-value">${escapeHtml(poMatch.grn_number || "N/A")} (${escapeHtml(poMatch.grn_date || "—")})</div>
    </div>
    <div class="kvp-tile">
      <div class="kvp-tile-label">Receiving Dock &amp; Inspector</div>
      <div class="kvp-tile-value">${escapeHtml(poMatch.receiving_dock || "N/A")} — ${escapeHtml(poMatch.grn_inspector || "—")}</div>
    </div>
    <div class="kvp-tile">
      <div class="kvp-tile-label">2-Way Match (PO vs Inv)</div>
      <div class="kvp-tile-value" style="color:${twoWayStatus === "MATCHED" ? "#198038" : "#b91c1c"};">
        ${escapeHtml(twoWayStatus)}
      </div>
    </div>
    <div class="kvp-tile">
      <div class="kvp-tile-label">3-Way Match (PO + GRN + Inv)</div>
      <div class="kvp-tile-value" style="color:${threeWayStatus === "MATCHED" ? "#198038" : "#b91c1c"};">
        ${escapeHtml(threeWayStatus)}
      </div>
    </div>
    <div class="kvp-tile">
      <div class="kvp-tile-label">GRN Accepted Subtotal</div>
      <div class="kvp-tile-value">${cur} ${Number(poMatch.grn_accepted_subtotal ?? poMatch.authorized_subtotal ?? 0).toFixed(2)}</div>
    </div>
    <div class="kvp-tile">
      <div class="kvp-tile-label">Billed Invoice Subtotal</div>
      <div class="kvp-tile-value">${cur} ${Number(poMatch.billed_subtotal || 0).toFixed(2)}</div>
    </div>
    <div class="kvp-tile ${Math.abs(grnVariance) > 0.05 ? "highlight" : ""}">
      <div class="kvp-tile-label">3-Way Net Variance (vs GRN)</div>
      <div class="kvp-tile-value" style="color:${Math.abs(grnVariance) > 0.05 ? "#b91c1c" : "#198038"};">
        ${grnVariance >= 0 ? "+" : ""}${cur} ${grnVariance.toFixed(2)} (${poMatch.grn_variance_pct ?? poMatch.variance_pct ?? 0}%)
      </div>
    </div>
  `;

  // Render Step PO Schedule & Milestone Drawdown Tracker
  const stepPo = poMatch.step_po;
  if (!stepPo || !stepPo.steps) {
    stepPoSection.innerHTML = "";
  } else {
    const hasBreach = (stepPo.steps || []).some((s) =>
      ["STEP_CEILING_BREACH", "LOCKED_MILESTONE_VIOLATION"].includes(s.status)
    );
    const overallStatus = hasBreach ? "STEP_GATE_HOLD" : "STEP_VERIFIED";
    const overallStatusColor = !hasBreach
      ? "background:#defbe6;color:#198038;"
      : "background:#fee2e2;color:#b91c1c;";
    const totalCap = Number(stepPo.total_contract_ceiling || 0);
    const totalDrawn = (stepPo.steps || []).reduce((acc, s) => acc + Number(s.billed_amount || 0), 0);
    const totalUtilPct = totalCap > 0 ? ((totalDrawn / totalCap) * 100).toFixed(1) : "100.0";

    const stepsHtml = (stepPo.steps || [])
      .map((s) => {
        const isCurrent = s.step_number === stepPo.current_step_number;
        const isBreach = ["STEP_CEILING_BREACH", "LOCKED_MILESTONE_VIOLATION"].includes(s.status);
        const badgeStyle =
          s.status === "COMPLETED_CLOSED"
            ? "background:#e0f2fe;color:#0369a1;"
            : s.status === "ACTIVE_VERIFIED"
            ? "background:#defbe6;color:#198038;"
            : isBreach
            ? "background:#fee2e2;color:#b91c1c;"
            : "background:#f1f5f9;color:#475569;";
        const barColor = isBreach
          ? "#da1e28"
          : s.status === "COMPLETED_CLOSED"
          ? "#0284c7"
          : "#198038";
        return `
          <div class="step-card ${isCurrent ? "active-step" : ""} ${isBreach ? "breach-step" : ""}">
            <div class="step-card-header">
              <span class="step-num-badge">Step ${s.step_number}${isCurrent ? " • CURRENT BILLING" : ""}</span>
              <span class="badge-tag" style="${badgeStyle}">${escapeHtml(s.status)}</span>
            </div>
            <div class="step-card-title">${escapeHtml(s.title)}</div>
            <div class="step-card-gate">Gate Sign-off: <strong>${escapeHtml(s.gate_requirement)}</strong></div>
            <div class="step-progress-track">
              <div class="step-progress-fill" style="width:${Math.min(100, s.utilization_pct || 0)}%;background:${barColor};"></div>
            </div>
            <div class="step-card-metrics">
              <span>Utilized: <strong>${cur} ${Number(s.billed_amount || 0).toFixed(2)}</strong> (${s.utilization_pct}%)</span>
              <span>Step Cap: <strong>${cur} ${Number(s.step_limit || 0).toFixed(2)}</strong></span>
            </div>
          </div>
        `;
      })
      .join("");

    stepPoSection.innerHTML = `
      <div class="step-po-header">
        <div>
          <h4>Step PO Phased Milestone &amp; Drawdown Tracker — ${escapeHtml(stepPo.contract_master_id || "MSA")} (${escapeHtml(stepPo.po_type_label || stepPo.po_type)})</h4>
          <p>Active Tranche: <strong>${escapeHtml(stepPo.current_step_name || "Step 1")}</strong> • Prior Billed: ${cur} ${Number(stepPo.prior_billed_amount || 0).toLocaleString()}</p>
        </div>
        <div class="step-po-meta">
          <span class="badge-tag" style="${overallStatusColor}">Step Gate: ${overallStatus}</span>
          <span class="badge-tag">Total Contract Cap: ${cur} ${totalCap.toLocaleString()} (${totalUtilPct}% drawn)</span>
        </div>
      </div>
      <div class="step-cards-grid">${stepsHtml}</div>
    `;
  }

  // Render 11-column 3-Way Match Matrix
  const lines = poMatch.line_comparisons || [];
  if (lines.length === 0) {
    poLinesTbody.innerHTML = `<tr><td colspan="11" class="empty-cell">No Purchase Order / GRN line-item baseline applicable for this document.</td></tr>`;
    return;
  }

  poLinesTbody.innerHTML = lines
    .map((l) => {
      const twoWayStr = l.two_way_status || l.status || "MATCHED";
      const threeWayStr = l.three_way_status || l.status || "3-WAY VERIFIED";
      const twoWayBadge =
        twoWayStr === "2-WAY OK" || twoWayStr === "MATCHED"
          ? "background:#defbe6;color:#198038;"
          : "background:#fee2e2;color:#b91c1c;";
      const threeWayBadge =
        threeWayStr === "3-WAY VERIFIED" || l.status === "MATCHED"
          ? "background:#defbe6;color:#198038;"
          : "background:#fee2e2;color:#b91c1c;";
      const grnQty = l.grn_qty ?? l.grn_accepted_qty ?? l.po_qty;
      const grnAmt = l.grn_amount ?? l.grn_accepted_amount ?? l.po_amount;
      const grnQtyMismatch = Math.abs(Number(l.inv_qty) - Number(grnQty)) > 0.01;
      return `
        <tr>
          <td>#${l.line_index}</td>
          <td>
            <strong>${escapeHtml(l.invoice_description)}</strong>
            ${l.grn_note ? `<div style="font-size:0.72rem;color:#64748b;margin-top:2px;">Dock Note: ${escapeHtml(l.grn_note)}</div>` : ""}
          </td>
          <td>${l.po_qty}</td>
          <td style="font-weight:700;color:${grnQtyMismatch ? "#b91c1c" : "#0369a1"};">
            ${grnQty} ${grnQtyMismatch ? "⚠" : "✓"}
          </td>
          <td><strong>${l.inv_qty}</strong></td>
          <td>${cur} ${Number(l.po_unit_price).toFixed(2)}</td>
          <td>${cur} ${Number(l.inv_unit_price).toFixed(2)}</td>
          <td>${cur} ${Number(grnAmt).toFixed(2)}</td>
          <td><strong>${cur} ${Number(l.inv_amount).toFixed(2)}</strong></td>
          <td><span class="badge-tag" style="${twoWayBadge}">${escapeHtml(twoWayStr)}</span></td>
          <td><span class="badge-tag" style="${threeWayBadge}">${escapeHtml(threeWayStr)}</span></td>
        </tr>
      `;
    })
    .join("");
}

function renderApAutomationTab(inv, apAuto, poMatch) {
  if (!apAuto || !apAuto.strategy) {
    apAutoBanner.innerHTML = "AP Payment Automation telemetry unavailable for this document.";
    apWaterfallGrid.innerHTML = "";
    apJournalTbody.innerHTML = `<tr><td colspan="5" class="empty-cell">No GL entries generated.</td></tr>`;
    return;
  }

  const cur = apAuto.currency || inv.currency || "USD";
  const strat = apAuto.strategy;
  const dmDeduction = Number(apAuto.debit_memo_deduction ?? apAuto.debit_memo_total_deduction ?? 0);
  const hasDebitMemo = dmDeduction > 0;
  const grossBilled = Number(apAuto.gross_billed_total ?? apAuto.billed_gross_total ?? inv.total_amount ?? 0);
  const verifiedGross = Number(apAuto.verified_gross_payable ?? apAuto.approved_gross_payable ?? grossBilled);
  const earlySavings = Number(apAuto.early_discount_savings ?? apAuto.early_payment_discount_savings ?? 0);
  const finalNet = Number(apAuto.final_net_settlement ?? apAuto.net_early_payment_disbursement ?? verifiedGross);
  const isSettled = inv.approval_tier === "AUTO_SHORT_PAID_DEBIT_MEMO" || inv.odoo_state === "posted";

  apAutoBanner.className = `ap-auto-banner ${hasDebitMemo ? "shortpay" : "ready"}`;
  apAutoBanner.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
      <div>
        <div style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.06em;font-weight:700;opacity:0.85;">
          Autonomous AP Settlement Strategy • Payment Rail: ${escapeHtml(apAuto.payment_method || "Automated ACH / ISO-20022 Wire")}
        </div>
        <div style="font-size:0.95rem;font-weight:700;margin-top:3px;">${escapeHtml(apAuto.strategy_label || strat)}</div>
        <div style="font-size:0.82rem;margin-top:4px;">${escapeHtml(apAuto.recommendation || "")}</div>
      </div>
      <span class="badge-tag" style="font-size:0.8rem;padding:6px 12px;${
        hasDebitMemo
          ? "background:#fef3c7;color:#b45309;"
          : "background:#defbe6;color:#198038;"
      }">${escapeHtml(strat)}</span>
    </div>
  `;

  apWaterfallGrid.innerHTML = `
    <div class="ap-waterfall-card">
      <div class="ap-wf-label">1. Vendor Billed Gross Total</div>
      <div class="ap-wf-val">${cur} ${grossBilled.toFixed(2)}</div>
      <div class="ap-wf-sub">Original Invoice Claim (incl. Tax)</div>
    </div>
    <div class="ap-waterfall-card ${hasDebitMemo ? "shortpay" : ""}">
      <div class="ap-wf-label">2. Auto Debit Memo (Short-Pay Adjustment)</div>
      <div class="ap-wf-val" style="color:${hasDebitMemo ? "#b91c1c" : "#64748b"};">
        -${cur} ${dmDeduction.toFixed(2)}
      </div>
      <div class="ap-wf-sub">
        ${
          hasDebitMemo
            ? `Ref: <strong>${escapeHtml(apAuto.debit_memo_number)}</strong> (GRN/PO Deduction + Tax Adj)`
            : "No GRN Shortage / Price Deduction Required"
        }
      </div>
    </div>
    <div class="ap-waterfall-card">
      <div class="ap-wf-label">3. 3-Way Verified Gross Payable</div>
      <div class="ap-wf-val">${cur} ${verifiedGross.toFixed(2)}</div>
      <div class="ap-wf-sub">Verified Goods/Milestone Value + Pro-Rata Tax</div>
    </div>
    <div class="ap-waterfall-card discount">
      <div class="ap-wf-label">4. Early-Pay Treasury Discount (${escapeHtml(apAuto.discount_terms || "2/10 Net 30")})</div>
      <div class="ap-wf-val" style="color:#198038;">
        -${cur} ${earlySavings.toFixed(2)}
      </div>
      <div class="ap-wf-sub">
        ${
          earlySavings > 0
            ? `${apAuto.discount_pct}% Treasury Yield (${apAuto.annualized_yield_apr || 36.7}% Annualized ROI)`
            : "Standard Net 30 Terms (0% Early Discount)"
        }
      </div>
    </div>
    <div class="ap-waterfall-card final">
      <div class="ap-wf-label">5. Final Net AP Disbursement (Early-Pay Window)</div>
      <div class="ap-wf-val" style="color:#0f62fe;">
        ${cur} ${finalNet.toFixed(2)}
      </div>
      <div class="ap-wf-sub">Net 30 Fallback: ${cur} ${verifiedGross.toFixed(2)}</div>
    </div>
  `;

  apActionInfo.innerHTML = `
    <strong>Automated AP Settlement &amp; Odoo ERP Posting:</strong>
    ${
      isSettled
        ? `Executed! Bill is posted in Odoo ERP (${escapeHtml(inv.approval_tier)}).`
        : hasDebitMemo
        ? `Ready to issue Debit Memo <strong>${escapeHtml(apAuto.debit_memo_number)}</strong> (-${cur} ${dmDeduction.toFixed(
            2
          )}) and post short-paid settlement of <strong>${cur} ${finalNet.toFixed(2)}</strong> to Odoo ERP.`
        : `Ready to capture ${escapeHtml(apAuto.discount_terms)} discount and post <strong>${cur} ${finalNet.toFixed(
            2
          )}</strong> payment run to Odoo ERP.`
    }
  `;

  executeApRunBtn.disabled = false;
  executeApRunBtn.innerHTML = isSettled
    ? "&#10003; Re-Sync AP Settlement &amp; Debit Memo in Odoo"
    : hasDebitMemo
    ? `&#9889; Issue Debit Memo (${escapeHtml(apAuto.debit_memo_number)}) &amp; Execute Short-Pay in Odoo`
    : "&#9889; Execute Automated AP Payment Run &amp; Post to Odoo";

  const entries = apAuto.journal_entries || [];
  if (entries.length === 0) {
    apJournalTbody.innerHTML = `<tr><td colspan="5" class="empty-cell">No GL postings generated.</td></tr>`;
  } else {
    apJournalTbody.innerHTML = entries
      .map((j) => {
        const eType = j.type || j.entry_type || "DEBIT";
        const typeBadge =
          eType === "DEBIT"
            ? "background:#e0f2fe;color:#0369a1;"
            : eType === "CREDIT"
            ? "background:#defbe6;color:#198038;"
            : "background:#fef3c7;color:#b45309;";
        return `
          <tr>
            <td><strong>${escapeHtml(j.account_code || j.gl_code)}</strong></td>
            <td>
              ${escapeHtml(j.account_name)}
              ${j.memo ? `<div style="font-size:0.72rem;color:#64748b;">${escapeHtml(j.memo)}</div>` : ""}
            </td>
            <td><span class="badge-tag" style="${typeBadge}">${escapeHtml(eType)}</span></td>
            <td>${j.debit > 0 ? `<strong>${cur} ${Number(j.debit).toFixed(2)}</strong>` : "—"}</td>
            <td>${j.credit > 0 ? `<strong>${cur} ${Number(j.credit).toFixed(2)}</strong>` : "—"}</td>
          </tr>
        `;
      })
      .join("");
  }
}

function renderRiskShieldTab(inv, riskShield) {
  const score = riskShield.risk_score ?? 5;
  const level = riskShield.risk_level || "LOW";
  const circleClass = level === "HIGH" ? "high" : level === "MEDIUM" ? "medium" : "";

  riskOverviewHeader.innerHTML = `
    <div>
      <h3 style="font-size:1rem;margin-bottom:4px;">Enterprise AP Fraud, Duplicate &amp; Split-Invoice Governance Shield</h3>
      <p style="font-size:0.82rem;color:#475569;">
        Automated 5-point forensic audit across SQLite historical ledger, Master ERP PO registry, and WDU OCR telemetry.
      </p>
    </div>
    <div class="risk-score-circle ${circleClass}">
      Risk Score: ${score} / 100 (${level})
    </div>
  `;

  const checks = riskShield.checks || [];
  riskChecksGrid.innerHTML = checks
    .map(
      (c) => `
      <div class="risk-check-card ${c.status}">
        <div class="risk-check-top">
          <span>${escapeHtml(c.title)}</span>
          <span class="badge-tag" style="${
            c.status === "PASS"
              ? "background:#defbe6;color:#198038;"
              : c.status === "WARN"
              ? "background:#fef3c7;color:#b45309;"
              : "background:#fee2e2;color:#b91c1c;"
          }">${escapeHtml(c.status)}</span>
        </div>
        <div class="risk-check-detail">${escapeHtml(c.detail)}</div>
      </div>
    `
    )
    .join("");
}

// ============================================================================
// HITL WORKBENCH ACTIONS (APPROVE & POST TO ODOO / EDIT FIELDS / DISPUTE EMAIL)
// ============================================================================
approvePostOdooBtn.addEventListener("click", async () => {
  if (!state.activeInvoice) return;
  const inv = state.activeInvoice;
  approvePostOdooBtn.disabled = true;
  approvePostOdooBtn.textContent = "Posting to Odoo General Ledger...";

  try {
    const res = await fetch(`/api/invoices/${inv.id}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        note: "Executive VP Sign-Off via watsonx Orchestrate HITL Workbench",
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to approve and post bill");

    await refreshInvoicesList(inv.id);
    alert(
      `Vendor Bill #${data.odoo_bill.id} (${data.odoo_bill.name}) is now officially POSTED in Odoo Cloud ERP!`
    );
  } catch (err) {
    alert(`HITL Approval Error: ${err.message}`);
    approvePostOdooBtn.disabled = false;
    approvePostOdooBtn.innerHTML = "&#10003; Approve &amp; Post Bill in Odoo";
  }
});

openEditFieldsBtn.addEventListener("click", () => {
  if (!state.activeInvoice) return;
  const inv = state.activeInvoice;
  document.getElementById("editInvoiceNumber").value = inv.invoice_number || "";
  document.getElementById("editPoNumber").value = inv.po_number || "";
  document.getElementById("editVendorName").value = inv.vendor_name || "";
  document.getElementById("editCurrency").value = inv.currency || "USD";
  document.getElementById("editSubtotal").value = Number(inv.subtotal_amount || 0).toFixed(2);
  document.getElementById("editTax").value = Number(inv.tax_amount || 0).toFixed(2);
  document.getElementById("editTotal").value = Number(inv.total_amount || 0).toFixed(2);
  document.getElementById("editDueDate").value = inv.due_date || "";
  editFieldsDialog.showModal();
});

cancelEditFieldsBtn.addEventListener("click", () => editFieldsDialog.close());

editFieldsForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!state.activeInvoice) return;
  const inv = state.activeInvoice;
  const saveBtn = document.getElementById("saveEditFieldsBtn");
  saveBtn.disabled = true;
  saveBtn.textContent = "Saving...";

  try {
    const overrides = {
      invoice_number: document.getElementById("editInvoiceNumber").value.trim(),
      po_number: document.getElementById("editPoNumber").value.trim(),
      vendor_name: document.getElementById("editVendorName").value.trim(),
      currency: document.getElementById("editCurrency").value.trim(),
      subtotal_amount: parseFloat(document.getElementById("editSubtotal").value),
      tax_amount: parseFloat(document.getElementById("editTax").value),
      total_amount: parseFloat(document.getElementById("editTotal").value),
      due_date: document.getElementById("editDueDate").value.trim(),
    };
    const res = await fetch(`/api/invoices/${inv.id}/update-fields`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ overrides }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to update fields");

    editFieldsDialog.close();
    await refreshInvoicesList(inv.id);
  } catch (err) {
    alert(`Update Error: ${err.message}`);
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = "Save Overrides & Re-Run Audit";
  }
});

openDisputeModalBtn.addEventListener("click", () => {
  if (!state.activeInvoice) return;
  const inv = state.activeInvoice;
  const poSummary = inv.audit?.po_match?.summary || "";
  const mathNote = inv.math_summary || inv.validation_notes || "";
  document.getElementById("disputeReason").value =
    `Dispute raised for ${inv.invoice_number} (${inv.vendor_name}, ${inv.currency} ${Number(inv.total_amount).toFixed(2)}).\n` +
    `2-Way PO Match Finding: ${poSummary}\n` +
    `Controller Audit Note: ${mathNote}\n` +
    `Please issue a revised invoice or credit memo referencing PO ${inv.po_number || "N/A"}.`;
  disputeDialog.showModal();
});

cancelDisputeBtn.addEventListener("click", () => disputeDialog.close());

disputeForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!state.activeInvoice) return;
  const inv = state.activeInvoice;
  const sendBtn = document.getElementById("sendDisputeSubmitBtn");
  sendBtn.disabled = true;
  sendBtn.textContent = "Sending Dispute Email via Gmail SMTP...";

  try {
    const recipient_email = document.getElementById("disputeRecipient").value.trim();
    const reason = document.getElementById("disputeReason").value.trim();
    const res = await fetch(`/api/invoices/${inv.id}/dispute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipient_email, reason }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Dispute email failed");

    disputeDialog.close();
    await refreshInvoicesList(inv.id);
    alert(`Formatted HTML AP Dispute Notice sent to ${data.recipient} and invoice marked REJECTED_DISPUTED!`);
  } catch (err) {
    alert(`Dispute Error: ${err.message}`);
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "Send Dispute Email & Mark Disputed";
  }
});

// ============================================================================
// 3-WAY GRN / STEP PO SCENARIO SIMULATOR & AUTOMATED AP PAYMENT RUN
// ============================================================================
document.querySelectorAll(".btn-sim").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!state.activeInvoice) return;
    const inv = state.activeInvoice;
    const mode = btn.dataset.sim || "normal";
    btn.disabled = true;
    try {
      const res = await fetch(`/api/invoices/${inv.id}/simulate-3way`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Simulation failed");
      await refreshInvoicesList(inv.id);
    } catch (err) {
      alert(`3-Way Scenario Error: ${err.message}`);
    } finally {
      btn.disabled = false;
    }
  });
});

if (executeApRunBtn) {
  executeApRunBtn.addEventListener("click", async () => {
    if (!state.activeInvoice) return;
    const inv = state.activeInvoice;
    executeApRunBtn.disabled = true;
    executeApRunBtn.textContent = "Executing Automated AP Run & Syncing Odoo GL...";

    try {
      const res = await fetch(`/api/invoices/${inv.id}/execute-ap-run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ apply_early_discount: true }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "AP Payment Run failed");

      await refreshInvoicesList(inv.id);
      const ap = data.ap_settlement || {};
      const dmText = ap.debit_memo_issued
        ? `\n• Auto Debit Memo Issued: ${ap.debit_memo_issued} (-${inv.currency} ${Number(ap.debit_memo_deduction || 0).toFixed(2)})`
        : "";
      alert(
        `Automated AP Payment Run Executed & Posted to Odoo Cloud ERP!\n` +
          `• Odoo Bill: #${data.odoo_bill?.id || "N/A"} (${data.odoo_bill?.name || "POSTED"})${dmText}\n` +
          `• Early-Pay Treasury Discount Saved: ${inv.currency} ${Number(ap.early_discount_saved || 0).toFixed(2)}\n` +
          `• Final Net Wire/ACH Disbursement: ${inv.currency} ${Number(ap.net_disbursed || 0).toFixed(2)}`
      );
    } catch (err) {
      alert(`AP Payment Run Error: ${err.message}`);
      executeApRunBtn.disabled = false;
      executeApRunBtn.innerHTML = "&#9889; Execute Automated AP Payment Run &amp; Post to Odoo";
    }
  });
}

// ============================================================================
// SQLITE TABLE RENDERING
// ============================================================================
function renderSqliteTable() {
  dbRecordCount.textContent = `${state.invoices.length} record${state.invoices.length === 1 ? "" : "s"}`;
  if (state.invoices.length === 0) {
    sqliteInvoicesTbody.innerHTML = `<tr><td colspan="10" class="empty-cell">No documents stored in SQLite yet.</td></tr>`;
    return;
  }

  sqliteInvoicesTbody.innerHTML = state.invoices
    .map((inv) => {
      const isSelected = state.activeInvoice && state.activeInvoice.id === inv.id;
      const poMatch = inv.audit?.po_match || {};
      const poStatus = poMatch.status || "MATCHED";
      const twoWay = poMatch.two_way_status || poStatus;
      const threeWay = poMatch.three_way_status || poStatus;
      const poBadge =
        poStatus === "MATCHED"
          ? `<span class="badge-tag" style="background:#defbe6;color:#198038;">3-Way Matched</span>`
          : twoWay === "MATCHED" && threeWay === "VARIANCE_DETECTED"
          ? `<span class="badge-tag" style="background:#fef3c7;color:#b45309;">3-Way GRN Shortage</span>`
          : poStatus === "VARIANCE_DETECTED"
          ? `<span class="badge-tag" style="background:#fee2e2;color:#b91c1c;">PO/GRN Variance</span>`
          : `<span class="badge-tag" style="background:#f1f5f9;color:#475569;">${escapeHtml(poStatus)}</span>`;

      const rScore = inv.audit?.risk_shield?.risk_score ?? 5;
      const rLevel = inv.audit?.risk_shield?.risk_level || "LOW";
      const riskBadge = `<span style="font-weight:700;color:${
        rLevel === "HIGH" ? "#b91c1c" : rLevel === "MEDIUM" ? "#b45309" : "#198038"
      };">${rScore}/100</span>`;

      const tier = inv.approval_tier || "AUTO_APPROVED";
      const tierBadge =
        tier === "VP_APPROVAL_REQUIRED"
          ? `<span style="color:#b28600;font-weight:600;">VP Review</span>`
          : tier === "REJECTED_DISPUTED" || tier === "FLAGGED_MATH_MISMATCH"
          ? `<span style="color:#da1e28;font-weight:600;">${escapeHtml(tier)}</span>`
          : tier === "AUTO_SHORT_PAID_DEBIT_MEMO"
          ? `<span style="color:#0369a1;font-weight:700;">Short-Paid (DM)</span>`
          : tier === "APPROVED_BY_VP"
          ? `<span style="color:#0f62fe;font-weight:700;">VP Approved</span>`
          : `<span style="color:#198038;font-weight:600;">Auto-OK</span>`;

      const odooState = (inv.odoo_state || "draft").toUpperCase();
      const odooBadge = inv.odoo_bill_id
        ? `<a href="${escapeHtml(inv.odoo_url || "https://invoiceprocessing.odoo.com")}" target="_blank" rel="noopener" class="badge-tag" style="${
            odooState === "POSTED"
              ? "background:#0f62fe;color:#ffffff;"
              : "background:#e0f2fe;color:#0369a1;"
          }text-decoration:none;" onclick="event.stopPropagation()">Bill #${inv.odoo_bill_id} (${odooState})</a>`
        : `<button type="button" class="btn-mini sync-odoo-btn" data-id="${inv.id}" onclick="event.stopPropagation()">Sync Odoo</button>`;

      return `
        <tr class="clickable-row ${isSelected ? "selected-row" : ""}" data-id="${inv.id}">
          <td>#${inv.id}</td>
          <td><span class="badge-tag">${escapeHtml(inv.document_type || "Invoice")}</span></td>
          <td data-type="${escapeHtml(inv.document_type || "Invoice")}"><strong>${escapeHtml(inv.invoice_number || "N/A")}</strong></td>
          <td>${escapeHtml(inv.vendor_name || "—")}</td>
          <td><strong>${escapeHtml(inv.currency)} ${Number(inv.total_amount).toFixed(2)}</strong></td>
          <td>${poBadge}</td>
          <td>${riskBadge}</td>
          <td>${tierBadge}</td>
          <td>${odooBadge}</td>
          <td>
            <button type="button" class="btn-mini delete-row-btn" data-id="${inv.id}">✕</button>
          </td>
        </tr>
      `;
    })
    .join("");

  sqliteInvoicesTbody.querySelectorAll(".sync-odoo-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const id = Number(btn.dataset.id);
      btn.textContent = "Syncing...";
      btn.disabled = true;
      try {
        const res = await fetch(`/api/invoices/${id}/sync-odoo`, { method: "POST" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Sync failed");
        await refreshInvoicesList(id);
      } catch (err) {
        alert(`Odoo error: ${err.message}`);
        btn.textContent = "Sync Odoo";
        btn.disabled = false;
      }
    });
  });

  sqliteInvoicesTbody.querySelectorAll("tr.clickable-row").forEach((tr) => {
    tr.addEventListener("click", (e) => {
      if (e.target.classList.contains("delete-row-btn")) return;
      const id = Number(tr.dataset.id);
      const found = state.invoices.find((x) => x.id === id);
      if (found) setActiveInvoice(found);
    });
  });

  sqliteInvoicesTbody.querySelectorAll(".delete-row-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const id = Number(btn.dataset.id);
      const res = await fetch(`/api/invoices/${id}`, { method: "DELETE" });
      if (res.ok) {
        await refreshInvoicesList();
      }
    });
  });
}

function populateInspectorDialog(inv) {
  dialogS3Url.textContent = inv.s3_url || "N/A";
  dialogFlowId.textContent = state.healthInfo ? state.healthInfo.flow_id : "513e67d6-2974-4776-a0ac-5869876bee9a";
  dialogAgentId.textContent = state.healthInfo ? state.healthInfo.agent_id : "23215e30-2f2f-4373-974b-0d7bb89e657a";
  dialogThreadId.textContent = inv.wxo_thread_id || "Headless Direct Flow (No chat thread)";
  dialogOcrText.textContent = inv.extracted_text || "No OCR text available.";

  const kvps = inv.raw_kvps || [];
  if (kvps.length === 0) {
    dialogRawKvpsTbody.innerHTML = `<tr><td colspan="4" class="empty-cell">No raw KVP nodes recorded.</td></tr>`;
    return;
  }

  dialogRawKvpsTbody.innerHTML = kvps
    .map((k) => {
      const bboxStr = k.bbox
        ? `p${k.bbox.page_number}: (${k.bbox.x}, ${k.bbox.y}, ${k.bbox.width}x${k.bbox.height})`
        : "—";
      const rowSuffix =
        k.table_row_index !== null && k.table_row_index !== undefined
          ? ` [row ${k.table_row_index}]`
          : "";
      return `
        <tr>
          <td><code>${escapeHtml(k.id || "—")}</code></td>
          <td><strong>${escapeHtml((k.label || "") + rowSuffix)}</strong></td>
          <td>${escapeHtml(k.value || "")}</td>
          <td><code>${escapeHtml(bboxStr)}</code></td>
        </tr>
      `;
    })
    .join("");
}

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const checkGmailBtn = document.getElementById("checkGmailBtn");
if (checkGmailBtn) {
  checkGmailBtn.addEventListener("click", async () => {
    checkGmailBtn.disabled = true;
    checkGmailBtn.textContent = "Scanning aditya.krishnan2829@gmail.com inbox...";
    try {
      const res = await fetch("/api/gmail/check-inbox", { method: "POST" });
      let data;
      try {
        data = await res.json();
      } catch (parseErr) {
        throw new Error(`Server returned status ${res.status} (${res.statusText})`);
      }
      if (!res.ok) throw new Error(data?.detail || `Error: ${res.statusText}`);
      if (data.processed_count === 0) {
        alert(
          "No new unread invoice emails found in INBOX. Send an email with an invoice attachment (PDF/PNG) to aditya.krishnan2829@gmail.com and try again!"
        );
      } else {
        await refreshInvoicesList();
        alert(
          `Successfully ingested and processed ${data.processed_count} invoice email(s) and synced to Odoo ERP!`
        );
      }
    } catch (err) {
      alert(`Gmail check error: ${err.message}`);
    } finally {
      checkGmailBtn.disabled = false;
      checkGmailBtn.textContent = "Scan Gmail Inbox for Invoices";
    }
  });
}

initApp();
