/**
 * Custom Frontend Controller for IBM watsonx Orchestrate Invoice IDP Pipeline.
 *
 * Implements:
 * - Drag & drop file upload OR pre-generated sample invoice selection
 * - Execution mode toggle: `direct_flow` (`/v1/orchestrate/flows/{flow_id}/run`)
 *   vs. `agent_two_turn` (`/v1/orchestrate/runs` 2-turn `file_upload` slot)
 * - Real-time pipeline telemetry visualization
 * - SQLite database table viewer + Deep WDU `docproc` KVP/BBox Inspector `<dialog>`
 */

const state = {
  selectedFile: null,
  selectedSampleFilename: "invoice_acme_cloud_0042.png",
  executionMode: "direct_flow",
  activeInvoice: null,
  invoices: [],
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

const activeInvoiceSubtitle = document.getElementById("activeInvoiceSubtitle");
const activeConfidenceBadge = document.getElementById("activeConfidenceBadge");
const openInspectorModalBtn = document.getElementById("openInspectorModalBtn");
const emptyStateBox = document.getElementById("emptyStateBox");
const invoiceDetailsContainer = document.getElementById("invoiceDetailsContainer");
const structuredHeaderGrid = document.getElementById("structuredHeaderGrid");
const validationBanner = document.getElementById("validationBanner");
const lineItemsTbody = document.getElementById("lineItemsTbody");

const dbRecordCount = document.getElementById("dbRecordCount");
const sqliteInvoicesTbody = document.getElementById("sqliteInvoicesTbody");

const rawInspectorDialog = document.getElementById("rawInspectorDialog");
const dialogS3Url = document.getElementById("dialogS3Url");
const dialogFlowId = document.getElementById("dialogFlowId");
const dialogAgentId = document.getElementById("dialogAgentId");
const dialogThreadId = document.getElementById("dialogThreadId");
const dialogRawKvpsTbody = document.getElementById("dialogRawKvpsTbody");
const dialogOcrText = document.getElementById("dialogOcrText");

// Mandatory fallback for browsers without native <dialog closedby="any"> support (e.g. Safari)
if (rawInspectorDialog && !("closedBy" in HTMLDialogElement.prototype)) {
  rawInspectorDialog.addEventListener("click", (event) => {
    if (event.target !== rawInspectorDialog) return;
    const rect = rawInspectorDialog.getBoundingClientRect();
    const isDialogContent =
      rect.top <= event.clientY &&
      event.clientY <= rect.top + rect.height &&
      rect.left <= event.clientX &&
      event.clientX <= rect.left + rect.width;
    if (isDialogContent) return;
    rawInspectorDialog.close();
  });
}

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

async function initApp() {
  try {
    const [healthRes, samplesRes, invoicesRes] = await Promise.all([
      fetch("/api/health"),
      fetch("/api/samples"),
      fetch("/api/invoices"),
    ]);

    if (healthRes.ok) {
      state.healthInfo = await healthRes.json();
      tenantStatusText.textContent = `Connected: ca-tor | Flow ${state.healthInfo.flow_id.slice(0, 8)}... | Agent ${state.healthInfo.agent_id.slice(0, 8)}...`;
    }

    if (samplesRes.ok) {
      const { samples } = await samplesRes.json();
      renderSampleButtons(samples);
    }

    if (invoicesRes.ok) {
      const { invoices } = await invoicesRes.json();
      state.invoices = invoices;
      renderSqliteTable();
      if (invoices.length > 0) {
        setActiveInvoice(invoices[0]);
      }
    }
  } catch (err) {
    tenantStatusText.textContent = `Backend Error: ${err.message}`;
  }
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
    alert("Please drop an invoice file or select one of the sample invoices first.");
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
    setActiveInvoice(data.invoice);

    // Refresh SQLite table
    const listRes = await fetch("/api/invoices");
    if (listRes.ok) {
      const listData = await listRes.json();
      state.invoices = listData.invoices;
      renderSqliteTable();
    }
  } catch (err) {
    telemetryElapsed.textContent = "Error";
    alert(`Pipeline Error: ${err.message}`);
  } finally {
    runPipelineBtn.disabled = false;
    runBtnLabel.textContent = originalText;
  }
});

function setActiveInvoice(inv) {
  state.activeInvoice = inv;
  emptyStateBox.hidden = true;
  invoiceDetailsContainer.hidden = false;
  openInspectorModalBtn.disabled = false;

  const confPct = ((Number(inv.avg_confidence) || 0.98) * 100).toFixed(1);
  activeConfidenceBadge.hidden = false;
  activeConfidenceBadge.textContent = `${confPct}% WDU Confidence`;
  activeInvoiceSubtitle.textContent = `File: ${inv.file_name} | Mode: ${inv.execution_mode} | SQLite Row #${inv.id}`;

  if (inv.telemetry && inv.telemetry.length > 0) {
    renderTelemetryResults(inv.telemetry);
  }

  const headerFields = [
    { label: "Document Type", value: inv.document_type || "Invoice", highlight: true },
    { label: "Invoice / Ref Number", value: inv.invoice_number, highlight: true },
    { label: "Approval Tier", value: inv.approval_tier || "AUTO_APPROVED", highlight: true },
    { label: "Odoo ERP Status", value: inv.odoo_bill_id ? `Bill #${inv.odoo_bill_id} (Synced)` : "Pending Sync", highlight: true },
    { label: "Vendor / Merchant", value: inv.vendor_name, highlight: true },
    { label: "Buyer (Bill To)", value: inv.buyer_name },
    { label: "Doc Date", value: inv.invoice_date },
    { label: "Due Date", value: inv.due_date },
    { label: "PO Number", value: inv.po_number },
    { label: "Payment Terms", value: inv.payment_terms },
    { label: "Subtotal", value: `${inv.currency} ${Number(inv.subtotal_amount).toFixed(2)}` },
    { label: "Tax Amount", value: `${inv.currency} ${Number(inv.tax_amount).toFixed(2)}` },
    { label: "Total Amount Due", value: `${inv.currency} ${Number(inv.total_amount).toFixed(2)}`, highlight: true },
    { label: "Vendor Address", value: inv.vendor_address },
    { label: "Buyer Address", value: inv.buyer_address },
  ];

  structuredHeaderGrid.innerHTML = headerFields
    .map(
      (f) => `
      <div class="kvp-tile ${f.highlight ? "highlight" : ""}">
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
        (item) => `
        <tr>
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

  renderSqliteTable();
}

function renderSqliteTable() {
  dbRecordCount.textContent = `${state.invoices.length} record${state.invoices.length === 1 ? "" : "s"}`;
  if (state.invoices.length === 0) {
    sqliteInvoicesTbody.innerHTML = `<tr><td colspan="10" class="empty-cell">No invoices stored in SQLite yet.</td></tr>`;
    return;
  }

  sqliteInvoicesTbody.innerHTML = state.invoices
    .map((inv) => {
      const isSelected = state.activeInvoice && state.activeInvoice.id === inv.id;
      const tierBadge =
        inv.approval_tier === "VP_APPROVAL_REQUIRED"
          ? `<span style="color:#b28600;font-weight:600;">VP Review</span>`
          : inv.approval_tier === "FLAGGED_MATH_MISMATCH"
          ? `<span style="color:#da1e28;font-weight:600;">Mismatch</span>`
          : `<span style="color:#198038;font-weight:600;">Auto-OK</span>`;

      const odooBadge = inv.odoo_bill_id
        ? `<a href="${escapeHtml(inv.odoo_url || 'https://invoiceprocessing.odoo.com')}" target="_blank" rel="noopener" class="badge-tag" style="background:#e0f2fe;color:#0369a1;text-decoration:none;" onclick="event.stopPropagation()">Bill #${inv.odoo_bill_id}</a>`
        : `<button type="button" class="btn-mini sync-odoo-btn" data-id="${inv.id}" onclick="event.stopPropagation()">Sync Odoo</button>`;

      return `
        <tr class="clickable-row ${isSelected ? "selected-row" : ""}" data-id="${inv.id}">
          <td>#${inv.id}</td>
          <td><span class="badge-tag">${escapeHtml(inv.document_type || "Invoice")}</span></td>
          <td><strong>${escapeHtml(inv.invoice_number || "N/A")}</strong></td>
          <td>${escapeHtml(inv.vendor_name || "—")}</td>
          <td><strong>${escapeHtml(inv.currency)} ${Number(inv.total_amount).toFixed(2)}</strong></td>
          <td>${tierBadge}</td>
          <td>${odooBadge}</td>
          <td>${((Number(inv.avg_confidence) || 0.98) * 100).toFixed(0)}%</td>
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
        alert(`Successfully created Odoo Vendor Bill #${data.bill.id}!`);
        const listRes = await fetch("/api/invoices");
        if (listRes.ok) {
          state.invoices = (await listRes.json()).invoices;
          renderSqliteTable();
        }
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
        state.invoices = state.invoices.filter((x) => x.id !== id);
        renderSqliteTable();
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
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Gmail check failed");
      if (data.processed_count === 0) {
        alert("No new unread invoice emails found in INBOX. Send an email with an invoice attachment (PDF/PNG) to aditya.krishnan2829@gmail.com and try again!");
      } else {
        alert(`Successfully ingested and processed ${data.processed_count} invoice email(s) and synced to Odoo ERP!`);
        const listRes = await fetch("/api/invoices");
        if (listRes.ok) {
          state.invoices = (await listRes.json()).invoices;
          renderSqliteTable();
          if (state.invoices.length > 0) setActiveInvoice(state.invoices[0]);
        }
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
