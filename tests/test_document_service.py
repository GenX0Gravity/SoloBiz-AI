import os
from pathlib import Path
import pytest
from backend.services.document_service import (
    sanitize_filename,
    validate_file_metadata,
    compute_file_hash,
    extract_text_from_pdf,
)
from backend.services.ai_service import rule_based_extract

def test_sanitize_filename():
    assert sanitize_filename("../../../etc/passwd.pdf") == "passwd.pdf"
    assert sanitize_filename("receipt??#--.pdf") == "receipt___--.pdf"
    assert sanitize_filename("   invoice.png  ") == "invoice.png"
    assert sanitize_filename("") == "document"

def test_validate_file_metadata():
    # Valid PDF
    valid, msg = validate_file_metadata("receipt.pdf", 5000, "application/pdf")
    assert valid is True

    # Disallowed extension
    valid, msg = validate_file_metadata("malware.exe", 5000, "application/octet-stream")
    assert valid is False
    assert "Unsupported file extension" in msg

    # Empty file
    valid, msg = validate_file_metadata("receipt.pdf", 0, "application/pdf")
    assert valid is False

def test_pdf_extraction_and_rule_parser():
    sample_pdf = Path(__file__).resolve().parent.parent / "sample_receipts" / "sample_aws_receipt.pdf"
    if sample_pdf.exists():
        text, meta = extract_text_from_pdf(sample_pdf)
        assert "AMAZON WEB SERVICES" in text
        assert "INV-AWS-849201" in text

        # Test rule-based financial parser on extracted text
        extracted = rule_based_extract(text)
        assert extracted.invoice_number == "INV-AWS-849201"
        assert extracted.date == "2026-10-14"
        assert extracted.total == 142.80
        assert extracted.subtotal == 130.00
        assert extracted.tax == 12.80
        assert extracted.category == "Software"
