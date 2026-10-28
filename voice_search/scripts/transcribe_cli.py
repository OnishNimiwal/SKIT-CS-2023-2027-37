"""Check speech-to-text alone, without the server:  python scripts/transcribe_cli.py recording.mp3"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pathlib import Path  # noqa: E402

from app import stt  # noqa: E402

t = stt.transcribe(Path(sys.argv[1]))
print(f"language={t.language} duration={t.duration}s")
for s in t.segments:
    print(f"[{s.start:7.2f} -> {s.end:7.2f}] {s.text}")
