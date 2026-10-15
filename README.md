# SKIT-CS-2023-2027-37
## How retrieval, prompting and context work

1. **Retrieval** (`chat/retrieval.py`): the question is embedded and the top candidates are
   fetched from Chroma, filtered by `RAG_MIN_SCORE`, de-duplicated and capped at `RAG_TOP_K`.
2. **Context management** (`chat/context.py`): chunks are fitted into `RAG_MAX_CONTEXT_CHARS`
   and chat history is trimmed to `RAG_HISTORY_MESSAGES` / `RAG_HISTORY_CHARS`.
3. **Prompt construction** (`chat/prompts.py`): passages are numbered `[1]`, `[2]` and the model
   is told to answer only from them and cite them.

The `/api/chat/` response includes `citations` (index, source, chunk, score, snippet).