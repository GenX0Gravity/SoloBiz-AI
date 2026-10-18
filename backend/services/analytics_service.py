import csv
import io
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from backend.database import get_db_connection

def get_analytics_overview() -> Dict[str, Any]:
    """
    Query database for complete expense analytics, monthly trends,
    category breakdowns, and pending invoice totals.
    """
    now = datetime.now()
    curr_month_str = now.strftime("%Y-%m")
    # Compute previous month
    first_day_curr = now.replace(day=1)
    prev_month_date = first_day_curr - timedelta(days=1)
    prev_month_str = prev_month_date.strftime("%Y-%m")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Total expenses all-time
        cursor.execute("SELECT COALESCE(SUM(amount), 0.0) AS total FROM expenses;")
        total_expenses = float(cursor.fetchone()["total"])

        # 2. Current month expenses
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0.0) AS total FROM expenses WHERE strftime('%Y-%m', date) = ?;",
            (curr_month_str,),
        )
        current_month_expenses = float(cursor.fetchone()["total"])

        # 3. Previous month expenses
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0.0) AS total FROM expenses WHERE strftime('%Y-%m', date) = ?;",
            (prev_month_str,),
        )
        previous_month_expenses = float(cursor.fetchone()["total"])

        # Month-over-month change percentage
        if previous_month_expenses > 0:
            mom_change = ((current_month_expenses - previous_month_expenses) / previous_month_expenses) * 100.0
        else:
            mom_change = 0.0

        # 4. Pending & Paid Invoices
        cursor.execute(
            "SELECT COUNT(*) AS count, COALESCE(SUM(total_amount), 0.0) AS total FROM invoices WHERE status IN ('Draft', 'Sent', 'Overdue');"
        )
        pending_row = cursor.fetchone()
        pending_count = int(pending_row["count"])
        pending_amount = float(pending_row["total"])

        cursor.execute(
            "SELECT COALESCE(SUM(total_amount), 0.0) AS total FROM invoices WHERE status = 'Paid';"
        )
        paid_amount = float(cursor.fetchone()["total"])

        # 5. Documents / receipts scanned count
        cursor.execute("SELECT COUNT(*) AS count FROM documents;")
        scanned_count = int(cursor.fetchone()["count"])

        # 6. Category breakdown
        cursor.execute(
            """
            SELECT category, COALESCE(SUM(amount), 0.0) AS total_amount, COUNT(*) AS count
            FROM expenses
            GROUP BY category
            ORDER BY total_amount DESC;
            """
        )
        cat_rows = cursor.fetchall()
        category_breakdown = []
        for r in cat_rows:
            amt = float(r["total_amount"])
            pct = (amt / total_expenses * 100.0) if total_expenses > 0 else 0.0
            category_breakdown.append({
                "category": r["category"],
                "total_amount": round(amt, 2),
                "count": r["count"],
                "percentage": round(pct, 1),
            })

        # 7. Monthly trends (last 6 months)
        cursor.execute(
            """
            SELECT strftime('%Y-%m', date) AS month, COALESCE(SUM(amount), 0.0) AS total_amount, COUNT(*) AS count
            FROM expenses
            GROUP BY month
            ORDER BY month ASC
            LIMIT 12;
            """
        )
        monthly_trends = [
            {
                "month": r["month"] or "Unknown",
                "total_amount": round(float(r["total_amount"]), 2),
                "count": r["count"],
            }
            for r in cursor.fetchall()
        ]

        # 8. Recent 10 transactions
        cursor.execute(
            """
            SELECT id, title, amount, currency, category, date, payment_method, tax_amount, subtotal, notes, document_id, is_verified, created_at
            FROM expenses
            ORDER BY date DESC, id DESC
            LIMIT 10;
            """
        )
        recent_transactions = cursor.fetchall()

    return {
        "total_expenses": round(total_expenses, 2),
        "current_month_expenses": round(current_month_expenses, 2),
        "previous_month_expenses": round(previous_month_expenses, 2),
        "month_over_month_change_pct": round(mom_change, 1),
        "pending_invoices_count": pending_count,
        "pending_invoices_amount": round(pending_amount, 2),
        "paid_invoices_amount": round(paid_amount, 2),
        "total_receipts_scanned": scanned_count,
        "category_breakdown": category_breakdown,
        "monthly_trends": monthly_trends,
        "recent_transactions": recent_transactions,
    }


def export_expenses_to_csv(
    category: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """Export filtered expenses to CSV formatted string."""
    query = """
        SELECT id, date, title, category, amount, currency, tax_amount, subtotal, payment_method, notes, document_id, created_at
        FROM expenses
        WHERE 1=1
    """
    params: List[Any] = []

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

    query += " ORDER BY date DESC, id DESC"

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Expense ID",
        "Date",
        "Merchant / Title",
        "Category",
        "Amount",
        "Currency",
        "Tax Amount",
        "Subtotal",
        "Payment Method",
        "Notes",
        "Document ID",
        "Created At",
    ])

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        for r in cursor.fetchall():
            writer.writerow([
                r["id"],
                r["date"],
                r["title"],
                r["category"],
                f"{r['amount']:.2f}",
                r["currency"],
                f"{r['tax_amount']:.2f}",
                f"{r['subtotal']:.2f}",
                r["payment_method"],
                r["notes"],
                r["document_id"] or "",
                r["created_at"],
            ])

    return output.getvalue()
