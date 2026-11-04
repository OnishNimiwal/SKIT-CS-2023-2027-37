# MRPL AI Workbench — User Guide

A practical, task-by-task guide to installing, running and using the Workbench. For the
formal specification (requirements, architecture, diagrams), see
[`../SRS/SRS_MRPL_AI_Workbench.docx`](../SRS/SRS_MRPL_AI_Workbench.docx). For a developer-level
tour of the codebase, see the [repository README](../../README.md).

---

## 1. What this is

MRPL AI Workbench is an **on-premise** AI chat and document assistant: you run it on one
machine on your local network (the project calls this PC5), sign in from a browser, and it
answers questions — either freely, or grounded in documents you upload — using a locally
hosted AI model. Nothing you type, upload, or receive back ever leaves your network.

The repository contains **two versions of the backend**, built in sequence. Pick one to run —
don't run both against the same frontend, they use different database schemas.

| | `backend/` (Phase 1 & 2) | `rag_backend/` (Phase 3) |
|---|---|---|
| Documents it accepts | PDF, TXT only | PDF, DOCX, TXT, MD, XLSX, CSV/TSV, PPTX, images, audio |
| How it answers | Pastes the whole document (up to 50,000 characters) into the prompt | Chunks and embeds the document, retrieves only the relevant passages, and cites them |
| Per-user privacy | Yes — each user only sees their own documents | Not yet enforced — treat as single-user/trusted-team for now |
| Cross-document search | No | Yes — search every uploaded file at once |
| Best for | A straightforward, proven document Q&A tool | Larger document sets, mixed file types, and citation-backed answers |

If you're not sure which to use, start with `backend/` — it's the simpler, more complete path
for a single team.

---

## 2. Before you start

You need three things installed on the machine that will run the Workbench (PC5):

1. **Python 3.10+** and **Node.js** (for the frontend build tools).
2. **[Ollama](https://ollama.com)**, running locally. Pull the two models the Workbench uses:
   ```bash
   ollama pull qwen3:4b             # the chat/answer model
   ollama pull nomic-embed-text     # only needed for rag_backend's search
   ollama serve                     # starts the Ollama daemon on port 11434
   ```
   Leave `ollama serve` running in its own terminal — the Workbench calls it over
   `http://127.0.0.1:11434` and will report "Local AI server is unavailable" if it isn't running.
3. A **modern browser** (Chrome, Edge or Firefox) on every workstation that will use the
   Workbench (PC2, PC3, PC4, …).

No internet connection is required once Ollama's models are downloaded — the whole system runs
offline from that point on.

---

## 3. First-time setup

Run these once, from the repository root.

```bash
# Python environment and dependencies
python -m venv venv
venv\Scripts\activate              # Windows — macOS/Linux: source venv/bin/activate
pip install -r requirements.txt           # if using backend/
# or: pip install -r rag_backend/requirements.txt   # if using rag_backend/

# Environment file
copy .env.example .env             # Windows — macOS/Linux: cp .env.example .env

# Database and admin account
venv\Scripts\python backend\manage.py migrate
venv\Scripts\python backend\manage.py createsuperuser     # choose a username and password — this is your login
```
(Swap `backend\manage.py` for `rag_backend\manage.py` throughout if you're running Phase 3.)

```bash
# Frontend
cd frontend
npm install
```

That's it — the account you create with `createsuperuser` is what you'll sign in with in the
browser. There is no public sign-up page; accounts are created this way or from
`http://<server>:8000/admin/` by whoever administers the Workbench.

---

## 4. Running it day to day

Three things need to be running at once, each in its own terminal:

```bash
# Terminal 1 — the local AI model (leave running)
ollama serve

# Terminal 2 — the Django API
venv\Scripts\python backend\manage.py runserver 0.0.0.0:8000

# Terminal 3 — the web interface
cd frontend
npm run dev -- --host 0.0.0.0
```

Then open the Workbench in a browser:
- **On the server itself (PC5):** `http://localhost:5173`
- **From another machine on the LAN (PC2, PC3, PC4):** `http://<PC5's IP address>:5173`
  — find PC5's IP with `ipconfig` (Windows) or `hostname -I` (Linux).

You'll land on a sign-in page. Use the username/password from `createsuperuser` (or an account
an administrator created for you).

---

## 5. Using the Chat tab

This is a general-purpose chat, not tied to any document — ask it anything the way you would
any AI assistant. Type your message and press **Enter** (or click Send). The header shows
**Deployment: On-Premise** and **External API: Disabled** as a visual reminder that your
conversation stays local.

Each reply has a **copy** button if you want to paste the answer elsewhere.

---

## 6. Using the Document Assistant

This is where you get answers grounded in a specific file rather than the model's general
knowledge.

### Upload a document
1. Open the **Documents** tab.
2. Drag a file onto the upload area, or click to browse for one.
   - `backend/`: only `.pdf` and `.txt` files, and only the first 50,000 characters of text are
     kept — plenty for most reports, but a very large PDF will be truncated.
   - `rag_backend/`: PDF, DOCX, TXT, MD, XLSX, CSV, TSV, PPTX, and (with Tesseract/Whisper
     installed) images and audio.
3. Wait for the upload to finish — the document appears in the list on the left once it's
   processed.

### Ask it a question
Select the document from the list, open its **Q&A** tab, and type your question. The answer is
built only from that document's content.
- `rag_backend/` additionally shows **citations** — numbered references like `[1]` pointing to
  the exact passage used, and a **sources** list of which file(s) the answer drew from.
- If the document genuinely doesn't contain the answer, the system says so rather than
  guessing — it won't fall back to general knowledge.

### Get a summary
Click **Summary** in the document's workspace to generate a structured executive overview —
overview, key points, and conclusions — without having to ask a specific question.

### Export a Word report
Click **Export** / **Generate Report** to download a `.docx` file containing the document's
metadata, the AI summary, and a preview of the extracted text. Useful for sharing a result
outside the Workbench.

### Delete a document
Use the delete control in the document list. This removes both the database record and the
underlying file from disk — it cannot be undone. In `backend/`, you can only delete documents
you uploaded yourself; other users' documents aren't visible to you at all.

---

## 7. Unified search (rag_backend only)

If you're running `rag_backend/`, the **Search** feature looks across *every* ingested
document — PDFs, spreadsheets, slides, images, audio transcripts — in one query, rather than
one document at a time. Each result shows:
- a colour-coded badge for its source format (PDF, CSV, Image (OCR), Audio Transcript, …),
- the matching passage,
- a relevance score.

You can narrow a search to specific formats or specific documents if you only want to search,
say, your spreadsheets.

---

## 8. Signing out / switching users

Use the **sign out** control in the header. Sessions last 8 hours by default
(`SESSION_COOKIE_AGE` in `.env`) before you'll need to sign in again.

---

## 9. Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| "Local AI server is unavailable" on every request | Ollama isn't running, or the wrong model name is configured | Make sure `ollama serve` is running in its own terminal; check `OLLAMA_MODEL` in `.env` matches a model you've pulled (`ollama list`) |
| First reply after a while is very slow, then gets fast | Ollama had unloaded the model from memory | Normal — `OLLAMA_KEEP_ALIVE` (default 30 minutes) keeps it loaded between requests once warmed up |
| Upload rejected with "unsupported file type" | File extension isn't in the allowed list for the backend you're running | Check Section 1's table — `backend/` only takes PDF/TXT; use `rag_backend/` for other formats |
| Can't reach the Workbench from another PC on the LAN | Frontend or backend not bound to the network, or a firewall is blocking it | Make sure you started the frontend with `--host 0.0.0.0` and Django with `0.0.0.0:8000`; check Windows Firewall allows inbound connections on ports 5173 and 8000 |
| "Session expired" / keeps asking to sign in | The 8-hour session cookie lapsed, or cookies are blocked | Sign in again; make sure your browser isn't blocking cookies for the Workbench's address |
| A document you uploaded isn't visible to a colleague (or vice versa) | This is by design in `backend/` — documents are private to their uploader | Have each person upload their own copy, or ask an administrator to share results via the exported Word report instead |

---

## 10. Where your data lives

Everything stays on the server (PC5), in the repository's own folders:
- **Accounts and document metadata** — `db.sqlite3` (SQLite).
- **Uploaded files** — `media/documents/` on disk; not served at a public URL, so a file can
  only be reached through the authenticated API.
- **Search index** (`rag_backend/` only) — `vector_db/` (ChromaDB).

Nothing here is synced anywhere else. Back up these locations yourself if you need to preserve
data across a server move or rebuild.

---

## 11. Optional / advanced modules

Two standalone modules in the repository aren't wired into the main Workbench by default —
they're building blocks a developer can plug in:

- **`OCR_modul/`** — a command-line OCR tool for extracting text from images and scanned PDFs
  (`python -m ocr_module.cli path/to/scan.pdf`). The Document Assistant's own image ingestion
  (`rag_backend/`) already does this automatically on upload; use the CLI directly only if you
  want to OCR a file outside the Workbench.
- **`voice_search/`** — a separate speech-to-text search service (its own server, its own
  `.env`) for transcribing and searching audio recordings. See
  [`voice_search/README.md`](../../voice_search/README.md) to run it on its own.
- **`dashboard-uploads/`** — a feature branch snapshot adding a dashboard-style multimodal
  upload UI; see [`dashboard-uploads/INTEGRATION.md`](../../dashboard-uploads/INTEGRATION.md)
  for how to merge it in.

---

## 12. Frequently asked questions

**Does any of this use the internet or send data to OpenAI/Google/Claude/etc.?**
No. `ALLOW_EXTERNAL_AI` defaults to `False`, and the only AI calls made are to Ollama on
`127.0.0.1` — the same machine. Once Ollama's models are downloaded, the whole system works
with no internet connection at all.

**Can I use a different model than qwen3:4b?**
Yes — pull it with `ollama pull <model>` and set `OLLAMA_MODEL=<model>` in `.env`. Larger
models answer better but respond more slowly and need more memory.

**Why does my question get answered from "general knowledge" instead of my document?**
You're likely on the Chat tab, not the Documents tab — Chat doesn't look at any document.
Open the document, use its own Q&A box.

**Is there a size limit on uploads?**
Yes, 15 MB per file (`FILE_UPLOAD_MAX_MEMORY_SIZE` / `DATA_UPLOAD_MAX_MEMORY_SIZE` in
`backend/config/settings.py`), plus the 50,000-character extraction cap in `backend/` noted
above.

**Who can create new user accounts?**
Only someone with access to the server's command line (`createsuperuser`) or the Django admin
site (`/admin/`) — there's no self-service sign-up, by design.
