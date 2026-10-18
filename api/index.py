import os
import sys
from pathlib import Path

# Add project root to sys.path so 'backend.*' imports succeed on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Signal Vercel environment for /tmp paths
os.environ["VERCEL"] = "1"

from backend.main import app
from backend.database import init_db
from backend.seed_data import seed_sample_data

# Ensure tables and demo data are initialized on serverless cold starts
try:
    init_db()
    seed_sample_data()
except Exception as e:
    print(f"Vercel cold start initialization note: {e}")
