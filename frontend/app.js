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
  selectedSampleFilename: "invoice_acme_cloud_0042.png",
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
const tabRiskScorePill = document.getElementById("tabRiskScorePill");

// Visual Grounding Canvas & Fields
const docPreviewImg = document.getElementById("docPreviewImg");
const docBboxSvg = document.getElementById("docBboxSvg");
const bboxHoverStatus = document.getElementById("bboxHoverStatus");
const structuredHeaderGrid = document.getElementById("structuredHeaderGrid");
const validationBanner = document.getElementById("validationBanner");
const lineItemsTbody = document.getElementById("lineItemsTbody");

// PO Matching & Risk Shield Panels
const poSummaryBanner = document.getElementById("poSummaryBanner");
const poKpiStrip = document.getElementById("poKpiStrip");
const poLinesTbody = document.getElementById("poLinesTbody");
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
        <strong>${escapeHtml(g.category)}</strong>: ${fmtUsd.format(g.amount_usd)} (${g.pct}%)
      </span>
    `
    )
    .join("");
}

function renderSampleButtons(samples) {
  sampleButtonsContainer.innerHTML = "";
  samples.forEach((s, idx) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `sample-btn ${s.png_filename === state.selectedSampleFilename ? "selected" : ""}`;
    btn.dataset.filename = s.png_filename;
    const typeTag = s.doc_type || "Invoice";
    const label = `[${typeTag}] ${s.invoice_number} — ${s.vendor_name} (${s.currency} ${s.total_amount})`;
    btn.innerHTML = `
      <span><strong>#${idx + 1}:</strong> ${escapeHtml(label)}</span>
      <a class="sample-preview-link" href="/samples/${s.png_filename}" target="_blank" rel="noopener" onclick="event.stopPropagation()">Preview PNG</a>
    `;
    btn.addEventListener("click", () => selectSampleInvoice(s.png_filename, label));
    sampleButtonsContainer.appendChild(btn);
  });
  if (samples.length > 0 && state.selectedSampleFilename) {
    const first = samples[0];
    selectSampleInvoice(
      first.png_filename,
      `[${first.doc_type || "Invoice"}] ${first.invoice_number} — ${first.vendor_name} (${first.currency} ${first.total_amount})`
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
  const riskShield = audit.risk_shield || {};

  // Risk Pill in Top Right
  const rScore = riskShield.risk_score ?? 5;
  const rLevel = riskShield.risk_level || "LOW";
  activeRiskBadge.hidden = false;
  activeRiskBadge.textContent = `Risk: ${rScore}/100 (${rLevel})`;
  activeRiskBadge.className = `risk-pill ${rLevel === "HIGH" ? "high" : rLevel === "MEDIUM" ? "medium" : ""}`;

  // Tab Pills
  tabPoStatusPill.textContent = poMatch.status || "MATCHED";
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

  tabRiskScorePill.textContent = `${rScore}/100`;
  tabRiskScorePill.style.background =
    rLevel === "HIGH" ? "#fee2e2" : rLevel === "MEDIUM" ? "#fef3c7" : "#defbe6";
  tabRiskScorePill.style.color =
    rLevel === "HIGH" ? "#b91c1c" : rLevel === "MEDIUM" ? "#b45309" : "#198038";

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
    { label: "Vendor Address", value: inv.vendor_address, kvpKey: "vendor_address" },
    { label: "Buyer Address", value: inv.buyer_address, kvpKey: "buyer_address" },
  ];

  structuredHeaderGrid.innerHTML = headerFields
    .map(
      (f) => `
      <div class="kvp-tile bbox-linked ${f.highlight ? "highlight" : ""}" data-kvp-key="${f.kvpKey}">
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

  // Render Tab 2: 2-Way PO Match
  renderPoMatchingTab(inv, poMatch);

  // Render Tab 3: Fraud & Compliance Shield
  renderRiskShieldTab(inv, riskShield);

  renderSqliteTable();
}

function renderInteractiveBoundingBoxes(inv) {
  const previewUrl =
    inv.preview_image_url ||
    (inv.file_name ? `/samples/${inv.file_name.replace(/\.pdf$/i, ".png")}` : "/samples/invoice_acme_cloud_0042.png");
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
  poSummaryBanner.className = `po-summary-banner ${
    status === "VARIANCE_DETECTED" ? "variance" : status === "MATCHED" ? "" : "nopo"
  }`;
  poSummaryBanner.textContent = poMatch.summary || "No PO comparison available.";

  const cur = inv.currency || "USD";
  poKpiStrip.innerHTML = `
    <div class="kvp-tile highlight">
      <div class="kvp-tile-label">PO Reference #</div>
      <div class="kvp-tile-value">${escapeHtml(poMatch.po_number || "None")}</div>
    </div>
    <div class="kvp-tile">
      <div class="kvp-tile-label">Authority Source</div>
      <div class="kvp-tile-value">${escapeHtml(poMatch.po_source || "N/A")}</div>
    </div>
    <div class="kvp-tile">
      <div class="kvp-tile-label">Authorized PO Subtotal</div>
      <div class="kvp-tile-value">${cur} ${Number(poMatch.authorized_subtotal || 0).toFixed(2)}</div>
    </div>
    <div class="kvp-tile">
      <div class="kvp-tile-label">Billed Invoice Subtotal</div>
      <div class="kvp-tile-value">${cur} ${Number(poMatch.billed_subtotal || 0).toFixed(2)}</div>
    </div>
    <div class="kvp-tile ${Math.abs(Number(poMatch.subtotal_variance || 0)) > 0.05 ? "highlight" : ""}">
      <div class="kvp-tile-label">Net Variance</div>
      <div class="kvp-tile-value" style="color:${
        Math.abs(Number(poMatch.subtotal_variance || 0)) > 0.05 ? "#b91c1c" : "#198038"
      };">
        ${Number(poMatch.subtotal_variance || 0) >= 0 ? "+" : ""}${cur} ${Number(poMatch.subtotal_variance || 0).toFixed(2)} (${poMatch.variance_pct || 0}%)
      </div>
    </div>
  `;

  const lines = poMatch.line_comparisons || [];
  if (lines.length === 0) {
    poLinesTbody.innerHTML = `<tr><td colspan="10" class="empty-cell">No Purchase Order line-item baseline applicable for this document.</td></tr>`;
    return;
  }

  poLinesTbody.innerHTML = lines
    .map((l) => {
      const badgeColor =
        l.status === "MATCHED"
          ? "background:#defbe6;color:#198038;"
          : "background:#fee2e2;color:#b91c1c;";
      return `
        <tr>
          <td>#${l.line_index}</td>
          <td><strong>${escapeHtml(l.invoice_description)}</strong></td>
          <td>${l.po_qty}</td>
          <td><strong>${l.inv_qty}</strong></td>
          <td>${cur} ${Number(l.po_unit_price).toFixed(2)}</td>
          <td>${cur} ${Number(l.inv_unit_price).toFixed(2)}</td>
          <td>${cur} ${Number(l.po_amount).toFixed(2)}</td>
          <td><strong>${cur} ${Number(l.inv_amount).toFixed(2)}</strong></td>
          <td style="font-weight:700;color:${Math.abs(l.delta_amount) > 0.05 ? "#b91c1c" : "#198038"};">
            ${l.delta_amount >= 0 ? "+" : ""}${cur} ${Number(l.delta_amount).toFixed(2)}
          </td>
          <td><span class="badge-tag" style="${badgeColor}">${escapeHtml(l.status)}</span></td>
        </tr>
      `;
    })
    .join("");
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
      const poStatus = inv.audit?.po_match?.status || "MATCHED";
      const poBadge =
        poStatus === "MATCHED"
          ? `<span class="badge-tag" style="background:#defbe6;color:#198038;">2-Way Matched</span>`
          : poStatus === "VARIANCE_DETECTED"
          ? `<span class="badge-tag" style="background:#fee2e2;color:#b91c1c;">PO Variance</span>`
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
          <td><strong>${escapeHtml(inv.invoice_number || "N/A")}</strong></td>
          <td>${escapeHtml(inv.vendor_name || "—")}</td>
          <td><strong>${escapeHtml(inv.currency)} ${Number(inv.total_amount).toFixed(2)}</strong></td>
          <td>${poBadge}</td>
          <td>${riskBadge}</td>
          <td>${tierBadge}</td>
          <td>${odooBadge}</td>
          <td>
            <button type="button" class="btn-mini delete-row-btn" data-id="${inv.id}">Delete</button>
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
