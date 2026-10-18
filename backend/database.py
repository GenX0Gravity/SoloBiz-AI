import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from typing import Generator
from backend.config import DB_PATH

def dict_factory(cursor, row):
    """Convert sqlite3 row to dictionary."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH), timeout=20.0)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        conn.execute("PRAGMA journal_mode = DELETE;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    """Initialize database tables, relations, and indexes."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Documents Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_hash TEXT UNIQUE,
                extracted_text TEXT,
                extraction_status TEXT DEFAULT 'pending',
                raw_metadata TEXT,
                created_at TEXT NOT NULL
            );
        """)
        
        # Expenses Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD',
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                payment_method TEXT DEFAULT 'Credit Card',
                tax_amount REAL DEFAULT 0.0,
                subtotal REAL DEFAULT 0.0,
                notes TEXT DEFAULT '',
                document_id INTEGER,
                is_verified INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE SET NULL
            );
        """)
        
        # Invoices Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT NOT NULL UNIQUE,
                client_name TEXT NOT NULL,
                client_email TEXT DEFAULT '',
                client_address TEXT DEFAULT '',
                sender_name TEXT DEFAULT '',
                sender_email TEXT DEFAULT '',
                sender_address TEXT DEFAULT '',
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Draft',
                currency TEXT NOT NULL DEFAULT 'USD',
                subtotal REAL NOT NULL DEFAULT 0.0,
                tax_rate REAL NOT NULL DEFAULT 0.0,
                tax_amount REAL NOT NULL DEFAULT 0.0,
                discount_rate REAL NOT NULL DEFAULT 0.0,
                discount_amount REAL NOT NULL DEFAULT 0.0,
                total_amount REAL NOT NULL DEFAULT 0.0,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );
        """)
        
        # Invoice Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 1.0,
                unit_price REAL NOT NULL DEFAULT 0.0,
                line_total REAL NOT NULL DEFAULT 0.0,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
            );
        """)
        
        # Indexes for fast querying & analytics
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id);")

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
