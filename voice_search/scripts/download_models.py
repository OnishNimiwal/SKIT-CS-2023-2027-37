"""Run ONCE with internet to cache the models. After that everything works offline.

    python scripts/download_models.py
"""
import os

os.environ["HF_HUB_OFFLINE"] = "0"
os.environ["TRANSFORMERS_OFFLINE"] = "0"

from dotenv import load_dotenv  # noqa: E402

load_dotenv()
emb = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
whisper = os.getenv("WHISPER_MODEL", "small")

print("Downloading embedding model:", emb)
from sentence_transformers import SentenceTransformer  # noqa: E402

SentenceTransformer(emb)

print("Downloading Whisper model:", whisper)
from faster_whisper import WhisperModel  # noqa: E402

WhisperModel(whisper, device="cpu", compute_type="int8")
print("Done.")
