/**
 * SoloBiz AI — API Client Module
 * Communicates with FastAPI local backend.
 */

const API_BASE = "/api";

async function request(endpoint, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    if (!res.ok) {
      let errorMsg = `HTTP Error ${res.status}`;
      try {
        const errJson = await res.json();
        if (errJson.detail) {
          errorMsg = Array.isArray(errJson.detail)
            ? errJson.detail.map((d) => d.msg || JSON.stringify(d)).join(", ")
            : errJson.detail;
        }
      } catch (e) {
        // fallback
      }
      throw new Error(errorMsg);
    }
    return await res.json();
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

export const API = {
  // Health & AI status
  async getHealth() {
    return request("/health");
  },

  async getAIStatus() {
    return request("/ai/status");
  },

  // Analytics Overview
  async getAnalyticsOverview() {
    return request("/analytics/overview");
  },

  getExportCSVUrl(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return `${API_BASE}/analytics/export/csv?${qs}`;
  },

  // Expenses CRUD
  async getExpenses(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return request(`/expenses?${qs}`);
  },

  async createExpense(expenseData) {
    return request("/expenses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(expenseData),
    });
  },

  async updateExpense(id, expenseData) {
    return request(`/expenses/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(expenseData),
    });
  },

  async deleteExpense(id) {
    return request(`/expenses/${id}`, {
      method: "DELETE",
    });
  },

  // Document Upload & AI Scanner
  async uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail || `Upload failed with status ${res.status}`);
    }
    return await res.json();
  },

  async verifyAndSaveReceipt(verifyData) {
    return request("/documents/verify-save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(verifyData),
    });
  },

  async getDocuments() {
    return request("/documents");
  },

  getDocumentFileUrl(docId) {
    return `${API_BASE}/documents/${docId}/file`;
  },

  // Invoices & PDF
  async getInvoices(statusFilter = "") {
    const endpoint = statusFilter && statusFilter !== "All"
      ? `/invoices?status_filter=${encodeURIComponent(statusFilter)}`
      : "/invoices";
    return request(endpoint);
  },

  async getInvoice(id) {
    return request(`/invoices/${id}`);
  },

  async createInvoice(invoiceData) {
    return request("/invoices", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(invoiceData),
    });
  },

  async updateInvoice(id, invoiceData) {
    return request(`/invoices/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(invoiceData),
    });
  },

  async deleteInvoice(id) {
    return request(`/invoices/${id}`, {
      method: "DELETE",
    });
  },

  getInvoicePdfUrl(id) {
    return `${API_BASE}/invoices/${id}/pdf`;
  },

  // AI Assistant Chat
  async chatWithAssistant(message, history = []) {
    return request("/ai/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });
  },
};
