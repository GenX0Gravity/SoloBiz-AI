/**
 * SoloBiz AI — Main Application Controller
 */

import { API } from "./api.js";
import { renderMonthlyTrendChart, renderCategoryChart } from "./charts.js";

// Application State
const state = {
  currentView: "overview",
  overview: null,
  expenses: [],
  documents: [],
  invoices: [],
  aiStatus: null,
  chatHistory: [],
  currentEditingExpense: null,
  currentUploadedDoc: null,
  invoiceDraft: {
    invoice_number: "",
    client_name: "",
    client_email: "",
    client_address: "",
    sender_name: "SoloBiz Studio",
    sender_email: "billing@solobiz.studio",
    sender_address: "120 Freelance Way, Suite 400\nAustin, TX 78701",
    issue_date: new Date().toISOString().split("T")[0],
    due_date: new Date(Date.now() + 14 * 86400000).toISOString().split("T")[0],
    status: "Draft",
    currency: "USD",
    tax_rate: 8.25,
    discount_rate: 0.0,
    notes: "Payment is appreciated upon receipt. Direct bank deposit preferred.",
    items: [
      { description: "Full-Stack Web Application Consulting", quantity: 20, unit_price: 85, line_total: 1700 },
      { description: "Local AI Integration & OCR Pipeline", quantity: 8, unit_price: 95, line_total: 760 },
    ],
  },
};

// ==========================================================================
// Toast Notification Utility
// ==========================================================================

export function showToast(message, type = "info", duration = 3500) {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${escapeHtml(message)}</span>
    <button class="btn btn-sm btn-secondary" style="padding: 2px 6px; border: none; background: transparent; color: inherit;">&times;</button>
  `;

  toast.querySelector("button").addEventListener("click", () => toast.remove());
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatCurrency(val, currency = "USD") {
  return `$${Number(val || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// ==========================================================================
// Navigation & View Routing
// ==========================================================================

export function switchView(viewName) {
  state.currentView = viewName;

  // Update nav links
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.toggle("active", link.dataset.view === viewName);
  });

  // Update view containers
  document.querySelectorAll(".view-section").forEach((sec) => {
    sec.style.display = sec.id === `view-${viewName}` ? "block" : "none";
  });

  // Header Title updates
  const titleEl = document.getElementById("pageTitle");
  const descEl = document.getElementById("pageDesc");
  const titles = {
    overview: { title: "Dashboard Overview", desc: "Real-time expense trends, monthly burn rate, and pending invoices" },
    expenses: { title: "Expense Manager", desc: "Filter, search, edit, and export your local expense records" },
    documents: { title: "AI Receipt & Document Scanner", desc: "Local OCR and private on-device document extraction" },
    assistant: { title: "AI Business Assistant", desc: "Private financial insights grounded strictly in your local database" },
    invoices: { title: "Invoice & PDF Generator", desc: "Create professional client invoices with verified calculations and PDF export" },
    settings: { title: "Privacy & System Settings", desc: "Local AI model runtime, hardware requirements, and on-device storage" },
  };

  if (titles[viewName]) {
    titleEl.textContent = titles[viewName].title;
    descEl.textContent = titles[viewName].desc;
  }

  // Load relevant view data
  if (viewName === "overview") loadOverview();
  else if (viewName === "expenses") loadExpenses();
  else if (viewName === "documents") loadDocuments();
  else if (viewName === "assistant") setupAssistantView();
  else if (viewName === "invoices") loadInvoices();
  else if (viewName === "settings") loadSettingsView();
}

// ==========================================================================
// View: Overview / Dashboard
// ==========================================================================

async function loadOverview() {
  try {
    const data = await API.getAnalyticsOverview();
    state.overview = data;

    // Update Metric Cards
    document.getElementById("metricTotalExpenses").textContent = formatCurrency(data.total_expenses);
    document.getElementById("metricCurrentMonth").textContent = formatCurrency(data.current_month_expenses);
    document.getElementById("metricPendingInvoices").textContent = formatCurrency(data.pending_invoices_amount);
    document.getElementById("metricPendingCount").textContent = `${data.pending_invoices_count} pending`;
    document.getElementById("metricScannedCount").textContent = data.total_receipts_scanned;

    // MoM Trend Badge
    const momBadge = document.getElementById("metricMoMBadge");
    if (momBadge) {
      const change = data.month_over_month_change_pct;
      if (change > 0) {
        momBadge.className = "trend-badge up";
        momBadge.innerHTML = `&uarr; +${change}% vs last mo`;
      } else if (change < 0) {
        momBadge.className = "trend-badge down";
        momBadge.innerHTML = `&darr; ${change}% vs last mo`;
      } else {
        momBadge.className = "trend-badge neutral";
        momBadge.textContent = "0% vs last mo";
      }
    }

    // Render Charts
    renderMonthlyTrendChart("monthlySpendChart", data.monthly_trends);
    renderCategoryChart("categorySpendChart", data.category_breakdown);

    // Populate Recent Transactions
    renderRecentTransactions(data.recent_transactions);
  } catch (err) {
    showToast(`Failed to load overview: ${err.message}`, "error");
  }
}

function renderRecentTransactions(txs = []) {
  const tbody = document.getElementById("recentTxTableBody");
  if (!tbody) return;

  if (!txs || txs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 24px; color: var(--text-muted);">No transactions recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = txs
    .map(
      (tx) => `
    <tr>
      <td class="font-mono" style="color: var(--text-muted); font-size: 0.8rem;">${escapeHtml(tx.date)}</td>
      <td style="font-weight: 600;">${escapeHtml(tx.title)}</td>
      <td><span class="badge badge-${tx.category.toLowerCase().replace(/[^a-z]/g, "")}">${escapeHtml(tx.category)}</span></td>
      <td style="color: var(--text-muted); font-size: 0.82rem;">${escapeHtml(tx.payment_method || "Card")}</td>
      <td class="font-mono" style="font-weight: 700; color: var(--text-main);">${formatCurrency(tx.amount)}</td>
    </tr>
  `
    )
    .join("");
}

// ==========================================================================
// View: Expenses Manager
// ==========================================================================

async function loadExpenses() {
  const category = document.getElementById("expenseCategoryFilter")?.value || "All";
  const search = document.getElementById("expenseSearchInput")?.value || "";

  try {
    const expenses = await API.getExpenses({ category, search, limit: 100 });
    state.expenses = expenses;
    renderExpensesTable(expenses);
  } catch (err) {
    showToast(`Failed to load expenses: ${err.message}`, "error");
  }
}

function renderExpensesTable(expenses = []) {
  const tbody = document.getElementById("expensesTableBody");
  const countEl = document.getElementById("expensesCountSummary");
  if (!tbody) return;

  if (countEl) {
    const totalSum = expenses.reduce((acc, curr) => acc + curr.amount, 0);
    countEl.textContent = `Showing ${expenses.length} records | Total: ${formatCurrency(totalSum)}`;
  }

  if (expenses.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 36px; color: var(--text-muted);">No matching expenses found.</td></tr>`;
    return;
  }

  tbody.innerHTML = expenses
    .map(
      (exp) => `
    <tr>
      <td class="font-mono" style="font-size: 0.82rem; color: var(--text-muted);">${escapeHtml(exp.date)}</td>
      <td style="font-weight: 600;">
        ${escapeHtml(exp.title)}
        ${exp.notes ? `<div style="font-size: 0.74rem; color: var(--text-muted); font-weight: 400;">${escapeHtml(exp.notes)}</div>` : ""}
      </td>
      <td><span class="badge badge-${exp.category.toLowerCase().replace(/[^a-z]/g, "")}">${escapeHtml(exp.category)}</span></td>
      <td style="color: var(--text-muted); font-size: 0.82rem;">${escapeHtml(exp.payment_method)}</td>
      <td class="font-mono" style="color: var(--text-muted); font-size: 0.82rem;">${formatCurrency(exp.tax_amount)}</td>
      <td class="font-mono" style="font-weight: 700;">${formatCurrency(exp.amount)}</td>
      <td>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-sm btn-secondary" onclick="window.editExpense(${exp.id})">Edit</button>
          <button class="btn btn-sm btn-danger" onclick="window.deleteExpense(${exp.id})">&times;</button>
        </div>
      </td>
    </tr>
  `
    )
    .join("");
}

// Window actions for expense editing/deleting
window.editExpense = function (id) {
  const exp = state.expenses.find((e) => e.id === id);
  if (!exp) return;

  state.currentEditingExpense = exp;
  document.getElementById("modalExpenseTitle").textContent = "Edit Expense";
  document.getElementById("expFormTitle").value = exp.title;
  document.getElementById("expFormAmount").value = exp.amount;
  document.getElementById("expFormCategory").value = exp.category;
  document.getElementById("expFormDate").value = exp.date;
  document.getElementById("expFormPayment").value = exp.payment_method;
  document.getElementById("expFormTax").value = exp.tax_amount || 0;
  document.getElementById("expFormNotes").value = exp.notes || "";

  openModal("expenseModal");
};

window.deleteExpense = async function (id) {
  if (!confirm("Are you sure you want to delete this expense record?")) return;
  try {
    await API.deleteExpense(id);
    showToast("Expense record deleted.", "success");
    loadExpenses();
    if (state.currentView === "overview") loadOverview();
  } catch (err) {
    showToast(`Error deleting expense: ${err.message}`, "error");
  }
};

// ==========================================================================
// View: Receipt Scanner & Documents
// ==========================================================================

async function loadDocuments() {
  try {
    const docs = await API.getDocuments();
    state.documents = docs;
    renderDocumentsTable(docs);
  } catch (err) {
    showToast(`Failed to load documents: ${err.message}`, "error");
  }
}

function renderDocumentsTable(docs = []) {
  const tbody = document.getElementById("documentsTableBody");
  if (!tbody) return;

  if (docs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 24px; color: var(--text-muted);">No uploaded documents yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = docs
    .map(
      (doc) => `
    <tr>
      <td class="font-mono" style="font-size: 0.8rem; color: var(--text-muted);">${doc.id}</td>
      <td style="font-weight: 600;">${escapeHtml(doc.original_filename)}</td>
      <td><span class="badge badge-software">${doc.file_type.toUpperCase()}</span></td>
      <td style="color: var(--text-muted); font-size: 0.82rem;">${(doc.file_size / 1024).toFixed(1)} KB</td>
      <td>
        <a href="${API.getDocumentFileUrl(doc.id)}" target="_blank" class="btn btn-sm btn-secondary">
          View File
        </a>
      </td>
    </tr>
  `
    )
    .join("");
}

export async function handleFileUpload(file) {
  if (!file) return;

  const dropzone = document.getElementById("documentDropzone");
  const spinner = document.getElementById("uploadSpinner");
  if (dropzone) dropzone.style.opacity = "0.5";
  if (spinner) spinner.style.display = "block";

  showToast(`Uploading and scanning "${file.name}" locally...`, "info", 5000);

  try {
    const res = await API.uploadDocument(file);
    state.currentUploadedDoc = res;

    showToast("Document processed! Please verify extracted fields.", "success");
    openVerificationModal(res);
    loadDocuments();
  } catch (err) {
    showToast(`Upload failed: ${err.message}`, "error", 6000);
  } finally {
    if (dropzone) dropzone.style.opacity = "1";
    if (spinner) spinner.style.display = "none";
  }
}

function openVerificationModal(uploadResult) {
  const data = uploadResult.extracted_data || {};

  document.getElementById("verifyDocName").textContent = uploadResult.filename;
  document.getElementById("verifyDocType").textContent = uploadResult.file_type.toUpperCase();
  document.getElementById("verifyDocSize").textContent = `${(uploadResult.file_size / 1024).toFixed(1)} KB`;
  document.getElementById("verifyRawText").textContent = uploadResult.extracted_text_snippet || "No textual preview available.";

  // Duplicate Warning
  const dupWarning = document.getElementById("verifyDuplicateWarning");
  if (dupWarning) {
    dupWarning.style.display = uploadResult.is_duplicate ? "block" : "none";
  }

  // Source badge
  const sourceBadge = document.getElementById("verifySourceBadge");
  if (sourceBadge) {
    sourceBadge.textContent = data.extraction_source === "ollama" ? "Local Ollama LLM" : "Local Rule Engine";
    sourceBadge.className = data.extraction_source === "ollama" ? "badge badge-software" : "badge badge-marketing";
  }

  // Pre-fill form
  document.getElementById("verifyDocId").value = uploadResult.document_id;
  document.getElementById("verifyMerchant").value = data.merchant_or_client || "";
  document.getElementById("verifyDate").value = data.date || new Date().toISOString().split("T")[0];
  document.getElementById("verifyCategory").value = data.category || "Other";
  document.getElementById("verifySubtotal").value = data.subtotal || 0;
  document.getElementById("verifyTax").value = data.tax || 0;
  document.getElementById("verifyTotal").value = data.total || 0;
  document.getElementById("verifyNotes").value = data.confidence_notes || "";

  openModal("verificationModal");
}

// ==========================================================================
// View: AI Business Assistant
// ==========================================================================

async function setupAssistantView() {
  updateAIStatusPill();
}

async function updateAIStatusPill() {
  try {
    const status = await API.getAIStatus();
    state.aiStatus = status;

    const pill = document.getElementById("aiStatusPill");
    const label = document.getElementById("aiStatusLabel");
    const detail = document.getElementById("aiStatusDetail");
    const banner = document.getElementById("aiOfflineBanner");

    if (pill && label && detail) {
      if (status.available) {
        pill.className = "status-pulse-dot";
        label.textContent = "Ollama Active";
        detail.textContent = `Model: ${status.configured_model}`;
        if (banner) banner.style.display = "none";
      } else {
        pill.className = "status-pulse-dot offline";
        label.textContent = "Offline Mode";
        detail.textContent = "Local SQLite Active";
        if (banner) banner.style.display = "block";
      }
    }
  } catch (err) {
    console.debug("AI status check error:", err);
  }
}

export async function sendChatMessage(promptText = null) {
  const inputEl = document.getElementById("chatInput");
  const message = promptText || inputEl?.value?.trim();
  if (!message) return;

  if (inputEl) inputEl.value = "";

  const container = document.getElementById("chatMessages");
  if (!container) return;

  // Append user message
  const userMsgEl = document.createElement("div");
  userMsgEl.className = "message-bubble user";
  userMsgEl.textContent = message;
  container.appendChild(userMsgEl);
  container.scrollTop = container.scrollHeight;

  // Append assistant loading placeholder
  const botMsgEl = document.createElement("div");
  botMsgEl.className = "message-bubble assistant";
  botMsgEl.innerHTML = `
    <div class="assistant-meta">SoloBiz Assistant</div>
    <div class="typing-indicator" style="display:flex; gap: 4px; padding: 6px 0;">
      <span style="animation: pulse 1s infinite;">Thinking</span>...
    </div>
  `;
  container.appendChild(botMsgEl);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await API.chatWithAssistant(message, state.chatHistory);
    state.chatHistory.push({ role: "user", content: message });
    state.chatHistory.push({ role: "assistant", content: res.response });

    // Format Markdown / Bolded text / Badges
    let formattedResponse = escapeHtml(res.response)
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\[Verified Record\]/g, '<span class="badge badge-office" style="font-size:0.75rem;">Verified Record</span>')
      .replace(/\[Suggestion\]/g, '<span class="badge badge-software" style="font-size:0.75rem;">Suggestion</span>')
      .replace(/\n/g, "<br/>");

    // Grounding facts accordion
    let groundingHtml = "";
    if (res.grounding_facts && res.grounding_facts.length > 0) {
      groundingHtml = `
        <div class="grounding-facts-card">
          <strong>Database Ground Truth Context:</strong>
          ${res.grounding_facts.map((f) => `<div class="fact-item">&bull; ${escapeHtml(f)}</div>`).join("")}
        </div>
      `;
    }

    botMsgEl.innerHTML = `
      <div class="assistant-meta">
        SoloBiz Assistant
        <span class="badge ${res.is_fallback ? "badge-marketing" : "badge-software"}" style="font-size: 0.68rem;">
          ${res.source === "ollama" ? `Ollama (${res.model})` : "Local Rule Engine"}
        </span>
      </div>
      <div>${formattedResponse}</div>
      ${groundingHtml}
    `;
  } catch (err) {
    botMsgEl.innerHTML = `
      <div class="assistant-meta" style="color: var(--accent-rose);">Assistant Notice</div>
      <div>Could not generate response: ${escapeHtml(err.message)}</div>
    `;
  }
  container.scrollTop = container.scrollHeight;
}

// ==========================================================================
// View: Invoices & PDF Generator
// ==========================================================================

async function loadInvoices() {
  try {
    const invoices = await API.getInvoices();
    state.invoices = invoices;
    renderInvoicesTable(invoices);
    renderLiveInvoicePreview();
  } catch (err) {
    showToast(`Failed to load invoices: ${err.message}`, "error");
  }
}

function renderInvoicesTable(invoices = []) {
  const tbody = document.getElementById("invoicesTableBody");
  if (!tbody) return;

  if (invoices.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 36px; color: var(--text-muted);">No invoices created yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = invoices
    .map(
      (inv) => `
    <tr>
      <td class="font-mono" style="font-weight: 700; color: var(--accent-cyan);">${escapeHtml(inv.invoice_number)}</td>
      <td style="font-weight: 600;">${escapeHtml(inv.client_name)}</td>
      <td class="font-mono" style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(inv.issue_date)}</td>
      <td class="font-mono" style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(inv.due_date)}</td>
      <td class="font-mono" style="font-weight: 700;">${formatCurrency(inv.total_amount)}</td>
      <td><span class="status-pill ${inv.status.toLowerCase()}">${escapeHtml(inv.status)}</span></td>
      <td>
        <div style="display: flex; gap: 8px;">
          <a href="${API.getInvoicePdfUrl(inv.id)}" target="_blank" class="btn btn-sm btn-primary">
            Download PDF
          </a>
          <button class="btn btn-sm btn-danger" onclick="window.deleteInvoice(${inv.id})">&times;</button>
        </div>
      </td>
    </tr>
  `
    )
    .join("");
}

window.deleteInvoice = async function (id) {
  if (!confirm("Are you sure you want to delete this invoice?")) return;
  try {
    await API.deleteInvoice(id);
    showToast("Invoice deleted.", "success");
    loadInvoices();
    if (state.currentView === "overview") loadOverview();
  } catch (err) {
    showToast(`Error deleting invoice: ${err.message}`, "error");
  }
};

export function renderLiveInvoicePreview() {
  const draft = state.invoiceDraft;

  // Calculate live totals
  let subtotal = 0;
  draft.items.forEach((item) => {
    const qty = Number(item.quantity) || 0;
    const price = Number(item.unit_price) || 0;
    item.line_total = Math.round(qty * price * 100) / 100;
    subtotal += item.line_total;
  });

  const discRate = Number(draft.discount_rate) || 0;
  const discountAmount = Math.round(subtotal * (discRate / 100) * 100) / 100;
  const taxable = Math.max(0, subtotal - discountAmount);
  const taxRate = Number(draft.tax_rate) || 0;
  const taxAmount = Math.round(taxable * (taxRate / 100) * 100) / 100;
  const totalAmount = Math.round((taxable + taxAmount) * 100) / 100;

  // Update paper preview DOM
  const preview = document.getElementById("invoicePaperPreview");
  if (!preview) return;

  preview.innerHTML = `
    <div class="inv-header">
      <div>
        <div class="inv-title">INVOICE</div>
        <div style="font-size: 0.82rem; font-weight: 700; color: #475569;"># ${escapeHtml(draft.invoice_number || "INV-NEW")}</div>
        <div style="font-size: 0.78rem; color: #64748b;">Issue Date: ${escapeHtml(draft.issue_date)}</div>
        <div style="font-size: 0.78rem; color: #64748b;">Due Date: ${escapeHtml(draft.due_date)}</div>
      </div>
      <div style="text-align: right;">
        <div style="font-weight: 800; color: #0f172a; font-size: 1rem;">${escapeHtml(draft.sender_name)}</div>
        <div style="font-size: 0.78rem; color: #64748b;">${escapeHtml(draft.sender_email)}</div>
        <div style="font-size: 0.76rem; color: #64748b; white-space: pre-line;">${escapeHtml(draft.sender_address)}</div>
      </div>
    </div>

    <div style="margin-bottom: 16px;">
      <div style="font-size: 0.72rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Bill To:</div>
      <div style="font-weight: 700; font-size: 0.95rem; color: #0f172a;">${escapeHtml(draft.client_name || "Client Name")}</div>
      <div style="font-size: 0.8rem; color: #64748b;">${escapeHtml(draft.client_email)}</div>
      <div style="font-size: 0.78rem; color: #64748b; white-space: pre-line;">${escapeHtml(draft.client_address)}</div>
    </div>

    <table>
      <thead>
        <tr>
          <th>Description</th>
          <th style="text-align: center;">Qty</th>
          <th style="text-align: right;">Rate</th>
          <th style="text-align: right;">Total</th>
        </tr>
      </thead>
      <tbody>
        ${draft.items
          .map(
            (i) => `
          <tr>
            <td style="font-weight: 600;">${escapeHtml(i.description || "Line Item")}</td>
            <td style="text-align: center;">${i.quantity}</td>
            <td style="text-align: right;">$${Number(i.unit_price).toFixed(2)}</td>
            <td style="text-align: right; font-weight: 700;">$${Number(i.line_total).toFixed(2)}</td>
          </tr>
        `
          )
          .join("")}
      </tbody>
    </table>

    <div class="inv-totals">
      <div class="total-line"><span>Subtotal:</span><span>$${subtotal.toFixed(2)}</span></div>
      ${discountAmount > 0 ? `<div class="total-line" style="color: #64748b;"><span>Discount (${discRate}%):</span><span>-$${discountAmount.toFixed(2)}</span></div>` : ""}
      ${taxAmount > 0 ? `<div class="total-line" style="color: #64748b;"><span>Tax (${taxRate}%):</span><span>+$${taxAmount.toFixed(2)}</span></div>` : ""}
      <div class="total-line grand-total"><span>Total Due:</span><span>$${totalAmount.toFixed(2)} ${draft.currency}</span></div>
    </div>

    <div style="margin-top: 24px; padding-top: 14px; border-top: 1px solid #e2e8f0; font-size: 0.76rem; color: #64748b;">
      <strong>Terms & Notes:</strong> ${escapeHtml(draft.notes)}
    </div>
  `;
}

export function addInvoiceLineItem() {
  state.invoiceDraft.items.push({
    description: "",
    quantity: 1,
    unit_price: 0,
    line_total: 0,
  });
  renderInvoiceLineItemInputs();
  renderLiveInvoicePreview();
}

export function removeInvoiceLineItem(idx) {
  if (state.invoiceDraft.items.length <= 1) {
    showToast("Invoice must contain at least one line item.", "warning");
    return;
  }
  state.invoiceDraft.items.splice(idx, 1);
  renderInvoiceLineItemInputs();
  renderLiveInvoicePreview();
}

function renderInvoiceLineItemInputs() {
  const container = document.getElementById("invoiceItemsContainer");
  if (!container) return;

  container.innerHTML = state.invoiceDraft.items
    .map(
      (item, idx) => `
    <div class="line-item-row" data-index="${idx}">
      <input type="text" class="form-control item-desc" placeholder="Service / product description" value="${escapeHtml(item.description)}">
      <input type="number" class="form-control item-qty" min="0.1" step="0.1" placeholder="1" value="${item.quantity}">
      <input type="number" class="form-control item-price" min="0" step="0.01" placeholder="0.00" value="${item.unit_price}">
      <div class="font-mono item-total" style="font-weight: 700; text-align: right; padding-right: 6px;">$${(item.line_total || 0).toFixed(2)}</div>
      <button type="button" class="btn btn-sm btn-danger" onclick="window.removeLineItem(${idx})" style="padding: 4px 8px;">&times;</button>
    </div>
  `
    )
    .join("");

  // Attach live input listeners
  container.querySelectorAll(".line-item-row").forEach((row) => {
    const idx = parseInt(row.dataset.index, 10);
    const descInput = row.querySelector(".item-desc");
    const qtyInput = row.querySelector(".item-qty");
    const priceInput = row.querySelector(".item-price");

    const update = () => {
      state.invoiceDraft.items[idx].description = descInput.value;
      state.invoiceDraft.items[idx].quantity = parseFloat(qtyInput.value) || 0;
      state.invoiceDraft.items[idx].unit_price = parseFloat(priceInput.value) || 0;
      renderLiveInvoicePreview();
    };

    descInput.addEventListener("input", update);
    qtyInput.addEventListener("input", update);
    priceInput.addEventListener("input", update);
  });
}

window.removeLineItem = removeInvoiceLineItem;

// ==========================================================================
// View: Privacy & Settings
// ==========================================================================

async function loadSettingsView() {
  try {
    const status = await API.getAIStatus();
    const statusText = document.getElementById("settingsOllamaStatus");
    const installedList = document.getElementById("settingsInstalledModels");
    const hardwareTable = document.getElementById("settingsRecommendedModels");

    if (statusText) {
      statusText.textContent = status.status_message;
      statusText.style.color = status.available ? "var(--accent-emerald)" : "var(--accent-amber)";
    }

    if (installedList) {
      installedList.innerHTML =
        status.installed_models.length > 0
          ? status.installed_models.map((m) => `<span class="badge badge-software">${m}</span>`).join(" ")
          : '<span style="color: var(--text-muted);">No models installed yet. Run <code>ollama run llama3.2</code> in terminal.</span>';
    }

    if (hardwareTable && status.recommended_models) {
      hardwareTable.innerHTML = status.recommended_models
        .map(
          (m) => `
        <tr>
          <td style="font-weight: 700; color: var(--accent-cyan);">${escapeHtml(m.name)}</td>
          <td style="color: var(--text-secondary); font-size: 0.84rem;">${escapeHtml(m.description)}</td>
          <td class="font-mono" style="font-size: 0.8rem;"><code>${escapeHtml(m.pull_command)}</code></td>
        </tr>
      `
        )
        .join("");
    }
  } catch (err) {
    showToast(`Error fetching system settings: ${err.message}`, "error");
  }
}

// ==========================================================================
// Modal Helpers
// ==========================================================================

export function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add("active");
}

export function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove("active");
}

// ==========================================================================
// Initialization & Event Listeners
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
  // 1. Navigation clicks
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      switchView(link.dataset.view);
    });
  });

  // 2. Global Upload Receipt Button
  document.getElementById("btnHeaderUpload")?.addEventListener("click", () => {
    switchView("documents");
  });

  // 3. Dropzone & File Input
  const fileInput = document.getElementById("receiptFileInput");
  const dropzone = document.getElementById("documentDropzone");

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

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
      if (e.dataTransfer.files.length > 0) {
        handleFileUpload(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
      }
    });
  }

  // 4. Modal Closes (buttons with data-close-modal)
  document.querySelectorAll("[data-close-modal]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modal = btn.closest(".modal-backdrop");
      if (modal) modal.classList.remove("active");
    });
  });

  // 5. Save Verified Receipt Form Submit
  document.getElementById("verifySaveForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      document_id: parseInt(document.getElementById("verifyDocId").value, 10),
      title: document.getElementById("verifyMerchant").value,
      date: document.getElementById("verifyDate").value,
      category: document.getElementById("verifyCategory").value,
      subtotal: parseFloat(document.getElementById("verifySubtotal").value) || 0,
      tax_amount: parseFloat(document.getElementById("verifyTax").value) || 0,
      amount: parseFloat(document.getElementById("verifyTotal").value) || 0,
      payment_method: document.getElementById("verifyPayment").value,
      notes: document.getElementById("verifyNotes").value,
    };

    try {
      await API.verifyAndSaveReceipt(payload);
      closeModal("verificationModal");
      showToast("Verified expense saved to database!", "success");
      loadExpenses();
      loadOverview();
    } catch (err) {
      showToast(`Failed to save verified receipt: ${err.message}`, "error");
    }
  });

  // 6. Manual Expense Modal & Form
  document.getElementById("btnAddExpense")?.addEventListener("click", () => {
    state.currentEditingExpense = null;
    document.getElementById("modalExpenseTitle").textContent = "Add Manual Expense";
    document.getElementById("expenseForm").reset();
    document.getElementById("expFormDate").value = new Date().toISOString().split("T")[0];
    openModal("expenseModal");
  });

  document.getElementById("expenseForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      title: document.getElementById("expFormTitle").value,
      amount: parseFloat(document.getElementById("expFormAmount").value) || 0,
      category: document.getElementById("expFormCategory").value,
      date: document.getElementById("expFormDate").value,
      payment_method: document.getElementById("expFormPayment").value,
      tax_amount: parseFloat(document.getElementById("expFormTax").value) || 0,
      subtotal: parseFloat(document.getElementById("expFormAmount").value) || 0,
      notes: document.getElementById("expFormNotes").value,
      currency: "USD",
      is_verified: 1,
    };

    try {
      if (state.currentEditingExpense) {
        await API.updateExpense(state.currentEditingExpense.id, payload);
        showToast("Expense updated successfully.", "success");
      } else {
        await API.createExpense(payload);
        showToast("New expense created.", "success");
      }
      closeModal("expenseModal");
      loadExpenses();
      loadOverview();
    } catch (err) {
      showToast(`Error saving expense: ${err.message}`, "error");
    }
  });

  // 7. Expenses Search & Filter triggers
  document.getElementById("expenseCategoryFilter")?.addEventListener("change", loadExpenses);
  document.getElementById("expenseSearchInput")?.addEventListener("input", () => {
    clearTimeout(window._searchTimer);
    window._searchTimer = setTimeout(loadExpenses, 250);
  });
  document.getElementById("btnExportExpensesCsv")?.addEventListener("click", () => {
    const cat = document.getElementById("expenseCategoryFilter")?.value || "All";
    const q = document.getElementById("expenseSearchInput")?.value || "";
    window.location.href = API.getExportCSVUrl({ category: cat, search: q });
  });

  // 8. AI Chat Input & Prompt Chips
  document.getElementById("chatSendBtn")?.addEventListener("click", () => sendChatMessage());
  document.getElementById("chatInput")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });
  document.querySelectorAll(".prompt-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      sendChatMessage(chip.dataset.prompt);
    });
  });

  // 9. Invoice Generator triggers
  document.getElementById("btnAddInvoiceItem")?.addEventListener("click", addInvoiceLineItem);
  document.getElementById("invoiceForm")?.addEventListener("input", () => {
    // Sync draft form to state
    state.invoiceDraft.invoice_number = document.getElementById("invNumber").value;
    state.invoiceDraft.client_name = document.getElementById("invClientName").value;
    state.invoiceDraft.client_email = document.getElementById("invClientEmail").value;
    state.invoiceDraft.client_address = document.getElementById("invClientAddress").value;
    state.invoiceDraft.sender_name = document.getElementById("invSenderName").value;
    state.invoiceDraft.sender_email = document.getElementById("invSenderEmail").value;
    state.invoiceDraft.sender_address = document.getElementById("invSenderAddress").value;
    state.invoiceDraft.issue_date = document.getElementById("invIssueDate").value;
    state.invoiceDraft.due_date = document.getElementById("invDueDate").value;
    state.invoiceDraft.status = document.getElementById("invStatus").value;
    state.invoiceDraft.tax_rate = parseFloat(document.getElementById("invTaxRate").value) || 0;
    state.invoiceDraft.discount_rate = parseFloat(document.getElementById("invDiscountRate").value) || 0;
    state.invoiceDraft.notes = document.getElementById("invNotes").value;
    renderLiveInvoicePreview();
  });

  document.getElementById("btnSaveInvoice")?.addEventListener("click", async () => {
    const draft = state.invoiceDraft;
    if (!draft.client_name.trim()) {
      showToast("Please enter a client name.", "warning");
      return;
    }
    if (!draft.invoice_number.trim()) {
      showToast("Please provide an invoice number.", "warning");
      return;
    }

    try {
      const created = await API.createInvoice(draft);
      showToast(`Invoice ${created.invoice_number} saved!`, "success");
      loadInvoices();
      loadOverview();
      // Generate unique next number
      document.getElementById("invNumber").value = `INV-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`;
      state.invoiceDraft.invoice_number = document.getElementById("invNumber").value;
    } catch (err) {
      showToast(`Failed to create invoice: ${err.message}`, "error");
    }
  });

  // Generate random invoice number on page load
  const invNumInput = document.getElementById("invNumber");
  if (invNumInput) {
    invNumInput.value = `INV-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`;
    state.invoiceDraft.invoice_number = invNumInput.value;
  }
  renderInvoiceLineItemInputs();

  // Mobile Sidebar Toggle
  document.getElementById("btnToggleSidebar")?.addEventListener("click", () => {
    document.querySelector(".app-sidebar")?.classList.toggle("open");
  });

  // Initial Load
  switchView("overview");
  updateAIStatusPill();
});
