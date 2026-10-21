/**
 * IBM watsonx Orchestrate IDP Client Demo Application Logic.
 */

const state = {
  selectedFile: null,
  selectedSample: null,
  activeDocument: null,
  history: [],
  samples: [],
  currentKvps: [],
};

// DOM Elements
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const selectedFileLabel = document.getElementById("selectedFileLabel");
const samplePillsContainer = document.getElementById("samplePillsContainer");
const runBtn = document.getElementById("runBtn");
const runBtnLabel = document.getElementById("runBtnLabel");
const stepperList = document.getElementById("stepperList");
const wxoStatusTag = document.getElementById("wxoStatusTag");
const flowIdTag = document.getElementById("flowIdTag");

// Result Elements
const docTypeBadge = document.getElementById("docTypeBadge");
const approvalTierBadge = document.getElementById("approvalTierBadge");
const metricInvNum = document.getElementById("metricInvNum");
const metricVendor = document.getElementById("metricVendor");
const metricBuyer = document.getElementById("metricBuyer");
const metricDate = document.getElementById("metricDate");
const metricTotal = document.getElementById("metricTotal");
const metricConf = document.getElementById("metricConf");

// Audit Banner
const auditBanner = document.getElementById("auditBanner");
const auditIcon = document.getElementById("auditIcon");
const auditTitle = document.getElementById("auditTitle");
const auditSub = document.getElementById("auditSub");

// Tabs & Content
const lineItemsTbody = document.getElementById("lineItemsTbody");
const kvpGrid = document.getElementById("kvpGrid");
const kvpSearchInput = document.getElementById("kvpSearchInput");
const ocrTextBox = document.getElementById("ocrTextBox");
const rawJsonBox = document.getElementById("rawJsonBox");
const historyTbody = document.getElementById("historyTbody");
const historyCount = document.getElementById("historyCount");

// 1. Initialize
async function init() {
  setupEventListeners();
  await checkHealth();
  await loadSamples();
  await loadHistory();
}

// 2. Health check
async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    if (res.ok) {
      const data = await res.json();
      wxoStatusTag.textContent = "Connected to wxO";
      flowIdTag.textContent = `Flow: ${data.flow_name || "invoice_idp_flow"}`;
    }
  } catch (err) {
    wxoStatusTag.textContent = "Offline Mode";
    wxoStatusTag.style.background = "#da1e28";
  }
}

// 3. Load samples
async function loadSamples() {
  try {
    const res = await fetch("/api/samples");
    if (!res.ok) return;
    const data = await res.json();
    state.samples = data.samples || [];

    samplePillsContainer.innerHTML = state.samples
      .map(
        (s) => `
        <button type="button" class="sample-pill-btn" data-filename="${s.filename}">
          <span>📄</span>
          <span>${escapeHtml(s.title)}</span>
          <span style="font-size:0.65rem;opacity:0.75;">(${s.document_type})</span>
        </button>
      `
      )
      .join("");

    samplePillsContainer.querySelectorAll(".sample-pill-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const fname = btn.dataset.filename;
        selectSample(fname);
      });
    });

    // Auto-select first sample
    if (state.samples.length > 0) {
      selectSample(state.samples[0].filename);
    }
  } catch (err) {
    console.warn("Could not load samples", err);
  }
}

function selectSample(filename) {
  state.selectedSample = filename;
  state.selectedFile = null;
  selectedFileLabel.textContent = `Sample: ${filename}`;
  samplePillsContainer.querySelectorAll(".sample-pill-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.filename === filename);
  });
}

// 4. File drag & drop
function setupEventListeners() {
  dropZone.addEventListener("click", () => fileInput.click());

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      state.selectedFile = e.target.files[0];
      state.selectedSample = null;
      selectedFileLabel.textContent = `Uploaded: ${state.selectedFile.name}`;
      samplePillsContainer.querySelectorAll(".sample-pill-btn").forEach((b) => b.classList.remove("active"));
    }
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      state.selectedFile = e.dataTransfer.files[0];
      state.selectedSample = null;
      selectedFileLabel.textContent = `Uploaded: ${state.selectedFile.name}`;
      samplePillsContainer.querySelectorAll(".sample-pill-btn").forEach((b) => b.classList.remove("active"));
    }
  });

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      const targetId = btn.dataset.tab;
      const target = document.getElementById(targetId);
      if (target) target.classList.add("active");
    });
  });

  // KVP search
  if (kvpSearchInput) {
    kvpSearchInput.addEventListener("input", (e) => {
      renderKvps(e.target.value.trim().toLowerCase());
    });
  }

  // Run pipeline
  runBtn.addEventListener("click", runPipeline);
}

// 5. Run Pipeline
async function runPipeline() {
  if (!state.selectedFile && !state.selectedSample) {
    alert("Please select a sample document or upload a PDF/PNG file.");
    return;
  }

  const execMode = document.querySelector('input[name="execMode"]:checked').value;
  setProcessingState(true);
  resetStepper();

  const formData = new FormData();
  formData.append("execution_mode", execMode);
  if (state.selectedFile) {
    formData.append("file", state.selectedFile);
  } else {
    formData.append("sample_filename", state.selectedSample);
  }

  try {
    // Animate stepper step 1
    setStep(1, "active");

    const timer1 = setTimeout(() => {
      setStep(1, "completed");
      setStep(2, "active");
    }, 1200);

    const timer2 = setTimeout(() => {
      setStep(2, "completed");
      setStep(3, "active");
    }, 4500);

    const timer3 = setTimeout(() => {
      setStep(3, "completed");
      setStep(4, "active");
    }, 8500);

    const res = await fetch("/api/process", {
      method: "POST",
      body: formData,
    });

    clearTimeout(timer1);
    clearTimeout(timer2);
    clearTimeout(timer3);

    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error(`Server returned status ${res.status}`);
    }

    if (!res.ok) {
      throw new Error(data.detail || "Pipeline processing failed");
    }

    // Complete all steps
    setStep(1, "completed");
    setStep(2, "completed");
    setStep(3, "completed");
    setStep(4, "completed");
    setStep(5, "completed");

    renderResult(data);
    await loadHistory();

  } catch (err) {
    alert(`Pipeline Error: ${err.message}`);
    resetStepper();
  } finally {
    setProcessingState(false);
  }
}

function setProcessingState(isProcessing) {
  runBtn.disabled = isProcessing;
  runBtnLabel.textContent = isProcessing
    ? "Processing via watsonx Orchestrate..."
    : "Upload to wxO S3 & Run IDP Pipeline";
}

function resetStepper() {
  stepperList.querySelectorAll(".step-item").forEach((step) => {
    step.className = "step-item pending";
  });
}

function setStep(stepNumber, stateClass) {
  const item = stepperList.querySelector(`[data-step="${stepNumber}"]`);
  if (item) {
    item.className = `step-item ${stateClass}`;
  }
}

// 6. Render Result
function renderResult(data) {
  const doc = data.document || {};
  const struct = data.structured_invoice || {};
  const logic = data.logic_summary || {};
  state.currentKvps = data.kvps || [];

  // Badges
  docTypeBadge.textContent = doc.document_type || "Invoice";
  approvalTierBadge.textContent = doc.approval_tier || "AUTO_APPROVED";

  if (doc.approval_tier === "AUTO_APPROVED") {
    approvalTierBadge.style.background = "#198038";
  } else if (doc.approval_tier === "VP_APPROVAL_REQUIRED") {
    approvalTierBadge.style.background = "#f1c21b";
    approvalTierBadge.style.color = "#161616";
  } else {
    approvalTierBadge.style.background = "#da1e28";
  }

  // Summary Metrics
  metricInvNum.textContent = doc.invoice_number || "—";
  metricVendor.textContent = doc.vendor_name || "—";
  metricBuyer.textContent = doc.buyer_name || "—";
  metricDate.textContent = doc.invoice_date || "—";
  metricTotal.textContent = `${doc.currency || "USD"} ${Number(doc.total_amount || 0).toFixed(2)}`;
  metricConf.textContent = `${((doc.avg_confidence || 0.98) * 100).toFixed(0)}%`;

  // Audit Banner
  if (doc.approval_tier === "AUTO_APPROVED") {
    auditBanner.className = "audit-banner";
    auditIcon.textContent = "✓";
    auditTitle.textContent = "Deterministic Math Audit Passed — AUTO_APPROVED";
    auditSub.textContent = doc.validation_notes || "Subtotal + Tax matches Total Amount. Zero math hallucination.";
  } else if (doc.approval_tier === "VP_APPROVAL_REQUIRED") {
    auditBanner.className = "audit-banner warning";
    auditIcon.textContent = "⚠";
    auditTitle.textContent = "High-Value Threshold Exceeded — VP_APPROVAL_REQUIRED";
    auditSub.textContent = doc.validation_notes || "Total exceeds $25,000 corporate threshold. Routed for VP approval.";
  } else {
    auditBanner.className = "audit-banner error";
    auditIcon.textContent = "✖";
    auditTitle.textContent = "Calculation Discrepancy — FLAGGED_MATH_MISMATCH";
    auditSub.textContent = doc.validation_notes || "Discrepancy detected between line items and total.";
  }

  // Line items
  const items = doc.line_items || [];
  if (items.length === 0) {
    lineItemsTbody.innerHTML = `<tr><td colspan="6" class="empty-cell">No line items extracted.</td></tr>`;
  } else {
    lineItemsTbody.innerHTML = items
      .map(
        (it) => `
      <tr>
        <td><strong>${it.line_index}</strong></td>
        <td>${escapeHtml(it.description)}</td>
        <td>${escapeHtml(it.quantity)}</td>
        <td>$${Number(it.unit_price).toFixed(2)}</td>
        <td><strong>$${Number(it.amount).toFixed(2)}</strong></td>
        <td><span class="gl-badge">${escapeHtml(it.gl_category || "General")}</span></td>
      </tr>
    `
      )
      .join("");
  }

  // KVPs
  renderKvps("");

  // OCR Text
  ocrTextBox.textContent = data.extracted_text || "No OCR text returned.";

  // Raw JSON
  rawJsonBox.textContent = JSON.stringify(data, null, 2);
}

function renderKvps(filter) {
  const filtered = state.currentKvps.filter(
    (k) => !filter || k.key.toLowerCase().includes(filter) || k.value.toLowerCase().includes(filter)
  );

  if (filtered.length === 0) {
    kvpGrid.innerHTML = `<div style="grid-column: 1/-1; padding: 20px; text-align: center; color: #8d8d8d;">No key-value pairs matching "${escapeHtml(filter)}".</div>`;
    return;
  }

  kvpGrid.innerHTML = filtered
    .map(
      (k) => `
    <div class="kvp-card">
      <div class="kvp-key-row">
        <span class="kvp-key">${escapeHtml(k.key)}</span>
        <span class="kvp-conf">${(Number(k.confidence || 0.98) * 100).toFixed(0)}%</span>
      </div>
      <div class="kvp-val">${escapeHtml(k.value || "—")}</div>
    </div>
  `
    )
    .join("");
}

// 7. Load History
async function loadHistory() {
  try {
    const res = await fetch("/api/invoices");
    if (!res.ok) return;
    const data = await res.json();
    state.history = data.documents || [];
    historyCount.textContent = `${state.history.length} records`;

    if (state.history.length === 0) {
      historyTbody.innerHTML = `<tr><td colspan="8" class="empty-cell">No documents saved yet.</td></tr>`;
      return;
    }

    historyTbody.innerHTML = state.history
      .map(
        (doc) => `
      <tr style="cursor: pointer;" data-id="${doc.id}">
        <td>#${doc.id}</td>
        <td><span class="badge-tag">${escapeHtml(doc.document_type || "Invoice")}</span></td>
        <td><strong>${escapeHtml(doc.invoice_number)}</strong></td>
        <td>${escapeHtml(doc.vendor_name || "—")}</td>
        <td><strong>${escapeHtml(doc.currency)} ${Number(doc.total_amount).toFixed(2)}</strong></td>
        <td><span style="font-weight:600;font-size:0.75rem;">${escapeHtml(doc.approval_tier)}</span></td>
        <td>${((doc.avg_confidence || 0.98) * 100).toFixed(0)}%</td>
        <td>
          <button type="button" class="btn-mini delete-doc-btn" data-id="${doc.id}">Delete</button>
        </td>
      </tr>
    `
      )
      .join("");

    historyTbody.querySelectorAll("tr").forEach((row) => {
      row.addEventListener("click", (e) => {
        if (e.target.classList.contains("delete-doc-btn")) return;
        const id = Number(row.dataset.id);
        const doc = state.history.find((d) => d.id === id);
        if (doc) {
          renderResult({
            document: doc,
            structured_invoice: doc,
            logic_summary: {
              math_summary: doc.math_summary,
              approval_tier: doc.approval_tier,
            },
            kvps: doc.raw_kvps || [],
            extracted_text: doc.extracted_text,
          });
        }
      });
    });

    historyTbody.querySelectorAll(".delete-doc-btn").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const id = btn.dataset.id;
        if (confirm(`Delete document #${id}?`)) {
          await fetch(`/api/invoices/${id}`, { method: "DELETE" });
          await loadHistory();
        }
      });
    });
  } catch (err) {
    console.warn("Could not load history", err);
  }
}

function escapeHtml(str) {
  if (typeof str !== "string") return String(str ?? "");
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

document.addEventListener("DOMContentLoaded", init);
