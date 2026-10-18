import os
from datetime import datetime, timedelta
from backend.database import init_db, get_db_connection
from backend.services.invoice_service import calculate_invoice_totals

def seed_sample_data():
    """Populate database with realistic freelance and business records."""
    init_db()

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    month_str = now.strftime("%Y-%m")
    
    # Calculate relative dates for realistic timeline
    def days_ago(d: int) -> str:
        return (now - timedelta(days=d)).strftime("%Y-%m-%d")

    sample_expenses = [
        # Software & Cloud
        {"title": "GitHub Enterprise & Copilot", "amount": 39.00, "category": "Software", "date": days_ago(2), "subtotal": 39.00, "tax_amount": 0.00, "payment_method": "Credit Card", "notes": "Monthly developer tooling subscription"},
        {"title": "Figma Professional", "amount": 15.00, "category": "Software", "date": days_ago(5), "subtotal": 15.00, "tax_amount": 0.00, "payment_method": "Credit Card", "notes": "Design and prototyping seat"},
        {"title": "AWS Cloud Hosting (Production)", "amount": 142.80, "category": "Software", "date": days_ago(12), "subtotal": 130.00, "tax_amount": 12.80, "payment_method": "Credit Card", "notes": "EC2, S3 & CloudFront client infrastructure"},
        {"title": "Slack Pro Workspace", "amount": 8.75, "category": "Software", "date": days_ago(18), "subtotal": 8.75, "tax_amount": 0.00, "payment_method": "Credit Card", "notes": "Client communications channel"},
        {"title": "Vercel Pro Team", "amount": 20.00, "category": "Software", "date": days_ago(25), "subtotal": 20.00, "tax_amount": 0.00, "payment_method": "Credit Card", "notes": "Frontend deployment platform"},
        # Marketing & Growth
        {"title": "Google Ads Campaign", "amount": 250.00, "category": "Marketing", "date": days_ago(8), "subtotal": 250.00, "tax_amount": 0.00, "payment_method": "Credit Card", "notes": "Q4 Freelance consulting acquisition ads"},
        {"title": "Domain Name Renewals (Namecheap)", "amount": 32.40, "category": "Marketing", "date": days_ago(22), "subtotal": 30.00, "tax_amount": 2.40, "payment_method": "PayPal", "notes": "Portfolio & project domain registrations"},
        # Equipment & Hardware
        {"title": "Dell UltraSharp 27'' 4K Monitor", "amount": 549.99, "category": "Equipment", "date": days_ago(35), "subtotal": 500.00, "tax_amount": 49.99, "payment_method": "Debit Card", "notes": "Workstation upgrade for pair programming & design"},
        {"title": "Logitech MX Master 3S Mouse", "amount": 99.00, "category": "Equipment", "date": days_ago(40), "subtotal": 90.00, "tax_amount": 9.00, "payment_method": "Credit Card", "notes": "Ergonomic hardware upgrade"},
        # Travel & Meals
        {"title": "Uber ride to Client Onsite Briefing", "amount": 34.50, "category": "Travel", "date": days_ago(6), "subtotal": 30.00, "tax_amount": 4.50, "payment_method": "Apple Pay", "notes": "Travel to downtown client headquarters"},
        {"title": "Delta Airlines Flight - Tech Conference", "amount": 384.20, "category": "Travel", "date": days_ago(28), "subtotal": 350.00, "tax_amount": 34.20, "payment_method": "Credit Card", "notes": "Open Source Developers Summit travel"},
        # Legal & Professional
        {"title": "CPA Tax Consulting Session", "amount": 175.00, "category": "Legal & Professional", "date": days_ago(15), "subtotal": 175.00, "tax_amount": 0.00, "payment_method": "Bank Transfer", "notes": "Quarterly estimated tax filing consultation"},
        # Utilities
        {"title": "Fiber Gigabit Internet (Home Office)", "amount": 79.99, "category": "Utilities", "date": days_ago(14), "subtotal": 79.99, "tax_amount": 0.00, "payment_method": "Auto-Debit", "notes": "Dedicated 50% home office business deduction"},
    ]

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check if already seeded
        cursor.execute("SELECT COUNT(*) as cnt FROM expenses;")
        if cursor.fetchone()["cnt"] > 0:
            print("Database already contains records. Skipping seed.")
            return

        print("Seeding sample expenses...")
        for exp in sample_expenses:
            cursor.execute(
                """
                INSERT INTO expenses (
                    title, amount, currency, category, date, payment_method,
                    tax_amount, subtotal, notes, is_verified, created_at
                ) VALUES (?, ?, 'USD', ?, ?, ?, ?, ?, ?, 1, ?);
                """,
                (
                    exp["title"],
                    exp["amount"],
                    exp["category"],
                    exp["date"],
                    exp["payment_method"],
                    exp["tax_amount"],
                    exp["subtotal"],
                    exp["notes"],
                    now.isoformat(),
                ),
            )

        # Seed sample invoices
        sample_invoices = [
            {
                "invoice_number": "INV-2026-001",
                "client_name": "Acme Innovations Ltd",
                "client_email": "billing@acmeinnovations.io",
                "client_address": "742 Evergreen Terrace, Tech District, CA 94107",
                "sender_name": "SoloBiz Studio",
                "sender_email": "alex@solobiz.studio",
                "sender_address": "120 Freelance Way, Suite 400, Austin, TX 78701",
                "issue_date": days_ago(20),
                "due_date": days_ago(5),
                "status": "Paid",
                "currency": "USD",
                "tax_rate": 8.25,
                "discount_rate": 5.0,
                "notes": "Thank you for working with us on the Full-Stack Web Application!",
                "items": [
                    {"description": "Full-Stack Web Application Development (Sprint 1 & 2)", "quantity": 40.0, "unit_price": 85.0},
                    {"description": "UI/UX Dashboard Prototyping & Glassmorphism Design", "quantity": 15.0, "unit_price": 75.0},
                    {"description": "Local AI Model Integration & Architecture Setup", "quantity": 10.0, "unit_price": 95.0},
                ],
            },
            {
                "invoice_number": "INV-2026-002",
                "client_name": "Apex Cloud Ventures",
                "client_email": "finance@apexcloud.co",
                "client_address": "100 Market St, Floor 14, San Francisco, CA 94105",
                "sender_name": "SoloBiz Studio",
                "sender_email": "alex@solobiz.studio",
                "sender_address": "120 Freelance Way, Suite 400, Austin, TX 78701",
                "issue_date": days_ago(7),
                "due_date": (now + timedelta(days=14)).strftime("%Y-%m-%d"),
                "status": "Sent",
                "currency": "USD",
                "tax_rate": 8.25,
                "discount_rate": 0.0,
                "notes": "Payment terms: Net 21. Direct deposit preferred.",
                "items": [
                    {"description": "FastAPI Microservice Architecture & SQLite Integration", "quantity": 25.0, "unit_price": 90.0},
                    {"description": "Document OCR & PDF Pipeline Implementation", "quantity": 12.0, "unit_price": 90.0},
                ],
            },
            {
                "invoice_number": "INV-2026-003",
                "client_name": "Nexus Media Studio",
                "client_email": "accounts@nexusmedia.design",
                "client_address": "55 Broadway, Brooklyn, NY 11249",
                "sender_name": "SoloBiz Studio",
                "sender_email": "alex@solobiz.studio",
                "sender_address": "120 Freelance Way, Suite 400, Austin, TX 78701",
                "issue_date": days_ago(1),
                "due_date": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
                "status": "Draft",
                "currency": "USD",
                "tax_rate": 0.0,
                "discount_rate": 0.0,
                "notes": "Draft for milestone 3 review.",
                "items": [
                    {"description": "Quarterly Technical Advisory & Strategy Retainer", "quantity": 1.0, "unit_price": 2500.0},
                ],
            },
        ]

        print("Seeding sample invoices...")
        for inv in sample_invoices:
            calc = calculate_invoice_totals(inv["items"], inv["tax_rate"], inv["discount_rate"])
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
                    inv["invoice_number"],
                    inv["client_name"],
                    inv["client_email"],
                    inv["client_address"],
                    inv["sender_name"],
                    inv["sender_email"],
                    inv["sender_address"],
                    inv["issue_date"],
                    inv["due_date"],
                    inv["status"],
                    inv["currency"],
                    calc["subtotal"],
                    calc["tax_rate"],
                    calc["tax_amount"],
                    calc["discount_rate"],
                    calc["discount_amount"],
                    calc["total_amount"],
                    inv["notes"],
                    now.isoformat(),
                ),
            )
            invoice_id = cursor.lastrowid
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

        print("Sample data successfully seeded!")

seed_demo_data = seed_sample_data

if __name__ == "__main__":
    seed_sample_data()
