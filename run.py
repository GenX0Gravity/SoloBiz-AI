"""
SoloBiz AI — Application Launcher
Run with: python run.py
"""

import sys
import os
import uvicorn
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.database import init_db
from backend.seed_data import seed_sample_data
from backend.config import APP_HOST, APP_PORT

def main():
    print("=" * 65)
    print("  SoloBiz AI — A Local-First AI Business Assistant")
    print("  100% On-Device Financial Intelligence & Invoice Automation")
    print("=" * 65)

    # 1. Initialize DB and seed demo data if empty
    print("[*] Initializing local SQLite database...")
    init_db()
    print("[*] Checking sample data...")
    seed_sample_data()

    host = APP_HOST
    port = APP_PORT

    print(f"\n[+] SoloBiz AI is live at: http://{host}:{port}")
    print(f"[+] Local SQLite Database: {BASE_DIR / 'data' / 'solobiz.db'}")
    print(f"[+] Uploads Directory:    {BASE_DIR / 'uploads'}")
    print(f"[+] Ollama Model Config:  {os.getenv('OLLAMA_MODEL', 'llama3.2:latest')}")
    print("\nPress Ctrl+C to stop the server.\n")

    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )

if __name__ == "__main__":
    main()
