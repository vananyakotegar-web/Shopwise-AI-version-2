import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env", override=True)
load_dotenv()

CANONICAL_DB_FILE = (BASE_DIR / "shopwise.db").resolve()
DEFAULT_DB = f"sqlite:///{CANONICAL_DB_FILE.as_posix()}"

raw_db_url = os.getenv("DATABASE_URL", "").strip()
if not raw_db_url or raw_db_url in ("sqlite:///./shopwise.db", "sqlite:///shopwise.db"):
    DATABASE_URL = DEFAULT_DB
elif raw_db_url.startswith("sqlite:///./"):
    rel_path = raw_db_url[len("sqlite:///./"):]
    DATABASE_URL = f"sqlite:///{(BASE_DIR / rel_path).resolve().as_posix()}"
else:
    DATABASE_URL = raw_db_url

JWT_SECRET = os.getenv("JWT_SECRET", "shopwise-v3-secret-key-2026")
JWT_HOURS = int(os.getenv("JWT_HOURS", "24"))

# Gemini API & AI Assistant Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta")

# Anthropic Claude (alternative LLM fallback)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

# SerpAPI Google Shopping Key & Endpoint
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
SERPAPI_API_BASE = os.getenv("SERPAPI_API_BASE", "https://serpapi.com/search.json")

# CORS
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175,http://localhost:5176,http://127.0.0.1:5176,http://localhost:5177,http://127.0.0.1:5177,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origin.strip()
]
