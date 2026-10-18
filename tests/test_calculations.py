import pytest
from backend.services.invoice_service import calculate_invoice_totals

def test_basic_invoice_calculation():
    items = [
        {"description": "Design consultation", "quantity": 10.0, "unit_price": 50.0},
        {"description": "Web development", "quantity": 20.0, "unit_price": 80.0},
    ]
    # subtotal = 500 + 1600 = 2100
    calc = calculate_invoice_totals(items, tax_rate=10.0, discount_rate=5.0)

    assert calc["subtotal"] == 2100.0
    # 5% discount on 2100 = 105.00
    assert calc["discount_amount"] == 105.0
    # Taxable base = 2100 - 105 = 1995.00
    # 10% tax on 1995 = 199.50
    assert calc["tax_amount"] == 199.5
    # Total = 1995 + 199.50 = 2194.50
    assert calc["total_amount"] == 2194.5

def test_zero_tax_and_zero_discount():
    items = [
        {"description": "SEO Audit", "quantity": 1.0, "unit_price": 450.0},
    ]
    calc = calculate_invoice_totals(items, tax_rate=0.0, discount_rate=0.0)

    assert calc["subtotal"] == 450.0
    assert calc["discount_amount"] == 0.0
    assert calc["tax_amount"] == 0.0
    assert calc["total_amount"] == 450.0

def test_decimal_rounding_precision():
    # Test fractional cents rounding (ROUND_HALF_UP)
    items = [
        {"description": "Item 1", "quantity": 3.0, "unit_price": 33.333},
    ]
    calc = calculate_invoice_totals(items, tax_rate=8.25, discount_rate=0.0)

    # 3 * 33.333 = 99.999 -> rounds to 100.00
    assert calc["subtotal"] == 100.00
    # 8.25% of 100.00 = 8.25
    assert calc["tax_amount"] == 8.25
    assert calc["total_amount"] == 108.25
