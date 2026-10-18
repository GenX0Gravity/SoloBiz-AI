import io
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def calculate_invoice_totals(
    items: List[Dict[str, Any]],
    tax_rate: float = 0.0,
    discount_rate: float = 0.0,
) -> Dict[str, Any]:
    """
    Perform accurate monetary calculations for invoices using Decimal.
    Guarantees no floating-point rounding anomalies.
    """
    tax_rate_dec = Decimal(str(tax_rate))
    discount_rate_dec = Decimal(str(discount_rate))

    calculated_items = []
    subtotal = Decimal("0.00")

    for item in items:
        qty = Decimal(str(item.get("quantity", 1.0)))
        price = Decimal(str(item.get("unit_price", 0.0)))
        line_total = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal += line_total

        item_copy = dict(item)
        item_copy["quantity"] = float(qty)
        item_copy["unit_price"] = float(price)
        item_copy["line_total"] = float(line_total)
        calculated_items.append(item_copy)

    # Discount calculation
    discount_amount = Decimal("0.00")
    if discount_rate_dec > Decimal("0.00"):
        discount_amount = (subtotal * (discount_rate_dec / Decimal("100.00"))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    taxable_base = subtotal - discount_amount
    if taxable_base < Decimal("0.00"):
        taxable_base = Decimal("0.00")

    # Tax calculation
    tax_amount = Decimal("0.00")
    if tax_rate_dec > Decimal("0.00"):
        tax_amount = (taxable_base * (tax_rate_dec / Decimal("100.00"))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    total_amount = (taxable_base + tax_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "items": calculated_items,
        "subtotal": float(subtotal),
        "discount_rate": float(discount_rate_dec),
        "discount_amount": float(discount_amount),
        "tax_rate": float(tax_rate_dec),
        "tax_amount": float(tax_amount),
        "total_amount": float(total_amount),
    }


def generate_invoice_pdf(invoice_data: Dict[str, Any]) -> bytes:
    """
    Generate an elegant, professional PDF invoice using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0f172a")  # Slate 900
    brand_blue = colors.HexColor("#3b82f6")     # Blue 500
    text_muted = colors.HexColor("#64748b")     # Slate 500
    bg_light = colors.HexColor("#f8fafc")       # Slate 50
    border_color = colors.HexColor("#e2e8f0")   # Slate 200

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=30,
        textColor=primary_color,
    )

    badge_style = ParagraphStyle(
        "StatusBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#1e293b"),
        alignment=2,  # Right aligned
    )

    header_label = ParagraphStyle(
        "HeaderLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=primary_color,
    )

    body_style = ParagraphStyle(
        "InvoiceBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=primary_color,
    )

    muted_style = ParagraphStyle(
        "InvoiceMuted",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_muted,
    )

    story = []

    # 1. Header Row (Brand & Invoice details)
    invoice_num = invoice_data.get("invoice_number", "INV-001")
    status = invoice_data.get("status", "Draft").upper()
    currency = invoice_data.get("currency", "USD")

    sender_name = invoice_data.get("sender_name") or "SoloBiz Business"
    sender_email = invoice_data.get("sender_email") or ""
    sender_addr = invoice_data.get("sender_address") or ""

    header_left = [
        Paragraph("INVOICE", title_style),
        Spacer(1, 4),
        Paragraph(f"<b>Number:</b> {invoice_num}", body_style),
        Paragraph(f"<b>Issue Date:</b> {invoice_data.get('issue_date', '')}", muted_style),
        Paragraph(f"<b>Due Date:</b> {invoice_data.get('due_date', '')}", muted_style),
    ]

    header_right = [
        Paragraph(f"<b>STATUS: {status}</b>", badge_style),
        Spacer(1, 8),
        Paragraph(f"<b>{sender_name}</b>", header_label),
        Paragraph(sender_email, muted_style),
        Paragraph(sender_addr.replace("\n", "<br/>"), muted_style),
    ]

    header_table = Table([[header_left, header_right]], colWidths=[280, 252])
    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    story.append(header_table)
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=0, spaceAfter=15))

    # 2. Bill To Information
    client_name = invoice_data.get("client_name", "Valued Client")
    client_email = invoice_data.get("client_email", "")
    client_addr = invoice_data.get("client_address", "")

    bill_to_content = [
        Paragraph("<b>BILL TO:</b>", header_label),
        Paragraph(f"<b>{client_name}</b>", body_style),
        Paragraph(client_email, muted_style),
        Paragraph(client_addr.replace("\n", "<br/>"), muted_style),
    ]

    meta_content = [
        Paragraph("<b>PAYMENT TERMS:</b>", header_label),
        Paragraph(f"Payable in {currency}", body_style),
        Paragraph("Payment due upon agreed terms", muted_style),
    ]

    client_table = Table([[bill_to_content, meta_content]], colWidths=[320, 212])
    client_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
        ])
    )
    story.append(client_table)

    # 3. Line Items Table
    items = invoice_data.get("items", [])
    table_data = [
        [
            Paragraph("<b>Description</b>", header_label),
            Paragraph("<b>Qty</b>", header_label),
            Paragraph("<b>Unit Price</b>", header_label),
            Paragraph("<b>Line Total</b>", header_label),
        ]
    ]

    for item in items:
        desc = item.get("description", "")
        qty = f"{item.get('quantity', 1):.2f}".rstrip("0").rstrip(".")
        unit_price = f"${item.get('unit_price', 0.0):,.2f}"
        line_total = f"${item.get('line_total', 0.0):,.2f}"

        table_data.append([
            Paragraph(desc, body_style),
            Paragraph(qty, body_style),
            Paragraph(unit_price, body_style),
            Paragraph(line_total, body_style),
        ])

    items_table = Table(table_data, colWidths=[280, 60, 96, 96])
    items_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), bg_light),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 8),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, border_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (-1, -1), "LEFT"),
        ])
    )
    story.append(items_table)
    story.append(Spacer(1, 15))

    # 4. Summary & Totals
    subtotal = invoice_data.get("subtotal", 0.0)
    tax_rate = invoice_data.get("tax_rate", 0.0)
    tax_amount = invoice_data.get("tax_amount", 0.0)
    discount_rate = invoice_data.get("discount_rate", 0.0)
    discount_amount = invoice_data.get("discount_amount", 0.0)
    total_amount = invoice_data.get("total_amount", 0.0)

    summary_rows = [
        [Paragraph("Subtotal:", body_style), Paragraph(f"${subtotal:,.2f}", body_style)],
    ]
    if discount_amount > 0:
        summary_rows.append([
            Paragraph(f"Discount ({discount_rate}%):", muted_style),
            Paragraph(f"-${discount_amount:,.2f}", muted_style),
        ])
    if tax_amount > 0 or tax_rate > 0:
        summary_rows.append([
            Paragraph(f"Tax ({tax_rate}%):", muted_style),
            Paragraph(f"+${tax_amount:,.2f}", muted_style),
        ])

    summary_rows.append([
        Paragraph("<b>Total Amount Due:</b>", header_label),
        Paragraph(f"<b>${total_amount:,.2f} {currency}</b>", header_label),
    ])

    summary_table = Table(summary_rows, colWidths=[150, 100])
    summary_table.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("LINEABOVE", (0, -1), (-1, -1), 1, primary_color),
        ])
    )

    # Put notes on left, summary table on right
    notes_text = invoice_data.get("notes") or "Thank you for your business! Payment is appreciated."
    notes_block = [
        Paragraph("<b>NOTES & TERMS:</b>", header_label),
        Spacer(1, 4),
        Paragraph(notes_text.replace("\n", "<br/>"), muted_style),
    ]

    totals_layout = Table([[notes_block, summary_table]], colWidths=[270, 262])
    totals_layout.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    story.append(KeepTogether(totals_layout))

    # 5. Footer
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=0.5, color=border_color, spaceBefore=0, spaceAfter=8))
    footer_text = "Generated with SoloBiz AI — Local-First Financial Assistant for Freelancers"
    story.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=muted_style, alignment=1, fontSize=8)))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
