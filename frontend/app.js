/**
 * IBM watsonx Orchestrate — Enterprise AP & Multi-Document IDP Command Center
 * Carbon Design System Application Controller
 *
 * Implements:
 * 1. Executive CFO Spend Analytics & General Ledger (GL) Category Ribbon
 * 2. Multi-Channel Ingestion (Sample Catalog, Local Upload, Gmail IMAP/SMTP)
 * 3. Interactive WDU `docproc` Visual Bounding-Box Overlay Canvas (2-way hover highlight)
 * 4. Automated 3-Way Matching (PO <-> Warehouse GRN <-> Vendor Invoice) & Step PO Tracker
 * 5. Autonomous AP Payment Automation (Debit Memo Generation, 2/10 Net 30 Early Pay Discount)
 * 6. 6-Point Fraud, Duplicate & Split-Invoice Governance Shield
 * 7. Live Odoo Cloud ERP XML-RPC Synchronization & HITL Workbench
 * 8. Official 7–10 Minute Client Demonstration Script & Presentation Stage Flow
 */

const state = {
  selectedFile: null,
  selectedSampleFilename: "clean_invoices/invoice_acme_cloud_0042.png",
  selectedFilterCategory: "all",
  executionMode: "direct_flow",
  activeInvoice: null,
  invoices: [],
  allSamples: [],
  analytics: null,
  healthInfo: null,
};

// ============================================================================
// DOM ELEMENTS REFERENCE
// ============================================================================
const tenantStatusText = document.getElementById("tenantStatusText");
const modeCardDirect = document.getElementById("modeCardDirect");
const modeCardAgent = document.getElementById("modeCardAgent");

// Ingestion Switcher & Sections
const tabBtnSamples = document.getElementById("tabBtnSamples");
const tabBtnUpload = document.getElementById("tabBtnUpload");
const tabBtnGmail = document.getElementById("tabBtnGmail");
const sectionSamples = document.getElementById("sectionSamples");
const sectionUpload = document.getElementById("sectionUpload");
const sectionGmail = document.getElementById("sectionGmail");

const sampleFilterBar = document.getElementById("sampleFilterBar");
const sampleButtonsContainer = document.getElementById("sampleButtonsContainer");
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const dropzoneTitle = document.getElementById("dropzoneTitle");
const dropzoneHint = document.getElementById("dropzoneHint");
const checkGmailBtn = document.getElementById("checkGmailBtn");
const gmailStatusTag = document.getElementById("gmailStatusTag");

// Execution & Telemetry
const runPipelineBtn = document.getElementById("runPipelineBtn");
const runBtnLabel = document.getElementById("runBtnLabel");
const telemetryElapsed = document.getElementById("telemetryElapsed");
const telemetrySteps = document.getElementById("telemetrySteps");

// CFO Analytics
const kpiTotalSpend = document.getElementById("kpiTotalSpend");
const kpiDocMix = document.getElementById("kpiDocMix");
const kpiStpRate = document.getElementById("kpiStpRate");
const kpiVpCount = document.getElementById("kpiVpCount");
const kpiOdooSynced = document.getElementById("kpiOdooSynced");
const kpiAvgConf = document.getElementById("kpiAvgConf");
const glProgressBar = document.getElementById("glProgressBar");
const glLegend = document.getElementById("glLegend");
const glTopCategoryLabel = document.getElementById("glTopCategoryLabel");

// Active Workbench Header & Status
const activeDocTitle = document.getElementById("activeDocTitle");
const activeInvoiceSubtitle = document.getElementById("activeInvoiceSubtitle");
const activeRiskBadge = document.getElementById("activeRiskBadge");
const activeConfidenceBadge = document.getElementById("activeConfidenceBadge");
const openInspectorModalBtn = document.getElementById("openInspectorModalBtn");
const emptyStateBox = document.getElementById("emptyStateBox");
const invoiceDetailsContainer = document.getElementById("invoiceDetailsContainer");

// HITL Workbench Actions
const hitlTierBadge = document.getElementById("hitlTierBadge");
const hitlOdooBadge = document.getElementById("hitlOdooBadge");
const approvePostOdooBtn = document.getElementById("approvePostOdooBtn");
const openEditFieldsBtn = document.getElementById("openEditFieldsBtn");
const openDisputeModalBtn = document.getElementById("openDisputeModalBtn");

// Tab Status Badges
const tabPoStatusPill = document.getElementById("tabPoStatusPill");
const tabApAutoPill = document.getElementById("tabApAutoPill");
const tabRiskScorePill = document.getElementById("tabRiskScorePill");

// Tab 1: Visual Grounding & Extracted KVPs
const docPreviewImg = document.getElementById("docPreviewImg");
const docBboxSvg = document.getElementById("docBboxSvg");
const bboxHoverStatus = document.getElementById("bboxHoverStatus");
const docEmptyNote = document.getElementById("docEmptyNote");
const structuredHeaderGrid = document.getElementById("structuredHeaderGrid");
const validationBanner = document.getElementById("validationBanner");
const lineItemsTbody = document.getElementById("lineItemsTbody");

// Tab 2: 3-Way Match & Step POs
const threeWaySimToolbar = document.getElementById("threeWaySimToolbar");
const poSummaryBanner = document.getElementById("poSummaryBanner");
const poKpiStrip = document.getElementById("poKpiStrip");
const stepPoSection = document.getElementById("stepPoSection");
const poLinesTbody = document.getElementById("poLinesTbody");

// Tab 3: AP Automation & Payment Run
const apAutoBanner = document.getElementById("apAutoBanner");
const apWaterfallGrid = document.getElementById("apWaterfallGrid");
const apActionInfo = document.getElementById("apActionInfo");
const executeApRunBtn = document.getElementById("executeApRunBtn");
const apJournalTbody = document.getElementById("apJournalTbody");

// Tab 4: Fraud Shield
const riskOverviewHeader = document.getElementById("riskOverviewHeader");
const riskChecksGrid = document.getElementById("riskChecksGrid");

// Downstream SQLite Table
const dbRecordCount = document.getElementById("dbRecordCount");
const sqliteInvoicesTbody = document.getElementById("sqliteInvoicesTbody");
const sqliteSearchInput = document.getElementById("sqliteSearchInput");
const sqliteFilterSelect = document.getElementById("sqliteFilterSelect");
const sqliteRefreshBtn = document.getElementById("sqliteRefreshBtn");

// Dialog Modals
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

// Topbar Demo Guide button & Modal
const openDemoGuideModalBtn = document.getElementById("openDemoGuideModalBtn");
const demoGuideModalDialog = document.getElementById("demoGuideModalDialog");

// Mandatory fallback for browsers without native <dialog closedby="any"> support
[rawInspectorDialog, editFieldsDialog, disputeDialog, demoGuideModalDialog].forEach((dlg) => {
  if (dlg && !("closedBy" in HTMLDialogElement.prototype)) {
    dlg.addEventListener("click", (event) => {
      if (event.target !== dlg) return;
      const rect = dlg.getBoundingClientRect();
      const isInside =
        rect.top <= event.clientY &&
        event.clientY <= rect.top + rect.height &&
        rect.left <= event.clientX &&
        event.clientX <= rect.left + rect.width;
      if (!isInside) dlg.close();
    });
  }
});

// ============================================================================
// WORKBENCH TAB SWITCHING
// ============================================================================
function switchTab(targetId) {
  if (invoiceDetailsContainer) invoiceDetailsContainer.hidden = false;
  if (emptyStateBox) emptyStateBox.hidden = true;
  document.querySelectorAll(".cds--tab-btn").forEach((b) => {
    const isActive = b.dataset.tab === targetId;
    b.classList.toggle("active", isActive);
    b.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  document.querySelectorAll(".cds--tab-panel").forEach((panel) => {
    const match = panel.id === targetId;
    panel.classList.toggle("active", match);
    panel.hidden = !match;
  });
}

document.querySelectorAll(".cds--tab-btn").forEach((tabBtn) => {
  tabBtn.addEventListener("click", () => switchTab(tabBtn.dataset.tab));
});

if (openDemoGuideModalBtn) {
  openDemoGuideModalBtn.addEventListener("click", () => {
    if (demoGuideModalDialog && typeof demoGuideModalDialog.showModal === "function") {
      demoGuideModalDialog.showModal();
    } else {
      switchTab("tabDemoGuide");
      document.getElementById("tabDemoGuide")?.scrollIntoView({ behavior: "smooth" });
    }
  });
}

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

// ============================================================================
// INGESTION NAV SWITCHER (SAMPLE CATALOG vs UPLOAD vs GMAIL)
// ============================================================================
function setIngestionTab(activeTab) {
  [tabBtnSamples, tabBtnUpload, tabBtnGmail].forEach((btn) => btn?.classList.remove("active"));
  sectionSamples.style.display = "none";
  sectionUpload.style.display = "none";
  sectionGmail.style.display = "none";

  if (activeTab === "samples") {
    tabBtnSamples.classList.add("active");
    sectionSamples.style.display = "block";
  } else if (activeTab === "upload") {
    tabBtnUpload.classList.add("active");
    sectionUpload.style.display = "block";
  } else if (activeTab === "gmail") {
    tabBtnGmail.classList.add("active");
    sectionGmail.style.display = "block";
  }
}

tabBtnSamples?.addEventListener("click", () => setIngestionTab("samples"));
tabBtnUpload?.addEventListener("click", () => setIngestionTab("upload"));
tabBtnGmail?.addEventListener("click", () => setIngestionTab("gmail"));

// Sample Category Filter Chips
sampleFilterBar?.querySelectorAll(".cds--filter-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    sampleFilterBar.querySelectorAll(".cds--filter-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    state.selectedFilterCategory = chip.dataset.filter || "all";
    renderFilteredSampleCards();
  });
});

// Drag & Drop File Ingestion
dropzone?.addEventListener("click", () => fileInput.click());
dropzone?.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("active");
});
dropzone?.addEventListener("dragleave", () => dropzone.classList.remove("active"));
dropzone?.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("active");
  if (e.dataTransfer.files?.length) {
    selectLocalFile(e.dataTransfer.files[0]);
  }
});
fileInput?.addEventListener("change", (e) => {
  if (e.target.files?.length) {
    selectLocalFile(e.target.files[0]);
  }
});

function selectLocalFile(file) {
  state.selectedFile = file;
  state.selectedSampleFilename = null;
  dropzoneTitle.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  dropzoneHint.textContent = "Click 'Upload to wxO S3 & Run IDP Flow' below to process via WDU";
  document.querySelectorAll(".cds--sample-card").forEach((c) => c.classList.remove("selected"));
}

function selectSampleInvoice(filename, label) {
  state.selectedSampleFilename = filename;
  state.selectedFile = null;
  highlightSelectedSampleCard();
  dropzoneTitle.textContent = `Selected Catalog Sample: ${filename.split("/").pop()}`;
  dropzoneHint.textContent = label || "Ready for S3 upload and docproc extraction";
}

function highlightSelectedSampleCard() {
  document.querySelectorAll(".cds--sample-card").forEach((card) => {
    const isSelected = card.dataset.filename === state.selectedSampleFilename;
    card.classList.toggle("selected", isSelected);
  });
}

// ============================================================================
// DATA LOADING & INITIALIZATION
// ============================================================================
async function initApp() {
  try {
    const [healthRes, samplesRes] = await Promise.all([
      fetch("/api/health"),
      fetch("/api/samples"),
    ]);

    if (healthRes.ok) {
      state.healthInfo = await healthRes.json();
      if (tenantStatusText) {
        tenantStatusText.textContent = `Connected: ca-tor | Flow ${state.healthInfo.flow_id.slice(0, 8)}... | Odoo ERP Active`;
      }
      if (state.healthInfo.database) {
        const db = state.healthInfo.database;
        const dbText = document.getElementById("dbStatusText");
        const dbTag = document.getElementById("dbEngineTag");
        if (dbText) dbText.textContent = `${db.engine}: Connected`;
        if (dbTag) dbTag.textContent = `${db.engine} (${db.database || "neondb"})`;
      }
    }

    if (samplesRes.ok) {
      const { samples } = await samplesRes.json();
      state.allSamples = samples || [];
      renderFilteredSampleCards();
    }

    await refreshInvoicesList();
  } catch (err) {
    tenantStatusText.textContent = `Backend Offline: ${err.message}`;
  }
}

async function refreshInvoicesList(preserveActiveId = null) {
  try {
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
  } catch (err) {
    console.error("Failed to refresh invoices:", err);
  }
}

// ============================================================================
// CFO SPEND ANALYTICS RIBBON RENDERING
// ============================================================================
function renderCfoAnalytics(analytics) {
  if (!analytics) return;
  const fmtUsd = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });

  const totalSpend = analytics.total_spend_usd ?? analytics.total_ap_spend_usd ?? 0;
  if (kpiTotalSpend) kpiTotalSpend.textContent = fmtUsd.format(totalSpend);

  const invCount = analytics.invoice_count ?? analytics.by_doc_type?.Invoice ?? 0;
  const poCount = analytics.po_count ?? analytics.by_doc_type?.["Purchase Order"] ?? 0;
  const rcptCount = analytics.receipt_count ?? analytics.by_doc_type?.Receipt ?? 0;
  if (kpiDocMix) kpiDocMix.textContent = `${invCount} Invoices • ${poCount} POs • ${rcptCount} Receipts`;

  const stpRate = analytics.stp_rate_pct ?? analytics.stp_rate ?? 0;
  const stpCount = analytics.stp_auto_approved_count ?? analytics.auto_approved_count ?? 0;
  const vpCount = analytics.vp_review_count ?? analytics.vp_approval_count ?? 0;
  if (kpiStpRate) kpiStpRate.textContent = `${Number(stpRate).toFixed(1)}%`;
  if (kpiVpCount) kpiVpCount.textContent = `${stpCount} Auto-Approved (${vpCount} VP Review)`;

  if (kpiOdooSynced) kpiOdooSynced.textContent = `${analytics.odoo_synced_count || 0} Bills`;
  const avgConf = analytics.avg_confidence_pct ?? analytics.avg_wdu_confidence ?? 98.5;
  if (kpiAvgConf) kpiAvgConf.textContent = `${Number(avgConf).toFixed(1)}%`;

  const breakdown = analytics.gl_breakdown || [];
  const topCat = breakdown[0]?.category || "Cloud Infrastructure";
  const topPct = breakdown[0]?.percentage ?? breakdown[0]?.pct ?? 0;
  if (glTopCategoryLabel) {
    glTopCategoryLabel.textContent = `Top Category: ${topCat} (${Number(topPct).toFixed(1)}% of Total Spend)`;
  }

  if (glProgressBar) {
    glProgressBar.innerHTML = breakdown
      .map(
        (b) =>
          `<div class="cds--gl-bar-segment" style="width:${b.percentage || b.pct}%;background-color:${b.color};" title="${escapeHtml(
            b.category
          )}: ${fmtUsd.format(b.amount_usd || b.spend_usd || 0)} (${b.percentage || b.pct}%)"></div>`
      )
      .join("");
  }

  if (glLegend) {
    glLegend.innerHTML = breakdown
      .map(
        (b) => `
        <div class="cds--gl-legend-item">
          <span class="cds--gl-dot" style="background-color:${b.color};"></span>
          <span><strong>${escapeHtml(b.category)}:</strong> ${fmtUsd.format(b.amount_usd || b.spend_usd || 0)} (${b.percentage || b.pct}%)</span>
        </div>
      `
      )
      .join("");
  }
}

// ============================================================================
// SAMPLE DOCUMENTS RENDERING
// ============================================================================
function renderFilteredSampleCards() {
  sampleButtonsContainer.innerHTML = "";
  const filter = state.selectedFilterCategory;

  const filtered = state.allSamples.filter((s) => {
    if (filter === "all") return true;
    if (filter === "clean") return s.subfolder === "clean_invoices";
    if (filter === "shortage") return s.png_filename?.includes("titan") || s.invoice_number === "INV-2026-7731";
    if (filter === "breach") return s.png_filename?.includes("pacific") || s.invoice_number === "INV-2026-2045";
    if (filter === "po") return s.subfolder === "purchase_orders";
    if (filter === "receipt") return s.subfolder === "receipts";
    return true;
  });

  if (filtered.length === 0) {
    sampleButtonsContainer.innerHTML = `<div style="padding:16px;font-size:12px;color:var(--text-secondary);text-align:center;">No documents match filter '${filter}'.</div>`;
    return;
  }

  filtered.forEach((s) => {
    const isSelected = s.png_filename === state.selectedSampleFilename;
    const card = document.createElement("div");
    card.className = `cds--sample-card ${isSelected ? "selected" : ""}`;
    card.dataset.filename = s.png_filename;

    let tagColor = "blue";
    let tagText = s.doc_type || "Invoice";
    if (s.subfolder === "clean_invoices") {
      tagColor = "green";
      tagText = "Clean STP";
    } else if (s.png_filename?.includes("titan")) {
      tagColor = "yellow";
      tagText = "3-Way Shortage";
    } else if (s.png_filename?.includes("pacific")) {
      tagColor = "red";
      tagText = "Step PO Breach";
    } else if (s.subfolder === "purchase_orders") {
      tagColor = "teal";
      tagText = "PO Catalog";
    } else if (s.subfolder === "receipts") {
      tagColor = "purple";
      tagText = "T&E Receipt";
    }

    const docNum = s.invoice_number || s.po_number || s.receipt_number || "DOC";
    const entityName = s.vendor_name || s.buyer_name || s.merchant_name || "Vendor";
    const amt = `${s.currency} ${s.total_amount || s.total_authorized_amount || "0.00"}`;
    const terms = s.payment_terms || "Corporate Card";

    card.innerHTML = `
      <div class="cds--sample-card-top">
        <span class="cds--sample-number">${escapeHtml(docNum)}</span>
        <span class="cds--tag ${tagColor}">${tagText}</span>
      </div>
      <div class="cds--sample-card-main">
        <span class="cds--sample-vendor" title="${escapeHtml(entityName)}">${escapeHtml(entityName)}</span>
        <span class="cds--sample-amount">${escapeHtml(amt)}</span>
      </div>
      <div class="cds--sample-card-bottom">
        <span>Terms: ${escapeHtml(terms)}</span>
        <a class="cds--sample-preview-btn" href="/samples/${s.png_filename}" target="_blank" rel="noopener" onclick="event.stopPropagation()">
          Preview PNG &nearr;
        </a>
      </div>
    `;

    card.addEventListener("click", () => {
      selectSampleInvoice(
        s.png_filename,
        `[${tagText}] ${docNum} — ${entityName} (${amt})`
      );
    });

    sampleButtonsContainer.appendChild(card);
  });
}

// ============================================================================
// TELEMETRY STEPPER CONTROLLER
// ============================================================================
function setTelemetryRunning() {
  telemetryElapsed.textContent = "Processing on watsonx Orchestrate...";
  const items = telemetrySteps.querySelectorAll(".cds--step-item");
  items.forEach((li, i) => {
    li.classList.remove("completed", "running", "error");
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
  telemetryList.forEach((step, idx) => {
    const li = document.createElement("li");
    const isSuccess = step.status === "completed";
    li.className = `cds--step-item ${isSuccess ? "completed" : "running"}`;
    li.innerHTML = `
      <div class="cds--step-node">${isSuccess ? "&#10003;" : idx + 1}</div>
      <div class="cds--step-content">
        <div class="cds--step-name">
          <span>${escapeHtml(step.name)}</span>
          <span class="cds--step-time">${step.duration_ms} ms</span>
        </div>
        <div class="cds--step-detail">
          <code>${escapeHtml(step.endpoint)}</code> &mdash; ${escapeHtml(step.detail || "")}
        </div>
      </div>
    `;
    telemetrySteps.appendChild(li);
  });
}

// ============================================================================
// RUN PIPELINE TRIGGER
// ============================================================================
runPipelineBtn?.addEventListener("click", async () => {
  if (!state.selectedFile && !state.selectedSampleFilename) {
    alert("Please select a sample document or drop an invoice file first.");
    return;
  }

  runPipelineBtn.disabled = true;
  const originalText = runBtnLabel.textContent;
  runBtnLabel.textContent = "Uploading to wxO S3 & Running docproc...";
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
    telemetryElapsed.textContent = "Execution Error";
    alert(`Pipeline Error: ${err.message}`);
  } finally {
    runPipelineBtn.disabled = false;
    runBtnLabel.textContent = originalText;
  }
});

// ============================================================================
// ACTIVE INVOICE WORKBENCH RENDERING
// ============================================================================
function setActiveInvoice(inv) {
  state.activeInvoice = inv;
  emptyStateBox.hidden = true;
  invoiceDetailsContainer.hidden = false;
  openInspectorModalBtn.disabled = false;

  const confPct = ((Number(inv.avg_confidence) || 0.98) * 100).toFixed(1);
  activeConfidenceBadge.hidden = false;
  activeConfidenceBadge.textContent = `${confPct}% WDU Confidence`;

  const docNum = inv.invoice_number || "N/A";
  const vendor = inv.vendor_name || "Vendor";
  const docType = inv.document_type || "Invoice";
  activeDocTitle.innerHTML = `2. ${escapeHtml(docType)}: <strong>${escapeHtml(docNum)}</strong> (${escapeHtml(vendor)})`;
  activeInvoiceSubtitle.textContent = `File: ${inv.file_name} | Channel: ${inv.source_channel || "web"} | Mode: ${inv.execution_mode} | SQLite Row #${inv.id}`;

  const audit = inv.audit || {};
  const poMatch = audit.po_match || {};
  const apAuto = audit.ap_automation || {};
  const riskShield = audit.risk_shield || {};

  // Risk Score Badge
  const rScore = riskShield.risk_score ?? 5;
  const rLevel = riskShield.risk_level || "LOW";
  activeRiskBadge.hidden = false;
  activeRiskBadge.textContent = `Risk: ${rScore}/100 (${rLevel})`;
  activeRiskBadge.className = `cds--tag ${rLevel === "HIGH" || rLevel === "CRITICAL" ? "red" : rLevel === "MEDIUM" ? "yellow" : "green"}`;

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

  tabPoStatusPill.className = `cds--tab-pill ${
    poMatch.status === "MATCHED"
      ? "cds--tag green"
      : poMatch.status === "VARIANCE_DETECTED"
      ? "cds--tag red"
      : "cds--tag gray"
  }`;

  if (tabApAutoPill) {
    const hasDebitMemo = Number(apAuto.debit_memo_deduction || 0) > 0;
    tabApAutoPill.textContent = hasDebitMemo
      ? `SHORT-PAY (${apAuto.debit_memo_number || "DM"})`
      : Number(apAuto.early_discount_savings || 0) > 0
      ? `SAVE ${inv.currency} ${Number(apAuto.early_discount_savings).toFixed(0)}`
      : "STP READY";
    tabApAutoPill.className = `cds--tab-pill ${hasDebitMemo ? "cds--tag yellow" : "cds--tag blue"}`;
  }

  tabRiskScorePill.textContent = `${rScore}/100`;
  tabRiskScorePill.className = `cds--tab-pill ${
    rLevel === "HIGH" || rLevel === "CRITICAL" ? "cds--tag red" : rLevel === "MEDIUM" ? "cds--tag yellow" : "cds--tag green"
  }`;

  // HITL Workbench Status Badges
  const tier = inv.approval_tier || "AUTO_APPROVED";
  hitlTierBadge.textContent = tier;
  hitlTierBadge.className = `cds--tag ${
    tier.includes("VP_APPROVAL")
      ? "yellow"
      : tier.includes("REJECTED") || tier.includes("FLAGGED")
      ? "red"
      : tier.includes("SHORT_PAID")
      ? "blue"
      : "green"
  }`;

  const odooState = (inv.odoo_state || "draft").toUpperCase();
  hitlOdooBadge.textContent = inv.odoo_bill_id
    ? `Odoo: ${odooState} (Bill #${inv.odoo_bill_id})`
    : `Odoo: Not Synced`;
  hitlOdooBadge.className = `cds--tag ${odooState === "POSTED" ? "green" : "blue"}`;

  // Render Sub-Views
  renderInteractiveBoundingBoxes(inv);
  renderStructuredHeaderKvps(inv);
  renderLineItems(inv.line_items || []);
  renderPoMatchingTab(inv, poMatch);
  renderApAutomationTab(inv, apAuto, poMatch);
  renderRiskShieldTab(inv, riskShield);
}

// ============================================================================
// TAB 1: VISUAL GROUNDING & BOUNDING BOX CANVAS
// ============================================================================
function renderInteractiveBoundingBoxes(inv) {
  const previewUrl =
    inv.preview_image_url ||
    (inv.file_name ? `/samples/${inv.file_name.replace(/\.pdf$/i, ".png")}` : "/samples/clean_invoices/invoice_acme_cloud_0042.png");

  const viewport = document.getElementById("docCanvasViewport");
  if (docEmptyNote) docEmptyNote.style.display = "none";

  const updateSvgViewBox = () => {
    const nw = docPreviewImg.naturalWidth || 1240;
    const nh = docPreviewImg.naturalHeight || (nw === 900 ? 1250 : 1600);
    docBboxSvg.setAttribute("viewBox", `0 0 ${nw} ${nh}`);
  };

  docPreviewImg.onerror = () => {
    if (docEmptyNote) docEmptyNote.style.display = "block";
    docBboxSvg.innerHTML = "";
  };
  docPreviewImg.onload = () => {
    updateSvgViewBox();
  };
  docPreviewImg.src = previewUrl;
  if (docPreviewImg.complete && docPreviewImg.naturalWidth) {
    updateSvgViewBox();
  }

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
    rect.setAttribute("rx", "1");
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
  structuredHeaderGrid.querySelectorAll(".cds--kvp-tile").forEach((tile) => {
    const key = tile.dataset.kvpKey;
    tile.addEventListener("mouseenter", () => {
      tile.classList.add("active-kvp");
      docBboxSvg.querySelectorAll(".bbox-rect").forEach((r) => {
        if (r.dataset.kvpLabel === key) {
          r.classList.add("active-bbox");
          bboxHoverStatus.textContent = `Highlighting '${key}' on document canvas`;
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
  lineItemsTbody.querySelectorAll("tr").forEach((row) => {
    const rowIdx = row.dataset.rowIndex;
    if (rowIdx === undefined) return;
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
    const row = lineItemsTbody.querySelector(`tr[data-row-index="${k.table_row_index}"]`);
    if (row) row.classList.add("active-line-row");
  } else {
    const tile = structuredHeaderGrid.querySelector(`.cds--kvp-tile[data-kvp-key="${k.label}"]`);
    if (tile) tile.classList.add("active-kvp");
  }
}

function clearFieldHighlights() {
  structuredHeaderGrid.querySelectorAll(".cds--kvp-tile").forEach((t) => t.classList.remove("active-kvp"));
  lineItemsTbody.querySelectorAll("tr").forEach((r) => r.classList.remove("active-line-row"));
}

function renderStructuredHeaderKvps(inv) {
  const fields = [
    { key: "invoice_number", label: "Invoice / Document #", val: inv.invoice_number || "N/A" },
    { key: "po_number", label: "Purchase Order #", val: inv.po_number || "None / N/A" },
    { key: "vendor_name", label: "Vendor / Supplier Name", val: inv.vendor_name || "—" },
    { key: "buyer_name", label: "Buyer / Customer Name", val: inv.buyer_name || "—" },
    { key: "invoice_date", label: "Invoice Date", val: inv.invoice_date || "—" },
    { key: "due_date", label: "Due Date", val: inv.due_date || "—" },
    { key: "payment_terms", label: "Payment Terms", val: inv.payment_terms || "Net 30" },
    { key: "currency", label: "Currency", val: inv.currency || "USD" },
    { key: "subtotal_amount", label: "Subtotal Amount", val: `${inv.currency} ${Number(inv.subtotal_amount || 0).toFixed(2)}` },
    { key: "tax_amount", label: "Tax Amount", val: `${inv.currency} ${Number(inv.tax_amount || 0).toFixed(2)}` },
    { key: "total_amount", label: "Total Amount Due", val: `${inv.currency} ${Number(inv.total_amount || 0).toFixed(2)}`, highlight: true },
  ];

  structuredHeaderGrid.innerHTML = fields
    .map(
      (f) => `
      <div class="cds--kvp-tile ${f.highlight ? "highlight" : ""}" data-kvp-key="${f.key}">
        <div class="cds--kvp-tile-label">
          <span>${escapeHtml(f.label)}</span>
          <span style="font-size:10px;color:var(--text-helper);">KVP</span>
        </div>
        <div class="cds--kvp-tile-value">${escapeHtml(f.val)}</div>
      </div>
    `
    )
    .join("");

  validationBanner.textContent = inv.validation_notes || "All extracted header values validated successfully.";
}

function renderLineItems(items) {
  if (!items || items.length === 0) {
    lineItemsTbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:16px;color:var(--text-secondary);">No line items extracted.</td></tr>`;
    return;
  }

  lineItemsTbody.innerHTML = items
    .map(
      (it, i) => `
      <tr data-row-index="${i}">
        <td>#${it.line_index || i + 1}</td>
        <td><strong>${escapeHtml(it.description || "Line Item")}</strong></td>
        <td>${escapeHtml(String(it.quantity || "1"))}</td>
        <td>${Number(it.unit_price || 0).toFixed(2)}</td>
        <td><strong>${Number(it.amount || 0).toFixed(2)}</strong></td>
        <td><span class="cds--tag blue">${escapeHtml(it.gl_category || "General Expense")}</span></td>
        <td>${Math.round((it.confidence || 0.98) * 100)}%</td>
      </tr>
    `
    )
    .join("");
}

// ============================================================================
// TAB 2: 3-WAY MATCHING & STEP PO GOVERNANCE
// ============================================================================
function renderPoMatchingTab(inv, poMatch) {
  const status = poMatch.status || "NO_PO";
  const twoWayStatus = poMatch.two_way_status || status;
  const threeWayStatus = poMatch.three_way_status || status;
  const simMode = poMatch.simulation_mode || "normal";

  // Highlight active simulation button
  document.querySelectorAll(".cds--btn-sim").forEach((btn) => {
    const bMode = btn.dataset.simMode || btn.dataset.sim || "normal";
    btn.classList.toggle("active", bMode === simMode);
  });

  poSummaryBanner.className = `cds--po-banner ${
    status === "VARIANCE_DETECTED" ? "variance" : status === "MATCHED" ? "" : "nopo"
  }`;
  poSummaryBanner.textContent = poMatch.summary || "No 3-Way PO/GRN comparison available.";

  const cur = inv.currency || "USD";
  const grnVariance = Number(poMatch.grn_variance ?? poMatch.subtotal_variance ?? 0);
  poKpiStrip.innerHTML = `
    <div class="cds--kvp-tile">
      <div class="cds--kvp-tile-label">PO Reference #</div>
      <div class="cds--kvp-tile-value">${escapeHtml(poMatch.po_number || "None")}</div>
    </div>
    <div class="cds--kvp-tile">
      <div class="cds--kvp-tile-label">Warehouse GRN / SES #</div>
      <div class="cds--kvp-tile-value">${escapeHtml(poMatch.grn_number || "N/A")} (${escapeHtml(poMatch.grn_date || "—")})</div>
    </div>
    <div class="cds--kvp-tile">
      <div class="cds--kvp-tile-label">Receiving Dock &amp; Inspector</div>
      <div class="cds--kvp-tile-value">${escapeHtml(poMatch.receiving_dock || "N/A")} — ${escapeHtml(poMatch.grn_inspector || "—")}</div>
    </div>
    <div class="cds--kvp-tile">
      <div class="cds--kvp-tile-label">2-Way Match (PO vs Inv)</div>
      <div class="cds--kvp-tile-value" style="color:${twoWayStatus === "MATCHED" ? "var(--cds-support-success)" : "var(--cds-support-danger)"};">
        ${escapeHtml(twoWayStatus)}
      </div>
    </div>
    <div class="cds--kvp-tile">
      <div class="cds--kvp-tile-label">3-Way Match (PO + GRN + Inv)</div>
      <div class="cds--kvp-tile-value" style="color:${threeWayStatus === "MATCHED" ? "var(--cds-support-success)" : "var(--cds-support-danger)"};">
        ${escapeHtml(threeWayStatus)}
      </div>
    </div>
    <div class="cds--kvp-tile">
      <div class="cds--kvp-tile-label">GRN Accepted Subtotal</div>
      <div class="cds--kvp-tile-value">${cur} ${Number(poMatch.grn_accepted_subtotal ?? poMatch.authorized_subtotal ?? 0).toFixed(2)}</div>
    </div>
    <div class="cds--kvp-tile">
      <div class="cds--kvp-tile-label">Billed Invoice Subtotal</div>
      <div class="cds--kvp-tile-value">${cur} ${Number(poMatch.billed_subtotal || 0).toFixed(2)}</div>
    </div>
    <div class="cds--kvp-tile ${Math.abs(grnVariance) > 0.05 ? "highlight" : ""}">
      <div class="cds--kvp-tile-label">3-Way Net Variance (vs GRN)</div>
      <div class="cds--kvp-tile-value" style="color:${Math.abs(grnVariance) > 0.05 ? "var(--cds-support-danger)" : "var(--cds-support-success)"};">
        ${grnVariance >= 0 ? "+" : ""}${cur} ${grnVariance.toFixed(2)} (${poMatch.grn_variance_pct ?? poMatch.variance_pct ?? 0}%)
      </div>
    </div>
  `;

  // Step PO Milestone Drawdown Tracker
  const stepPo = poMatch.step_po;
  if (!stepPo || !stepPo.steps) {
    stepPoSection.innerHTML = "";
  } else {
    const hasBreach = (stepPo.steps || []).some((s) =>
      ["STEP_CEILING_BREACH", "LOCKED_MILESTONE_VIOLATION"].includes(s.status)
    );
    const overallStatus = hasBreach ? "STEP_GATE_HOLD" : "STEP_VERIFIED";
    const overallTagColor = !hasBreach ? "green" : "red";
    const totalCap = Number(stepPo.total_contract_ceiling || 0);
    const totalDrawn = (stepPo.steps || []).reduce((acc, s) => acc + Number(s.billed_amount || 0), 0);
    const totalUtilPct = totalCap > 0 ? ((totalDrawn / totalCap) * 100).toFixed(1) : "100.0";

    const stepsHtml = (stepPo.steps || [])
      .map((s) => {
        const isCurrent = s.step_number === stepPo.current_step_number;
        const isBreach = ["STEP_CEILING_BREACH", "LOCKED_MILESTONE_VIOLATION"].includes(s.status);
        const tagClass =
          s.status === "COMPLETED_CLOSED"
            ? "blue"
            : s.status === "ACTIVE_VERIFIED"
            ? "green"
            : isBreach
            ? "red"
            : "gray";

        const barColor = isBreach
          ? "var(--cds-support-danger)"
          : s.status === "COMPLETED_CLOSED"
          ? "var(--cds-blue-60)"
          : "var(--cds-support-success)";

        return `
          <div class="cds--step-card ${isCurrent ? "active-step" : ""} ${isBreach ? "breach-step" : ""}">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span style="font-size:11px;font-weight:700;color:var(--text-secondary);">Step ${s.step_number}${isCurrent ? " &bull; ACTIVE TRANCHE" : ""}</span>
              <span class="cds--tag ${tagClass}">${escapeHtml(s.status)}</span>
            </div>
            <div style="font-size:13px;font-weight:600;color:var(--text-primary);margin-top:2px;">${escapeHtml(s.title)}</div>
            <div style="font-size:11px;color:var(--text-helper);">Gate Sign-Off: <strong>${escapeHtml(s.gate_requirement)}</strong></div>
            <div class="cds--step-progress-track" style="margin:4px 0;">
              <div class="cds--step-progress-fill" style="width:${Math.min(100, s.utilization_pct || 0)}%;background:${barColor};"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-secondary);">
              <span>Utilized: <strong>${cur} ${Number(s.billed_amount || 0).toFixed(2)}</strong> (${s.utilization_pct}%)</span>
              <span>Cap: <strong>${cur} ${Number(s.step_limit || 0).toFixed(2)}</strong></span>
            </div>
          </div>
        `;
      })
      .join("");

    stepPoSection.innerHTML = `
      <div style="background-color:var(--bg-surface-alt);border:1px solid var(--border-subtle);padding:14px 16px;margin-top:12px;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
          <div>
            <h4 style="font-size:13px;font-weight:600;color:var(--text-primary);">
              Step PO Milestone Governance Tracker &mdash; ${escapeHtml(stepPo.contract_master_id || "MSA")} (${escapeHtml(stepPo.po_type_label || stepPo.po_type)})
            </h4>
            <p style="font-size:12px;color:var(--text-helper);margin-top:2px;">
              Active: <strong>${escapeHtml(stepPo.current_step_name || "Step 1")}</strong> &bull; Total Drawn: ${cur} ${totalDrawn.toLocaleString()} / ${cur} ${totalCap.toLocaleString()} (${totalUtilPct}%)
            </p>
          </div>
          <div style="display:flex;gap:6px;">
            <span class="cds--tag ${overallTagColor}">Gate: ${overallStatus}</span>
          </div>
        </div>
        <div class="cds--step-cards-grid">${stepsHtml}</div>
      </div>
    `;
  }

  // Render 11-column 3-Way Match Matrix
  const lines = poMatch.line_comparisons || [];
  if (lines.length === 0) {
    poLinesTbody.innerHTML = `<tr><td colspan="11" style="text-align:center;padding:16px;color:var(--text-secondary);">No Purchase Order / GRN line-item baseline applicable for this document.</td></tr>`;
    return;
  }

  poLinesTbody.innerHTML = lines
    .map((l) => {
      const twoWayStr = l.two_way_status || l.status || "MATCHED";
      const threeWayStr = l.three_way_status || l.status || "3-WAY VERIFIED";
      const twoWayTag = twoWayStr === "2-WAY OK" || twoWayStr === "MATCHED" ? "green" : "red";
      const threeWayTag = threeWayStr === "3-WAY VERIFIED" || l.status === "MATCHED" ? "green" : "red";
      const grnQty = l.grn_qty ?? l.grn_accepted_qty ?? l.po_qty;
      const grnAmt = l.grn_amount ?? l.grn_accepted_amount ?? l.po_amount;
      const grnQtyMismatch = Math.abs(Number(l.inv_qty) - Number(grnQty)) > 0.01;

      return `
        <tr>
          <td>#${l.line_index}</td>
          <td>
            <strong>${escapeHtml(l.invoice_description)}</strong>
            ${l.grn_note ? `<div style="font-size:11px;color:var(--text-helper);margin-top:2px;">Dock Note: ${escapeHtml(l.grn_note)}</div>` : ""}
          </td>
          <td>${l.po_qty}</td>
          <td style="font-weight:700;color:${grnQtyMismatch ? "var(--cds-support-danger)" : "var(--cds-blue-70)"};">
            ${grnQty} ${grnQtyMismatch ? "⚠" : "✓"}
          </td>
          <td><strong>${l.inv_qty}</strong></td>
          <td>${cur} ${Number(l.po_unit_price).toFixed(2)}</td>
          <td>${cur} ${Number(l.inv_unit_price).toFixed(2)}</td>
          <td>${cur} ${Number(grnAmt).toFixed(2)}</td>
          <td><strong>${cur} ${Number(l.inv_amount).toFixed(2)}</strong></td>
          <td><span class="cds--tag ${twoWayTag}">${escapeHtml(twoWayStr)}</span></td>
          <td><span class="cds--tag ${threeWayTag}">${escapeHtml(threeWayStr)}</span></td>
        </tr>
      `;
    })
    .join("");
}

// ============================================================================
// TAB 3: AP AUTOMATION & PAYMENT RUN
// ============================================================================
function renderApAutomationTab(inv, apAuto, poMatch) {
  if (!apAuto || !apAuto.strategy) {
    apAutoBanner.innerHTML = "AP Payment Automation telemetry unavailable for this document.";
    apWaterfallGrid.innerHTML = "";
    apJournalTbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:16px;color:var(--text-secondary);">No GL entries generated.</td></tr>`;
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

  apAutoBanner.className = `cds--notification-banner ${hasDebitMemo ? "shortpay" : "ready"}`;
  apAutoBanner.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
      <div>
        <div style="font-size:11px;text-transform:uppercase;font-weight:700;color:var(--text-secondary);">
          Autonomous AP Settlement Strategy &bull; Payment Rail: ${escapeHtml(apAuto.payment_method || "Automated ACH / ISO-20022 Wire")}
        </div>
        <div style="font-size:14px;font-weight:700;margin-top:2px;">${escapeHtml(apAuto.strategy_label || strat)}</div>
        <div style="font-size:12px;margin-top:2px;">${escapeHtml(apAuto.recommendation || "")}</div>
      </div>
      <span class="cds--tag ${hasDebitMemo ? "yellow" : "green"}">${escapeHtml(strat)}</span>
    </div>
  `;

  apWaterfallGrid.innerHTML = `
    <div class="cds--waterfall-card">
      <div class="cds--kpi-label">1. Vendor Billed Gross</div>
      <div class="cds--waterfall-val">${cur} ${grossBilled.toFixed(2)}</div>
      <div class="cds--kpi-sub">Original Invoice Claim</div>
    </div>
    <div class="cds--waterfall-card ${hasDebitMemo ? "shortpay" : ""}">
      <div class="cds--kpi-label">2. Auto Debit Memo</div>
      <div class="cds--waterfall-val" style="color:${hasDebitMemo ? "var(--cds-support-danger)" : "var(--text-helper)"};">
        -${cur} ${dmDeduction.toFixed(2)}
      </div>
      <div class="cds--kpi-sub">
        ${hasDebitMemo ? `Ref: <strong>${escapeHtml(apAuto.debit_memo_number)}</strong>` : "No Dock Shortage"}
      </div>
    </div>
    <div class="cds--waterfall-card">
      <div class="cds--kpi-label">3. Verified Gross Payable</div>
      <div class="cds--waterfall-val">${cur} ${verifiedGross.toFixed(2)}</div>
      <div class="cds--kpi-sub">Goods Received + Pro-Rata Tax</div>
    </div>
    <div class="cds--waterfall-card">
      <div class="cds--kpi-label">4. Early-Pay Discount (${escapeHtml(apAuto.discount_terms || "2/10 Net 30")})</div>
      <div class="cds--waterfall-val" style="color:var(--cds-support-success);">
        -${cur} ${earlySavings.toFixed(2)}
      </div>
      <div class="cds--kpi-sub">
        ${earlySavings > 0 ? `${apAuto.discount_pct}% Yield (${apAuto.annualized_yield_apr || 36.7}% APR ROI)` : "Standard Net 30 Terms"}
      </div>
    </div>
    <div class="cds--waterfall-card final">
      <div class="cds--kpi-label">5. Final Net AP Wire</div>
      <div class="cds--waterfall-val" style="color:var(--cds-blue-60);">
        ${cur} ${finalNet.toFixed(2)}
      </div>
      <div class="cds--kpi-sub">Net 30 Fallback: ${cur} ${verifiedGross.toFixed(2)}</div>
    </div>
  `;

  apActionInfo.innerHTML = `
    <strong>Automated Settlement &amp; Odoo Posting:</strong>
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
    apJournalTbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:16px;color:var(--text-secondary);">No GL postings generated.</td></tr>`;
  } else {
    apJournalTbody.innerHTML = entries
      .map((j) => {
        const eType = j.type || j.entry_type || "DEBIT";
        const tagClass = eType === "DEBIT" ? "blue" : eType === "CREDIT" ? "green" : "yellow";
        return `
          <tr>
            <td><strong>${escapeHtml(j.account_code || j.gl_code)}</strong></td>
            <td>
              ${escapeHtml(j.account_name)}
              ${j.memo ? `<div style="font-size:11px;color:var(--text-helper);">${escapeHtml(j.memo)}</div>` : ""}
            </td>
            <td><span class="cds--tag ${tagClass}">${escapeHtml(eType)}</span></td>
            <td>${j.debit > 0 ? `<strong>${cur} ${Number(j.debit).toFixed(2)}</strong>` : "—"}</td>
            <td>${j.credit > 0 ? `<strong>${cur} ${Number(j.credit).toFixed(2)}</strong>` : "—"}</td>
          </tr>
        `;
      })
      .join("");
  }
}

// ============================================================================
// TAB 4: FRAUD & COMPLIANCE SHIELD
// ============================================================================
function renderRiskShieldTab(inv, riskShield) {
  const score = riskShield.risk_score ?? 5;
  const level = riskShield.risk_level || "LOW";
  const gaugeClass = level === "HIGH" ? "high" : level === "MEDIUM" ? "medium" : "";

  riskOverviewHeader.innerHTML = `
    <div>
      <h3 style="font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:2px;">
        Enterprise AP Fraud, Duplicate &amp; Split-Invoice Forensic Shield
      </h3>
      <p style="font-size:12px;color:var(--text-secondary);">
        Automated 5-point audit across SQLite historical ledger, Master ERP PO registry, and WDU OCR telemetry.
      </p>
    </div>
    <div class="cds--risk-gauge ${gaugeClass}">
      Risk Score: ${score} / 100 (${level})
    </div>
  `;

  const checks = riskShield.checks || [];
  riskChecksGrid.innerHTML = checks
    .map(
      (c) => `
      <div class="cds--risk-check-card ${c.status}">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <strong style="font-size:12px;color:var(--text-primary);">${escapeHtml(c.title)}</strong>
          <span class="cds--tag ${c.status === "PASS" ? "green" : c.status === "WARN" ? "yellow" : "red"}">${escapeHtml(c.status)}</span>
        </div>
        <div style="font-size:12px;color:var(--text-secondary);line-height:1.4;">${escapeHtml(c.detail)}</div>
      </div>
    `
    )
    .join("");
}

// ============================================================================
// 3-WAY GRN & STEP PO SCENARIO LAB EVENT LISTENERS
// ============================================================================
document.querySelectorAll(".cds--btn-sim").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!state.activeInvoice) return;
    const inv = state.activeInvoice;
    const mode = btn.dataset.simMode || btn.dataset.sim || "normal";
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

executeApRunBtn?.addEventListener("click", async () => {
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

// ============================================================================
// HITL ACTIONS: APPROVE IN ODOO / EDIT FIELDS / DISPUTE EMAIL
// ============================================================================
approvePostOdooBtn?.addEventListener("click", async () => {
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

openEditFieldsBtn?.addEventListener("click", () => {
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

cancelEditFieldsBtn?.addEventListener("click", () => editFieldsDialog.close());

editFieldsForm?.addEventListener("submit", async (e) => {
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

openDisputeModalBtn?.addEventListener("click", () => {
  if (!state.activeInvoice) return;
  const inv = state.activeInvoice;
  const poSummary = inv.audit?.po_match?.summary || "";
  const mathNote = inv.math_summary || inv.validation_notes || "";
  document.getElementById("disputeReason").value =
    `Dispute raised for ${inv.invoice_number} (${inv.vendor_name}, ${inv.currency} ${Number(inv.total_amount).toFixed(2)}).\n` +
    `2-Way PO Match Finding: ${poSummary}\n` +
    `Audit Finding: ${mathNote}\n` +
    `Please issue a revised invoice or credit memo referencing PO ${inv.po_number || "N/A"}.`;
  disputeDialog.showModal();
});

cancelDisputeBtn?.addEventListener("click", () => disputeDialog.close());

disputeForm?.addEventListener("submit", async (e) => {
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
    alert(`Formatted HTML AP Dispute Notice dispatched to ${data.recipient} via Gmail SMTP and marked REJECTED_DISPUTED!`);
  } catch (err) {
    alert(`Dispute Error: ${err.message}`);
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "Send Dispute Email & Mark Disputed";
  }
});

// ============================================================================
// SQLITE LEDGER TABLE RENDERING & FILTERING
// ============================================================================
function getFilteredInvoices() {
  const query = (sqliteSearchInput?.value || "").toLowerCase().trim();
  const filterTier = sqliteFilterSelect?.value || "all";

  return state.invoices.filter((inv) => {
    if (filterTier !== "all") {
      if (filterTier === "AUTO_APPROVED" && inv.approval_tier !== "AUTO_APPROVED") return false;
      if (filterTier === "APPROVED_BY_VP" && inv.approval_tier !== "APPROVED_BY_VP") return false;
      if (filterTier === "AUTO_SHORT_PAID_DEBIT_MEMO" && inv.approval_tier !== "AUTO_SHORT_PAID_DEBIT_MEMO") return false;
      if (filterTier === "REJECTED_DISPUTED" && inv.approval_tier !== "REJECTED_DISPUTED") return false;
    }
    if (!query) return true;
    const invNum = (inv.invoice_number || "").toLowerCase();
    const vendor = (inv.vendor_name || "").toLowerCase();
    const docType = (inv.document_type || "").toLowerCase();
    const tier = (inv.approval_tier || "").toLowerCase();
    const odoo = (inv.odoo_state || "").toLowerCase();
    return (
      invNum.includes(query) ||
      vendor.includes(query) ||
      docType.includes(query) ||
      tier.includes(query) ||
      odoo.includes(query)
    );
  });
}

function renderSqliteTable() {
  const filtered = getFilteredInvoices();
  dbRecordCount.textContent = `${filtered.length} of ${state.invoices.length} records`;

  if (filtered.length === 0) {
    sqliteInvoicesTbody.innerHTML = `<tr><td colspan="10" style="text-align:center;padding:24px;color:var(--text-secondary);">No documents match filter criteria.</td></tr>`;
    return;
  }

  sqliteInvoicesTbody.innerHTML = filtered
    .map((inv) => {
      const isSelected = state.activeInvoice && state.activeInvoice.id === inv.id;
      const poMatch = inv.audit?.po_match || {};
      const poStatus = poMatch.status || "MATCHED";
      const twoWay = poMatch.two_way_status || poStatus;
      const threeWay = poMatch.three_way_status || poStatus;

      let poBadgeClass = "green";
      let poBadgeLabel = "3-Way Matched";
      if (twoWay === "MATCHED" && threeWay === "VARIANCE_DETECTED") {
        poBadgeClass = "yellow";
        poBadgeLabel = "GRN Shortage";
      } else if (poStatus === "VARIANCE_DETECTED") {
        poBadgeClass = "red";
        poBadgeLabel = "PO Variance";
      } else if (poStatus === "NO_PO") {
        poBadgeClass = "gray";
        poBadgeLabel = "Direct Expense";
      }

      const rScore = inv.audit?.risk_shield?.risk_score ?? 5;
      const rLevel = inv.audit?.risk_shield?.risk_level || "LOW";
      const riskClass = rLevel === "HIGH" ? "red" : rLevel === "MEDIUM" ? "yellow" : "green";

      const tier = inv.approval_tier || "AUTO_APPROVED";
      let tierTagClass = "green";
      let tierLabel = "Auto-Approved";
      if (tier === "VP_APPROVAL_REQUIRED") {
        tierTagClass = "yellow";
        tierLabel = "VP Review";
      } else if (tier === "REJECTED_DISPUTED") {
        tierTagClass = "red";
        tierLabel = "Disputed";
      } else if (tier === "AUTO_SHORT_PAID_DEBIT_MEMO") {
        tierTagClass = "blue";
        tierLabel = "Short-Paid (DM)";
      } else if (tier === "APPROVED_BY_VP") {
        tierTagClass = "blue";
        tierLabel = "VP Approved";
      }

      const odooState = (inv.odoo_state || "draft").toUpperCase();
      const odooBadge = inv.odoo_bill_id
        ? `<a href="${escapeHtml(inv.odoo_url || "https://invoiceprocessing.odoo.com")}" target="_blank" rel="noopener" class="cds--tag ${odooState === "POSTED" ? "green" : "blue"}" style="text-decoration:none;" onclick="event.stopPropagation()">Bill #${inv.odoo_bill_id} (${odooState}) &nearr;</a>`
        : `<button type="button" class="cds--btn-mini sync-odoo-btn" data-id="${inv.id}" onclick="event.stopPropagation()">Sync Odoo</button>`;

      return `
        <tr class="clickable-row ${isSelected ? "selected-row" : ""}" data-id="${inv.id}">
          <td>#${inv.id}</td>
          <td><span class="cds--tag blue">${escapeHtml(inv.document_type || "Invoice")}</span></td>
          <td><strong>${escapeHtml(inv.invoice_number || "N/A")}</strong></td>
          <td>${escapeHtml(inv.vendor_name || "—")}</td>
          <td><strong>${escapeHtml(inv.currency)} ${Number(inv.total_amount).toFixed(2)}</strong></td>
          <td><span class="cds--tag ${poBadgeClass}">${poBadgeLabel}</span></td>
          <td><span class="cds--tag ${riskClass}">${rScore}/100</span></td>
          <td><span class="cds--tag ${tierTagClass}">${tierLabel}</span></td>
          <td>${odooBadge}</td>
          <td>
            <button type="button" class="cds--btn-mini delete-row-btn" data-id="${inv.id}" title="Delete Record">✕</button>
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
      const inv = state.invoices.find((x) => x.id === id);
      if (inv) {
        setActiveInvoice(inv);
        sqliteInvoicesTbody.querySelectorAll("tr.clickable-row").forEach((r) => r.classList.remove("selected-row"));
        tr.classList.add("selected-row");
      }
    });
  });

  sqliteInvoicesTbody.querySelectorAll(".delete-row-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      const id = Number(btn.dataset.id);
      if (!confirm(`Delete document record #${id} from SQLite database?`)) return;
      try {
        const res = await fetch(`/api/invoices/${id}`, { method: "DELETE" });
        if (!res.ok) throw new Error("Delete failed");
        await refreshInvoicesList();
      } catch (err) {
        alert(`Error deleting record: ${err.message}`);
      }
    });
  });
}

sqliteSearchInput?.addEventListener("input", () => renderSqliteTable());
sqliteFilterSelect?.addEventListener("change", () => renderSqliteTable());
sqliteRefreshBtn?.addEventListener("click", () => refreshInvoicesList());

// ============================================================================
// TAB 5 & HEADER: INTERACTIVE DEMO SCENARIO SHORTCUTS
// ============================================================================
window.loadDemoScenario = async function (scenarioKey) {
  let targetFile = "";
  let targetTab = "tabVisualGrounding";
  let targetDocNum = "";

  if (scenarioKey === "clean") {
    targetFile = "clean_invoices/invoice_acme_cloud_0042.png";
    targetDocNum = "INV-2026-0042";
    targetTab = "tabVisualGrounding";
  } else if (scenarioKey === "shortage") {
    targetFile = "variance_invoices/invoice_titan_hypercompute_7731.png";
    targetDocNum = "INV-2026-7731";
    targetTab = "tabPoMatching";
  } else if (scenarioKey === "breach") {
    targetFile = "variance_invoices/invoice_pacific_cyber_2045.png";
    targetDocNum = "INV-2026-2045";
    targetTab = "tabPoMatching";
  } else if (scenarioKey === "receipt") {
    targetFile = "receipts/receipt_cloud_summit_9041.png";
    targetDocNum = "REC-2026-9041";
    targetTab = "tabVisualGrounding";
  }

  // If Demo Guide Modal is open, close it cleanly so user sees the workbench
  if (demoGuideModalDialog && demoGuideModalDialog.open) {
    demoGuideModalDialog.close();
  }

  // Ensure left panel is on sample library and category is visible
  setIngestionTab("samples");
  state.selectedFilterCategory = "all";
  document.querySelectorAll(".cds--filter-chip").forEach((chip) => {
    chip.classList.toggle("active", chip.dataset.filter === "all");
  });
  renderFilteredSampleCards();
  selectSampleInvoice(targetFile);

  // If already in state.invoices, activate and switch tab
  const found = state.invoices.find(
    (inv) =>
      inv.invoice_number === targetDocNum ||
      (inv.file_name && targetFile.includes(inv.file_name))
  );

  if (found) {
    setActiveInvoice(found);
    switchTab(targetTab);
    const workbenchEl = document.querySelector(".cds--workbench-header") || document.getElementById(targetTab);
    workbenchEl?.scrollIntoView({ behavior: "smooth", block: "start" });
  } else {
    // If not in database yet, trigger IDP pipeline
    switchTab(targetTab);
    runPipelineBtn.click();
  }
};

// ============================================================================
// RAW WDU INSPECTOR MODAL POPULATION
// ============================================================================
openInspectorModalBtn?.addEventListener("click", () => {
  if (!state.activeInvoice) return;
  populateInspectorDialog(state.activeInvoice);
  rawInspectorDialog.showModal();
});

function populateInspectorDialog(inv) {
  dialogS3Url.textContent = inv.s3_url || "Not stored in COS";
  dialogFlowId.textContent = state.healthInfo?.flow_id || "513e67d6...";
  dialogAgentId.textContent = state.healthInfo?.agent_id || "23215e30...";
  dialogThreadId.textContent = inv.wxo_thread_id || "direct_flow_headless";

  const rawKvps = inv.raw_kvps || [];
  if (rawKvps.length === 0) {
    dialogRawKvpsTbody.innerHTML = `<tr><td colspan="4" style="text-align:center;padding:16px;">No raw KVP nodes available.</td></tr>`;
  } else {
    dialogRawKvpsTbody.innerHTML = rawKvps
      .map((k) => {
        const bboxStr = k.bbox ? `${k.bbox.x}, ${k.bbox.y}, ${k.bbox.width}, ${k.bbox.height}` : "—";
        return `
          <tr>
            <td><code>${escapeHtml(k.id || "node")}</code></td>
            <td><strong>${escapeHtml(k.label || "field")}</strong></td>
            <td>${escapeHtml(k.value || "—")}</td>
            <td><code>${escapeHtml(bboxStr)}</code></td>
          </tr>
        `;
      })
      .join("");
  }

  dialogOcrText.textContent = inv.extracted_text || "No OCR Markdown text emitted by WDU docproc.";
}

// Gmail Ingestion Trigger
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

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Launch app
initApp();
