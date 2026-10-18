import os
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    Query,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse

from backend.config import (
    APP_NAME,
    APP_VERSION,
    UPLOAD_DIR,
    BASE_DIR,
    MAX_UPLOAD_SIZE_BYTES,
)
from backend.database import init_db, get_db_connection
from backend.models import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    AIChatRequest,
    AIChatResponse,
    AIStatusResponse,
    AnalyticsOverview,
    VerifyAndSaveReceiptRequest,
    DocumentResponse,
    ExtractedInvoiceData,
)
from backend.services.document_service import process_uploaded_document
from backend.services.ai_service import (
    extract_receipt_with_ai,
    ask_business_assistant,
    check_ollama_status,
)
from backend.services.invoice_service import (
    calculate_invoice_totals,
    generate_invoice_pdf,
)
from backend.services.analytics_service import (
    get_analytics_overview,
    export_expenses_to_csv,
)

from contextlib import asynccontextmanager

# Application Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

# Initialize application
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="A Local-First AI Business Assistant for Freelancers and Small Businesses",
    lifespan=lifespan,
)

# Enable CORS for local development and cloud deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Health & Status Endpoints -----------------

@app.get("/api/index.py")
@app.get("/api/index")
def vercel_entrypoint_fallback():
    index_file = BASE_DIR / "frontend" / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "online", "message": "SoloBiz AI API"}

@app.get("/health")
@app.get("/api/health")
def health_check():
    """System health check endpoint for monitoring and container orchestration."""
    db_ok = False
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1;").fetchone()
            db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "online" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/api/ai/status", response_model=AIStatusResponse)
async def get_ai_status():
    """Check Ollama connectivity and model availability."""
    return await check_ollama_status()

# ----------------- AI Business Assistant -----------------

@app.post("/api/ai/chat", response_model=AIChatResponse)
async def chat_with_assistant(payload: AIChatRequest):
    """
    Chat with the business assistant. Queries real SQLite database records
    to ground answers in verified financial facts.
    """
    overview = get_analytics_overview()
    history_dicts = [{"role": m.role, "content": m.content} for m in payload.history]
    return await ask_business_assistant(payload.message, history_dicts, overview)

# ----------------- Analytics Endpoints -----------------

@app.get("/api/analytics/overview")
def get_analytics():
    """Retrieve full dashboard analytics overview."""
    return get_analytics_overview()

@app.get("/api/analytics/export/csv")
def export_csv(
    category: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Download verified expense records as a CSV spreadsheet."""
    csv_content = export_expenses_to_csv(category, search, start_date, end_date)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"solobiz_expenses_{timestamp}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

# ----------------- Expense CRUD Endpoints -----------------

@app.get("/api/expenses", response_model=List[ExpenseResponse])
def list_expenses(
    category: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List expenses with optional search and category filters."""
    query = "SELECT * FROM expenses WHERE 1=1"
    params: List[object] = []

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (title LIKE ? OR notes LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term])

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [ExpenseResponse(**r) for r in rows]

@app.post("/api/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(payload: ExpenseCreate):
    """Create a new verified expense record."""
    now_str = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO expenses (
                title, amount, currency, category, date, payment_method,
                tax_amount, subtotal, notes, document_id, is_verified, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                payload.title,
                payload.amount,
                payload.currency,
                payload.category,
                payload.date,
                payload.payment_method,
                payload.tax_amount,
                payload.subtotal,
                payload.notes or "",
                payload.document_id,
                payload.is_verified,
                now_str,
            ),
        )
        new_id = cursor.lastrowid
        cursor.execute("SELECT * FROM expenses WHERE id = ?;", (new_id,))
        row = cursor.fetchone()
        return ExpenseResponse(**row)

@app.get("/api/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int):
    """Fetch single expense by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?;", (expense_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Expense not found")
        return ExpenseResponse(**row)

@app.put("/api/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, payload: ExpenseUpdate):
    """Update existing expense."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?;", (expense_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Expense not found")

        updates = []
        params = []
        for field, value in payload.model_dump(exclude_unset=True).items():
            updates.append(f"{field} = ?")
            params.append(value)

        if updates:
            params.append(expense_id)
            cursor.execute(f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?;", params)

        cursor.execute("SELECT * FROM expenses WHERE id = ?;", (expense_id,))
        return ExpenseResponse(**cursor.fetchone())

@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: int):
    """Delete an expense record."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM expenses WHERE id = ?;", (expense_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Expense not found")
        cursor.execute("DELETE FROM expenses WHERE id = ?;", (expense_id,))
        return {"success": True, "message": f"Expense {expense_id} deleted."}

# ----------------- Document Upload & AI Scanner -----------------

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a receipt or invoice document (PDF, PNG, JPG).
    Saves document locally, extracts text, runs local AI extraction (or rule-based fallback),
    and returns fields for user verification before committing to expenses.
    """
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds maximum allowed size.")

    try:
        doc_info = process_uploaded_document(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check for duplicate document hash in database
    is_duplicate = False
    doc_id = None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, original_filename, extracted_text FROM documents WHERE file_hash = ?;",
            (doc_info["file_hash"],),
        )
        existing_doc = cursor.fetchone()
        if existing_doc:
            is_duplicate = True
            doc_id = existing_doc["id"]

    now_str = datetime.now().isoformat()
    if not is_duplicate:
        # Save document record
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO documents (
                    original_filename, stored_filename, file_path, file_type,
                    file_size, file_hash, extracted_text, extraction_status,
                    raw_metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    doc_info["original_filename"],
                    doc_info["stored_filename"],
                    doc_info["file_path"],
                    doc_info["file_type"],
                    doc_info["file_size"],
                    doc_info["file_hash"],
                    doc_info["extracted_text"],
                    "completed" if doc_info["extracted_text"] else "partial",
                    json.dumps(doc_info["metadata"]),
                    now_str,
                ),
            )
            doc_id = cursor.lastrowid

    # Run AI extraction on extracted text
    extracted_data = await extract_receipt_with_ai(doc_info["extracted_text"])

    return {
        "document_id": doc_id,
        "filename": doc_info["original_filename"],
        "file_type": doc_info["file_type"],
        "file_size": doc_info["file_size"],
        "is_duplicate": is_duplicate,
        "extracted_text_snippet": doc_info["extracted_text"][:500] if doc_info["extracted_text"] else "",
        "extracted_data": extracted_data,
        "verification_required": True,
    }

@app.post("/api/documents/verify-save", response_model=ExpenseResponse)
def verify_and_save_receipt(payload: VerifyAndSaveReceiptRequest):
    """
    Commit user-verified receipt fields into the expenses database.
    Guarantees that no unverified or hallucinated AI fields are saved automatically.
    """
    now_str = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Ensure document exists
        cursor.execute("SELECT id FROM documents WHERE id = ?;", (payload.document_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Referenced document not found.")

        cursor.execute(
            """
            INSERT INTO expenses (
                title, amount, currency, category, date, payment_method,
                tax_amount, subtotal, notes, document_id, is_verified, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
            """,
            (
                payload.title,
                payload.amount,
                payload.currency,
                payload.category,
                payload.date,
                payload.payment_method,
                payload.tax_amount,
                payload.subtotal,
                payload.notes or "",
                payload.document_id,
                now_str,
            ),
        )
        expense_id = cursor.lastrowid
        cursor.execute("SELECT * FROM expenses WHERE id = ?;", (expense_id,))
        return ExpenseResponse(**cursor.fetchone())

@app.get("/api/documents", response_model=List[DocumentResponse])
def list_documents(limit: int = 50):
    """List recent uploaded documents."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, original_filename, stored_filename, file_type, file_size, file_hash, extracted_text, extraction_status, created_at FROM documents ORDER BY id DESC LIMIT ?;",
            (limit,),
        )
        return [DocumentResponse(**r) for r in cursor.fetchall()]

@app.get("/api/documents/{doc_id}/file")
def get_document_file(doc_id: int):
    """Serve local document file for preview/download."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT file_path, original_filename, file_type FROM documents WHERE id = ?;", (doc_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Document not found.")

    file_path = Path(row["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file missing on disk.")

    media_type = "application/pdf" if row["file_type"] == "pdf" else "image/png"
    return FileResponse(
        path=str(file_path),
        filename=row["original_filename"],
        media_type=media_type,
    )

# ----------------- Invoice Generator Endpoints -----------------

@app.get("/api/invoices", response_model=List[InvoiceResponse])
def list_invoices(status_filter: Optional[str] = None):
    """List generated invoices with their items and calculated totals."""
    query = "SELECT * FROM invoices WHERE 1=1"
    params: List[object] = []
    if status_filter and status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)
    query += " ORDER BY id DESC"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        invoices = cursor.fetchall()

        results = []
        for inv in invoices:
            cursor.execute(
                "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY sort_order ASC, id ASC;",
                (inv["id"],),
            )
            items = cursor.fetchall()
            inv_dict = dict(inv)
            inv_dict["items"] = items
            results.append(InvoiceResponse(**inv_dict))

        return results

@app.post("/api/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(payload: InvoiceCreate):
    """Create a new professional invoice with calculated totals."""
    items_dicts = [i.model_dump() for i in payload.items]
    calc = calculate_invoice_totals(items_dicts, payload.tax_rate, payload.discount_rate)

    now_str = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check invoice number uniqueness
        cursor.execute("SELECT id FROM invoices WHERE invoice_number = ?;", (payload.invoice_number,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Invoice number '{payload.invoice_number}' already exists. Please use a unique number.",
            )

        cursor.execute(
            """
            INSERT INTO invoices (
                invoice_number, client_name, client_email, client_address,
                sender_name, sender_email, sender_address, issue_date, due_date,
                status, currency, subtotal, tax_rate, tax_amount,
                discount_rate, discount_amount, total_amount, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                payload.invoice_number,
                payload.client_name,
                payload.client_email or "",
                payload.client_address or "",
                payload.sender_name or "",
                payload.sender_email or "",
                payload.sender_address or "",
                payload.issue_date,
                payload.due_date,
                payload.status,
                payload.currency,
                calc["subtotal"],
                calc["tax_rate"],
                calc["tax_amount"],
                calc["discount_rate"],
                calc["discount_amount"],
                calc["total_amount"],
                payload.notes or "",
                now_str,
            ),
        )
        invoice_id = cursor.lastrowid

        # Insert calculated line items
        for idx, item in enumerate(calc["items"]):
            cursor.execute(
                """
                INSERT INTO invoice_items (
                    invoice_id, description, quantity, unit_price, line_total, sort_order
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    invoice_id,
                    item["description"],
                    item["quantity"],
                    item["unit_price"],
                    item["line_total"],
                    idx,
                ),
            )

        # Retrieve and return complete object
        cursor.execute("SELECT * FROM invoices WHERE id = ?;", (invoice_id,))
        created_inv = dict(cursor.fetchone())
        cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY sort_order ASC;", (invoice_id,))
        created_inv["items"] = cursor.fetchall()
        return InvoiceResponse(**created_inv)

@app.get("/api/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int):
    """Retrieve full invoice details with line items."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE id = ?;", (invoice_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Invoice not found")
        inv_dict = dict(row)
        cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY sort_order ASC;", (invoice_id,))
        inv_dict["items"] = cursor.fetchall()
        return InvoiceResponse(**inv_dict)

@app.put("/api/invoices/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(invoice_id: int, payload: InvoiceUpdate):
    """Update invoice metadata and optionally recalculate line items."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE id = ?;", (invoice_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Recalculate if items or rates updated
        tax_rate = payload.tax_rate if payload.tax_rate is not None else existing["tax_rate"]
        disc_rate = payload.discount_rate if payload.discount_rate is not None else existing["discount_rate"]

        if payload.items is not None:
            # Delete old items and re-insert
            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?;", (invoice_id,))
            calc = calculate_invoice_totals([i.model_dump() for i in payload.items], tax_rate, disc_rate)
            for idx, item in enumerate(calc["items"]):
                cursor.execute(
                    """
                    INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, line_total, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (invoice_id, item["description"], item["quantity"], item["unit_price"], item["line_total"], idx),
                )
            subtotal = calc["subtotal"]
            tax_amount = calc["tax_amount"]
            disc_amount = calc["discount_amount"]
            total_amount = calc["total_amount"]
        else:
            # Recalculate based on existing items
            cursor.execute("SELECT description, quantity, unit_price FROM invoice_items WHERE invoice_id = ?;", (invoice_id,))
            existing_items = cursor.fetchall()
            calc = calculate_invoice_totals(existing_items, tax_rate, disc_rate)
            subtotal = calc["subtotal"]
            tax_amount = calc["tax_amount"]
            disc_amount = calc["discount_amount"]
            total_amount = calc["total_amount"]

        # Update invoice record
        cursor.execute(
            """
            UPDATE invoices SET
                client_name = COALESCE(?, client_name),
                client_email = COALESCE(?, client_email),
                client_address = COALESCE(?, client_address),
                sender_name = COALESCE(?, sender_name),
                sender_email = COALESCE(?, sender_email),
                sender_address = COALESCE(?, sender_address),
                issue_date = COALESCE(?, issue_date),
                due_date = COALESCE(?, due_date),
                status = COALESCE(?, status),
                currency = COALESCE(?, currency),
                tax_rate = ?,
                tax_amount = ?,
                discount_rate = ?,
                discount_amount = ?,
                subtotal = ?,
                total_amount = ?,
                notes = COALESCE(?, notes)
            WHERE id = ?;
            """,
            (
                payload.client_name,
                payload.client_email,
                payload.client_address,
                payload.sender_name,
                payload.sender_email,
                payload.sender_address,
                payload.issue_date,
                payload.due_date,
                payload.status,
                payload.currency,
                tax_rate,
                tax_amount,
                disc_rate,
                disc_amount,
                subtotal,
                total_amount,
                payload.notes,
                invoice_id,
            ),
        )

        cursor.execute("SELECT * FROM invoices WHERE id = ?;", (invoice_id,))
        updated = dict(cursor.fetchone())
        cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY sort_order ASC;", (invoice_id,))
        updated["items"] = cursor.fetchall()
        return InvoiceResponse(**updated)

@app.delete("/api/invoices/{invoice_id}")
def delete_invoice(invoice_id: int):
    """Delete an invoice and its associated line items."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM invoices WHERE id = ?;", (invoice_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Invoice not found")
        cursor.execute("DELETE FROM invoices WHERE id = ?;", (invoice_id,))
        return {"success": True, "message": f"Invoice {invoice_id} deleted."}

@app.get("/api/invoices/{invoice_id}/pdf")
def export_invoice_pdf(invoice_id: int):
    """Generate and stream a professional PDF invoice."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM invoices WHERE id = ?;", (invoice_id,))
        inv = cursor.fetchone()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        inv_dict = dict(inv)
        cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY sort_order ASC;", (invoice_id,))
        inv_dict["items"] = cursor.fetchall()

    pdf_bytes = generate_invoice_pdf(inv_dict)
    filename = f"Invoice_{inv_dict['invoice_number']}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )

# ----------------- Frontend Static Files Mounting -----------------

frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
