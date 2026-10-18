import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent

if os.getenv("VERCEL"):
    _upload_env = os.getenv("UPLOAD_DIR", "/tmp/uploads")
    _data_env = os.getenv("DATA_DIR", "/tmp/data")
else:
    _upload_env = os.getenv("UPLOAD_DIR", "uploads")
    _data_env = os.getenv("DATA_DIR", "data")

UPLOAD_DIR = Path(_upload_env) if Path(_upload_env).is_absolute() else (BASE_DIR / _upload_env)
DATA_DIR = Path(_data_env) if Path(_data_env).is_absolute() else (BASE_DIR / _data_env)

DB_PATH = DATA_DIR / os.getenv("DATABASE_NAME", "solobiz.db")

# Ensure required directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Server Host & Port (Render/Railway/Heroku inject PORT)
APP_HOST = os.getenv("APP_HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1")
APP_PORT = int(os.getenv("PORT", os.getenv("APP_PORT", "8000")))

# AI Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "45.0"))

# File Upload Settings
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "15"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
}

# App Info
APP_NAME = "SoloBiz AI"
APP_VERSION = "1.0.0"
