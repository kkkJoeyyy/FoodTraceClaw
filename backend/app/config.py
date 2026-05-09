import os
from pathlib import Path

# Auto-load .env from project root
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                # Strip inline comments
                value = value.split("#")[0].strip().strip('"').strip("'")
                if key.strip() not in os.environ:
                    os.environ[key.strip()] = value

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

VL_MODEL = os.getenv("VL_MODEL", OPENAI_MODEL)

GEOCODE_PROVIDER = os.getenv("GEOCODE_PROVIDER", "osm")
AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")

DB_PATH = os.getenv("DB_PATH", "/app/data/foodtrace.db")
