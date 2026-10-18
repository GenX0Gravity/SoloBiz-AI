import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["database"] == "connected"

    # Also test root /health used by cloud orchestrators
    res_root = client.get("/health")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "online"

def test_ai_status_endpoint():
    res = client.get("/api/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "configured_model" in data
    assert "recommended_models" in data
    assert len(data["recommended_models"]) > 0

def test_create_and_get_expense():
    payload = {
        "title": "JetBrains All Products Pack",
        "amount": 249.00,
        "currency": "USD",
        "category": "Software",
        "date": "2026-10-18",
        "payment_method": "Credit Card",
        "tax_amount": 0.0,
        "subtotal": 249.0,
        "notes": "IDE tooling license",
        "is_verified": 1,
    }
    create_res = client.post("/api/expenses", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["title"] == payload["title"]
    assert created["amount"] == 249.00

    exp_id = created["id"]
    get_res = client.get(f"/api/expenses/{exp_id}")
    assert get_res.status_code == 200
    assert get_res.json()["category"] == "Software"

def test_create_and_pdf_invoice():
    import uuid
    inv_num = f"TEST-INV-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "invoice_number": inv_num,
        "client_name": "Test Client Corp",
        "client_email": "test@corp.com",
        "client_address": "123 Test St",
        "sender_name": "SoloBiz Dev",
        "issue_date": "2026-10-18",
        "due_date": "2026-11-01",
        "status": "Draft",
        "currency": "USD",
        "tax_rate": 10.0,
        "discount_rate": 0.0,
        "notes": "Unit test invoice",
        "items": [
            {"description": "Backend API Development", "quantity": 10.0, "unit_price": 100.0, "line_total": 1000.0, "sort_order": 0}
        ],
    }
    res = client.post("/api/invoices", json=payload)
    assert res.status_code == 201
    inv_data = res.json()
    assert inv_data["subtotal"] == 1000.0
    assert inv_data["tax_amount"] == 100.0
    assert inv_data["total_amount"] == 1100.0

    # Test PDF generation endpoint
    inv_id = inv_data["id"]
    pdf_res = client.get(f"/api/invoices/{inv_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000

def test_export_csv():
    res = client.get("/api/analytics/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "Expense ID,Date,Merchant / Title" in res.text

def test_upload_pdf_receipt():
    sample_pdf = Path(__file__).resolve().parent.parent / "sample_receipts" / "sample_aws_receipt.pdf"
    if sample_pdf.exists():
        with open(sample_pdf, "rb") as f:
            res = client.post(
                "/api/documents/upload",
                files={"file": ("sample_aws_receipt.pdf", f, "application/pdf")},
            )
        assert res.status_code == 200
        data = res.json()
        assert data["verification_required"] is True
        assert data["extracted_data"]["total"] == 142.80
        assert data["extracted_data"]["invoice_number"] == "INV-AWS-849201"
