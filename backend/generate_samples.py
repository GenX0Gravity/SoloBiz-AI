import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import reportlab
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_sample_pdf(output_path: Path):
    """Generate a realistic test PDF invoice."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    
    story = [
        Paragraph("<b>AMAZON WEB SERVICES, INC.</b>", styles["Title"]),
        Paragraph("Invoice Number: INV-AWS-849201", styles["Normal"]),
        Paragraph("Date: 2026-10-14", styles["Normal"]),
        Spacer(1, 15),
        Paragraph("<b>Account Summary</b>", styles["Heading2"]),
        Paragraph("Subtotal: $130.00", styles["Normal"]),
        Paragraph("Estimated Tax (VAT): $12.80", styles["Normal"]),
        Paragraph("<b>Total Amount Due: $142.80</b>", styles["Normal"]),
        Spacer(1, 15),
        Paragraph("Service: Amazon Elastic Compute Cloud (EC2) & Simple Storage Service (S3)", styles["Normal"]),
        Paragraph("Payment Method: Visa ending in 4242", styles["Normal"]),
    ]
    doc.build(story)
    print(f"Sample PDF created at {output_path}")

def create_sample_receipt_image(output_path: Path):
    """Generate a clean sample receipt image with readable text."""
    width, height = 500, 600
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw simulated receipt text
    lines = [
        ("BLUE BOTTLE COFFEE", 40, True),
        ("San Francisco, CA", 80, False),
        ("Date: 2026-10-15", 120, False),
        ("Order #9402", 150, False),
        ("----------------------------------", 180, False),
        ("1x Hayes Valley Espresso    $4.50", 220, False),
        ("1x Almond Croissant         $5.25", 260, False),
        ("1x Cold Brew Can            $4.75", 300, False),
        ("----------------------------------", 340, False),
        ("Subtotal:                  $14.50", 380, False),
        ("Tax (8.5%):                 $1.23", 420, False),
        ("TOTAL:                     $15.73", 470, True),
        ("----------------------------------", 510, False),
        ("Category: Travel & Meals", 540, False),
    ]

    for text, y, is_bold in lines:
        draw.text((40, y), text, fill=(20, 20, 20))

    img.save(str(output_path))
    print(f"Sample receipt image created at {output_path}")

if __name__ == "__main__":
    sample_dir = Path(__file__).resolve().parent.parent / "sample_receipts"
    sample_dir.mkdir(parents=True, exist_ok=True)
    create_sample_pdf(sample_dir / "sample_aws_receipt.pdf")
    create_sample_receipt_image(sample_dir / "sample_coffee_receipt.png")
