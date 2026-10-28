"""FastAPI backend: record/upload voice, transcribe offline, search what was said."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config, index

app = FastAPI(title="Voice Search", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class SearchIn(BaseModel):
    query: str = Field(min_length=2)
    k: int = Field(default=config.TOP_K, ge=1, le=20)
    doc_id: Optional[str] = None


@app.get("/api/health")
def health():
    return {"status": "ok", "whisper_model": config.WHISPER_MODEL}


@app.post("/api/upload")
def upload(file: UploadFile = File(...)):
    """Accepts an audio file or a browser recording (webm/ogg/mp4)."""
    name = Path(file.filename or "recording.webm").name
    ext = Path(name).suffix.lower()
    if ext not in config.AUDIO_EXT:
        raise HTTPException(400, f"Unsupported type '{ext}'. Allowed: {sorted(config.AUDIO_EXT)}")

    doc_id = index.new_id()
    dest = config.UPLOAD_DIR / f"{doc_id}_{name}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        return index.index_audio(dest, filename=name, doc_id=doc_id)
    except ValueError as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(422, str(e))
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(500, f"Transcription failed: {e}")


@app.get("/api/files")
def files():
    return index.list_files()


@app.get("/api/transcript/{doc_id}")
def transcript(doc_id: str):
    rows = index.get_transcript(doc_id)
    if not rows:
        raise HTTPException(404, "Recording not found")
    return {"doc_id": doc_id, "transcript": rows}


@app.delete("/api/files/{doc_id}")
def delete(doc_id: str):
    removed = index.delete_file(doc_id)
    if not removed:
        raise HTTPException(404, "Recording not found")
    for f in config.UPLOAD_DIR.glob(f"{doc_id}_*"):
        f.unlink(missing_ok=True)
    return {"deleted_chunks": removed}


@app.post("/api/search")
def search(body: SearchIn):
    return {"results": index.search(body.query, k=body.k, doc_id=body.doc_id)}


@app.get("/api/audio/{filename}")
def audio(filename: str):
    """Serve the original audio (supports Range requests so the player can seek)."""
    path = config.UPLOAD_DIR / Path(filename).name
    if not path.is_file():
        raise HTTPException(404, "Not found")
    return FileResponse(path)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")
