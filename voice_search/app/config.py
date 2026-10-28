"""Settings, read from environment variables / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "voice_search")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "").strip() or None
WHISPER_TASK = os.getenv("WHISPER_TASK", "transcribe").strip()

CHUNK_SECONDS = float(os.getenv("CHUNK_SECONDS", "30"))
CHUNK_MAX_CHARS = int(os.getenv("CHUNK_MAX_CHARS", "700"))
TOP_K = int(os.getenv("TOP_K", "5"))

if OFFLINE_MODE:  # must be set before huggingface is imported
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

AUDIO_EXT = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".opus", ".aac", ".wma", ".webm", ".mp4"}
