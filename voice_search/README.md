# Voice Search (Offline Speech-to-Text + Semantic Search)

Part of the Offline Multimodal RAG final year project: **record or upload voice, convert it to text on this
machine, and search what was said** (with a jump to that moment in the audio). No internet needed at runtime.

```
mic recording / audio file --> faster-whisper (speech-to-text, timestamped segments)
                                  --> group into ~30 s chunks --> embeddings --> Chroma (local disk)
search query --> embed --> top-k similar chunks --> text + start/end time + audio player at that moment
```

* **Speech-to-text:** faster-whisper (Whisper models run locally). Silence is skipped (voice-activity filter), language is auto-detected, English/Hindi/etc. supported. Set `WHISPER_TASK=translate` to turn any language into English text.
* **Recording:** the web page records from the microphone (MediaRecorder) and uploads the clip. Browsers allow the mic on `localhost` or `https` only.
* **Formats:** mp3, wav, m4a, flac, ogg, opus, aac, wma, webm, mp4. Decoding is bundled, so ffmpeg is not required.
* **Search:** sentence-transformer embeddings + ChromaDB. Each result has the text, start and end time, and a player that starts at that time.

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate            # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
python scripts/download_models.py # once, needs internet: caches Whisper + embedding models
uvicorn app.main:app --reload
```
Open http://localhost:8000. API docs at http://localhost:8000/docs.

Check speech-to-text alone: `python scripts/transcribe_cli.py sample.mp3`

## Choosing a Whisper model (`WHISPER_MODEL` in `.env`)
| Model | Speed on CPU | Accuracy |
|---|---|---|
| tiny / base | fastest | fine for clear English |
| small (default) | good balance | good |
| medium / large-v3 | slow without a GPU | best, better for Hindi and noisy audio |

On an NVIDIA GPU set `WHISPER_DEVICE=cuda` and `WHISPER_COMPUTE_TYPE=float16`.

**Hindi or mixed-language speech:** also change `EMBEDDING_MODEL` to a multilingual one such as
`intfloat/multilingual-e5-small`, otherwise the English-only embeddings will match poorly. Delete `data/chroma` after changing it.

## API
| Method | Path | Purpose |
|---|---|---|
| POST | `/api/upload` | multipart `file` (audio or browser recording): transcribe + index |
| POST | `/api/search` | `{"query": "...", "k": 5, "doc_id": null}` returns chunks with `start`, `end`, `text`, `file` |
| GET | `/api/transcript/{doc_id}` | full transcript in time order |
| GET | `/api/files` | list recordings |
| DELETE | `/api/files/{doc_id}` | remove a recording and its vectors |
| GET | `/api/audio/{file}` | original audio (Range requests for seeking) |

## Plugging into the full project
`app.index.search(query, k)` returns the top chunks as dictionaries, so your LangChain chain can pass their
text to the local LLM and cite `filename @ mm:ss`.

## Tests
```bash
pytest -q    # no internet, GPU or model download needed (Whisper and embeddings are faked)
```
