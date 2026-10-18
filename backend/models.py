from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import date as DateType

# ----------------- Expense Models -----------------

class ExpenseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Merchant or expense description")
    amount: float = Field(..., ge=0.0, description="Total amount spent")
    currency: str = Field("USD", max_length=10)
    category: str = Field("Other", description="Expense category e.g. Software, Travel, etc.")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    payment_method: str = Field("Credit Card", max_length=50)
    tax_amount: float = Field(0.0, ge=0.0)
    subtotal: float = Field(0.0, ge=0.0)
    notes: Optional[str] = Field("", max_length=1000)
    document_id: Optional[int] = None
    is_verified: int = Field(1, ge=0, le=1)

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[float] = Field(None, ge=0.0)
    currency: Optional[str] = None
    category: Optional[str] = None
    date: Optional[str] = None
    payment_method: Optional[str] = None
    tax_amount: Optional[float] = None
    subtotal: Optional[float] = None
    notes: Optional[str] = None
    document_id: Optional[int] = None
    is_verified: Optional[int] = None

class ExpenseResponse(ExpenseBase):
    id: int
    created_at: str

# ----------------- Invoice Models -----------------

class InvoiceItemBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=250)
    quantity: float = Field(1.0, gt=0.0)
    unit_price: float = Field(0.0, ge=0.0)
    line_total: float = Field(0.0, ge=0.0)
    sort_order: int = Field(0, ge=0)

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItemResponse(InvoiceItemBase):
    id: int
    invoice_id: int

class InvoiceBase(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=50)
    client_name: str = Field(..., min_length=1, max_length=150)
    client_email: Optional[str] = Field("", max_length=150)
    client_address: Optional[str] = Field("", max_length=300)
    sender_name: Optional[str] = Field("SoloBiz Freelancer", max_length=150)
    sender_email: Optional[str] = Field("", max_length=150)
    sender_address: Optional[str] = Field("", max_length=300)
    issue_date: str = Field(..., description="YYYY-MM-DD")
    due_date: str = Field(..., description="YYYY-MM-DD")
    status: str = Field("Draft", description="Draft, Sent, Paid, Overdue, Cancelled")
    currency: str = Field("USD", max_length=10)
    tax_rate: float = Field(0.0, ge=0.0, le=100.0, description="Tax rate in percentage")
    discount_rate: float = Field(0.0, ge=0.0, le=100.0, description="Discount rate in percentage")
    notes: Optional[str] = Field("", max_length=1000)

class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate] = Field(..., min_length=1)

class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_address: Optional[str] = None
    sender_name: Optional[str] = None
    sender_email: Optional[str] = None
    sender_address: Optional[str] = None
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    currency: Optional[str] = None
    tax_rate: Optional[float] = None
    discount_rate: Optional[float] = None
    notes: Optional[str] = None
    items: Optional[List[InvoiceItemCreate]] = None

class InvoiceResponse(InvoiceBase):
    id: int
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    created_at: str
    items: List[InvoiceItemResponse] = []

# ----------------- Document & Extraction Models -----------------

class ExtractedInvoiceData(BaseModel):
    merchant_or_client: Optional[str] = None
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    category: Optional[str] = "Other"
    currency: str = "USD"
    confidence_notes: Optional[str] = None
    raw_text_snippet: Optional[str] = None
    extraction_source: str = "rule_based"  # 'ollama' or 'rule_based'

class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    file_hash: Optional[str] = None
    extracted_text: Optional[str] = None
    extraction_status: str
    created_at: str

class VerifyAndSaveReceiptRequest(BaseModel):
    document_id: int
    title: str
    amount: float
    currency: str = "USD"
    category: str
    date: str
    tax_amount: float = 0.0
    subtotal: float = 0.0
    payment_method: str = "Credit Card"
    notes: Optional[str] = ""

# ----------------- AI Assistant Models -----------------

class AIChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str

class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: List[AIChatMessage] = Field(default_factory=list)

class AIChatResponse(BaseModel):
    response: str
    grounding_facts: List[str] = []
    source: str = "ollama"  # 'ollama' or 'local_rule_engine'
    model: str
    is_fallback: bool = False

class AIStatusResponse(BaseModel):
    available: bool
    status_message: str
    host: str
    configured_model: str
    installed_models: List[str] = []
    recommended_models: List[Dict[str, str]] = []
    is_model_installed: bool = False

# ----------------- Analytics Models -----------------

class CategoryBreakdown(BaseModel):
    category: str
    total_amount: float
    count: int
    percentage: float

class MonthlySpend(BaseModel):
    month: str  # YYYY-MM
    total_amount: float
    count: int

class AnalyticsOverview(BaseModel):
    total_expenses: float
    current_month_expenses: float
    previous_month_expenses: float
    month_over_month_change_pct: float
    pending_invoices_count: int
    pending_invoices_amount: float
    paid_invoices_amount: float
    total_receipts_scanned: int
    category_breakdown: List[CategoryBreakdown]
    monthly_trends: List[MonthlySpend]
    recent_transactions: List[ExpenseResponse]
