"""Runs without internet or model downloads: Whisper and embeddings are replaced by fakes,
so this tests the pipeline logic (grouping, indexing, search, timestamps, API, audio seeking)."""
import wave

import pytest
from fastapi.testclient import TestClient
from langchain_chroma import Chroma
from langchain_core.embeddings import DeterministicFakeEmbedding

from app import index, stt
from app.main import app

FAKE = stt.Transcript(
    language="en",
    duration=75.0,
    segments=[
        stt.Segment(0.0, 10.0, "Welcome everyone to the project review."),
        stt.Segment(10.0, 22.0, "The submission deadline is the fifteenth of March."),
        stt.Segment(22.0, 40.0, "The budget for hardware is fifty thousand rupees."),
        stt.Segment(40.0, 75.0, "Next meeting will be held on Friday morning."),
    ],
)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    index.set_store(Chroma(
        collection_name="testcol",
        embedding_function=DeterministicFakeEmbedding(size=64),
        persist_directory=str(tmp_path / "chroma"),
        collection_metadata={"hnsw:space": "cosine"},
    ))
    monkeypatch.setattr(stt, "transcribe", lambda path: FAKE)
    return TestClient(app)


def make_wav(path, seconds=2):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 16000 * seconds)


def test_grouping_keeps_timestamps():
    chunks = index.group_segments(FAKE.segments)
    assert chunks[0]["start"] == 0.0 and chunks[-1]["end"] == 75.0
    assert all(c["end"] > c["start"] for c in chunks)
    assert "deadline" in " ".join(c["text"] for c in chunks)


def test_upload_search_transcript_delete(client, tmp_path):
    make_wav(tmp_path / "meeting.wav")
    r = client.post("/api/upload", files={"file": ("meeting.wav", open(tmp_path / "meeting.wav", "rb"))})
    assert r.status_code == 200
    body = r.json()
    assert body["chunks"] >= 1 and body["language"] == "en"
    doc_id = body["doc_id"]

    hits = client.post("/api/search", json={"query": "deadline"}).json()["results"]
    assert hits and hits[0]["filename"] == "meeting.wav"
    assert {"start", "end", "text", "file"} <= hits[0].keys()

    # audio can be fetched, and a Range request (what seeking uses) works
    audio = client.get("/api/audio/" + hits[0]["file"], headers={"Range": "bytes=0-99"})
    assert audio.status_code == 206 and len(audio.content) == 100

    t = client.get(f"/api/transcript/{doc_id}").json()["transcript"]
    assert t[0]["start"] == 0.0 and [c["start"] for c in t] == sorted(c["start"] for c in t)

    assert client.delete(f"/api/files/{doc_id}").status_code == 200
    assert client.get("/api/files").json() == []


def test_empty_speech_rejected(client, tmp_path, monkeypatch):
    monkeypatch.setattr(stt, "transcribe", lambda p: stt.Transcript("en", 3.0, []))
    make_wav(tmp_path / "silent.wav")
    r = client.post("/api/upload", files={"file": ("silent.wav", open(tmp_path / "silent.wav", "rb"))})
    assert r.status_code == 422


def test_rejects_bad_type(client):
    assert client.post("/api/upload", files={"file": ("x.exe", b"abc")}).status_code == 400
