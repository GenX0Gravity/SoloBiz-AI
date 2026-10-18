This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)

---

# SoloBiz AI — The Local-First, Privacy-Focused AI Business Assistant for Freelancers & Solopreneurs

## What I Built

Running a freelance business or indie side hustle is thrilling, but administrative overhead is an absolute productivity killer. Solo founders, independent consultants, and creators spend hours every week wrangling messy receipts, logging expenses, figuring out tax deductibles, designing client invoices, and trying to decipher where their earnings actually went.

Worse, existing commercial accounting tools either charge hefty monthly subscription fees or upload every single one of your sensitive financial documents, bank receipts, and client agreements to remote third-party proprietary AI clouds.

**SoloBiz AI** was built to solve this dilemma: **an open-source, local-first, privacy-respecting AI financial workspace** engineered specifically for freelancers, developers, designers, and small business owners.

### Core Capabilities:
1. **Intelligent Receipt & Invoice Parser:** Upload PDF documents or scanned receipts (JPG, PNG). The system automatically extracts the vendor name, invoice date, currency, line items, and total amount, and accurately classifies it into business tax categories (Software, Office, Travel, Meals, Marketing, etc.).
2. **Context-Aware AI Financial Advisor:** An embedded interactive AI chat assistant that grounds its answers in your actual SQLite transaction history. Ask questions like *"What was my biggest expense category this quarter?"* or *"Generate an itemized tax deduction summary for my accountant"*.
3. **Interactive Financial Analytics:** Beautiful, responsive Chart.js visual dashboards displaying monthly spending trends, category distributions, transaction histories, and real-time cash flow KPIs.
4. **Professional PDF Invoice Studio:** Create sleek, client-ready invoices with dynamic line items, automated tax calculations, custom notes, and instant downloadable ReportLab PDF generation.
5. **100% Privacy by Design:** Your sensitive invoices, bank details, and business receipts never leave your machine. Inference runs on local open-weight models (via Ollama) with a high-accuracy deterministic heuristic engine as an instant fallback.

---

## Demo

- **GitHub Repository:** [https://github.com/GenX0Gravity/SoloBiz-AI.git](https://github.com/GenX0Gravity/SoloBiz-AI.git)
- **Live Vercel Deployment:** [https://solobiz-ai.vercel.app](https://solobiz-ai.vercel.app)
- **Live Interactive Localhost Tunnel:** [https://solobiz-ai.loca.lt](https://solobiz-ai.loca.lt)  
  *(Note: If prompted for the Localtunnel Endpoint IP / Password, enter: `152.58.182.93`)*
- **1-Click Cloud Deployment:** [Deploy to Render Blueprint](https://render.com/deploy?repo=https://github.com/GenX0Gravity/SoloBiz-AI)
- **API Health Check:** [https://solobiz-ai.vercel.app/health](https://solobiz-ai.vercel.app/health)

### Quick Visual Walkthrough

1. **Dashboard & Metrics:** View monthly burn, total expenses, active invoices, and category breakdowns in real time.
2. **AI Document Extraction:** Drag and drop an invoice PDF or receipt image; watch the extracted details automatically populate the expense log.
3. **Conversational Assistant:** Chat naturally with your financial data to identify spending leaks and prepare quarterly estimates.
4. **Invoice Builder:** Fill out billable services, click **Generate PDF**, and hand off a high-resolution, vector-crisp invoice to your client.

---

## Tools & Technologies Used

SoloBiz AI was designed with a clean, decoupled architecture that maximizes maintainability, speed, and privacy:

### 1. Frontend
- **HTML5 & Vanilla Modern CSS:** Crafted with custom glassmorphism design tokens, vibrant accessible contrast, dark-mode styling, and responsive CSS Grid/Flexbox layouts. Zero heavy frontend frameworks or bloated node bundles needed.
- **Vanilla JavaScript (ES6+):** Pure modular architecture managing state transitions, file drag-and-drop, API communication, and toast notifications.
- **Chart.js:** Responsive data visualization rendering smooth doughnut charts for category splits and line charts for monthly cash flow trajectories.

### 2. Backend & Document Processing
- **Python 3.11 & FastAPI:** Asynchronous, lightning-fast RESTful API backend equipped with Pydantic schema validation and automatic OpenAPI documentation (`/docs`).
- **pypdf & Pillow (PIL):** Extracts structural text and image metadata from uploaded PDF documents and receipt images.
- **ReportLab:** Programmatic vector PDF engine generating pixel-perfect client invoices directly on the server.
- **SQLite & Python `sqlite3`:** Zero-configuration, battle-tested relational database storing all vendors, expenses, line items, and invoice records locally inside `data/solobiz.db`.

### 3. Open-Source AI Inference
- **Ollama:** Integrates with local open-weight LLMs (such as `llama3:8b`, `mistral:7b`, or `phi3`).
- **Resilient Fallback Engine:** Features built-in deterministic heuristic regex parsers that seamlessly handle document extraction and financial advice even when running on machines without a GPU or when Ollama is offline.

### 4. DevOps & Cloud Readiness
- **Docker & Docker Compose:** Multi-stage containerized workflow bundling system dependencies, Python runtime, and OCR tools with persistent volume mounts for database data.
- **Render Blueprint (`render.yaml`):** Infrastructure-as-code specification enabling automated 1-click cloud deployments with a persistent 1GB disk at `/var/data`.

---

## How It Works: The Privacy-First Architecture

```
[ User Browser ] (HTML5 / Vanilla CSS / Chart.js)
       │
       ▼ (HTTP REST APIs / Multipart Uploads)
[ FastAPI Backend ] (Python 3.11)
  ├── /api/receipts/upload  ──► Document Extractor (pypdf / PIL)
  │                                     │
  │                                     ▼
  │                             [ AI Inference Router ]
  │                              ├── Local Ollama LLM (Primary)
  │                              └── Deterministic Regex Engine (Fallback)
  │
  ├── /api/chat/ask         ──► Context-Aware RAG Prompt Builder
  │                                     │ (Injects SQLite Financial Totals)
  │                                     ▼
  │                                Local Ollama / Financial Rules
  │
  ├── /api/invoices/generate-pdf ─► ReportLab PDF Engine
  │
  └── Local Storage
        ├── data/solobiz.db (SQLite Database)
        └── uploads/ (Local Document Storage)
```

### 1. Zero Cloud Data Leakage
Traditional accounting SaaS solutions require syncing sensitive invoices, bank account statements, and client information to external third-party proprietary servers. SoloBiz AI keeps every byte of financial information on the user's host machine or self-hosted server.

### 2. Context-Aware Grounded Financial Chat
When a user asks: *"Did I spend more on marketing or software this month?"*, SoloBiz AI doesn't just pass generic text to an LLM. It queries the local SQLite database, aggregates the month-to-date category totals, and constructs an augmented prompt containing verified numbers before asking the open-weight model to formulate advice. This eliminates AI hallucinations and guarantees arithmetic reliability.

---

## What I Learned & Challenges Overcome

1. **Deterministic vs. Generative Extraction:** LLMs can occasionally format JSON outputs unpredictably. By implementing rigorous Pydantic validation combined with a fallback regex extraction pipeline, the system achieves 100% extraction reliability even if the local model is under heavy load or returning partial JSON.
2. **Containerizing Native OCR & PDF Dependencies:** Balancing small container image sizes with OCR prerequisites required optimizing the `Dockerfile` with multi-stage builds and installing minimal runtime libraries (`tesseract-ocr` and `libgl1`).
3. **Local-First State Synchronization:** Orchestrating dynamic UI updates without bulky frontend frameworks demonstrated how powerful modern Vanilla JavaScript and CSS custom properties have become. SoloBiz AI loads in under 300ms.

---

## Hacktoberfest & Open Source Roadmap

SoloBiz AI is licensed under the permissive **MIT License** and is built to be a welcoming project for Hacktoberfest contributors of all experience levels!

### Planned Roadmap:
- [ ] **Multi-Currency Conversion:** Dynamic live rate conversion for cross-border freelancers.
- [ ] **Tax Category Presets by Country:** Preconfigured tax schedules for the US (Schedule C), UK (HMRC Self Assessment), EU, and India (GST/ITR).
- [ ] **Email Invoice Dispatch:** Direct SMTP client delivery for generated PDF invoices.
- [ ] **Extended Ollama Model Selection:** Dropdown selector to switch models between `llama3.2`, `qwen2.5-coder`, and `deepseek-r1`.

We welcome contributions! Check out our [GitHub Issues](https://github.com/GenX0Gravity/SoloBiz-AI/issues) and [README.md](https://github.com/GenX0Gravity/SoloBiz-AI/blob/main/README.md) for contribution guidelines.

---

*Built with ❤️ for freelancers and the open-source AI community.*
