"""Speech-to-text with faster-whisper, running fully on this machine."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List

from . import config


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    language: str
    duration: float
    segments: List[Segment]


_model = None
_lock = threading.Lock()  # one transcription at a time; the model is not meant for parallel calls


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(
            config.WHISPER_MODEL,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
    return _model


def transcribe(path: Path) -> Transcript:
    """Return timestamped segments. Silence is skipped by the built-in voice-activity filter."""
    with _lock:
        segments_iter, info = _get_model().transcribe(
            str(path),
            language=config.WHISPER_LANGUAGE,
            task=config.WHISPER_TASK,
            vad_filter=True,
            beam_size=5,
        )
        segments = [
            Segment(round(s.start, 2), round(s.end, 2), s.text.strip())
            for s in segments_iter
            if s.text.strip()
        ]
    return Transcript(language=info.language, duration=round(info.duration, 1), segments=segments)
