"""LangGraph query-processing flow:

START -> condense -> retrieve -> (generate | not_found) -> END
"""

import re
from functools import lru_cache

from django.conf import settings
from langchain_core.messages import AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from .context import fit_chunks_to_budget, trim_history
from .prompts import NOT_FOUND, build_condense_prompt, build_system_prompt
from .retrieval import retrieve_chunks

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_think(text: str) -> str:
    """Remove Qwen3-style <think>...</think> reasoning blocks."""
    return _THINK_RE.sub("", text).strip()


class RAGState(MessagesState):
    doc_ids: list[str]
    question: str
    chunks: list[dict]
    sources: list[str]
    citations: list[dict]


@lru_cache(maxsize=1)
def get_llm() -> ChatOllama:
    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_URL,   # local Ollama only
        temperature=0.2,
        client_kwargs={"timeout": 120},
    )


def condense_node(state: RAGState):
    """Rewrite follow-up questions into standalone ones."""
    msgs = state["messages"]
    question = msgs[-1].content
    if len(msgs) < 3:  # first turn, nothing to resolve
        return {"question": question}
    history = trim_history(msgs[:-1], max_messages=6, max_chars=2000)
    rewritten = strip_think(
        get_llm().invoke(build_condense_prompt(history, question)).content
    )
    return {"question": rewritten or question}


def retrieve_node(state: RAGState):
    """Retrieve relevant chunks and fit them to the context budget."""
    try:
        chunks = retrieve_chunks(state["question"], state.get("doc_ids") or None)
    except Exception:
        chunks = []  # chat still responds if the vector DB is empty/unavailable
    chunks = fit_chunks_to_budget(chunks)
    return {
        "chunks": chunks,
        "sources": sorted({c["source"] for c in chunks}),
        "citations": [
            {
                "index": i,
                "source": c["source"],
                "chunk": c["chunk"],
                "score": c["score"],
                "snippet": c["text"][:200],
            }
            for i, c in enumerate(chunks, start=1)
        ],
    }


def route(state: RAGState) -> str:
    return "generate" if state["chunks"] else "not_found"


def generate_node(state: RAGState):
    """Build the prompt from retrieved chunks and recent history, then answer."""
    history = trim_history(state["messages"])
    system = SystemMessage(build_system_prompt(state["chunks"]))
    reply = get_llm().invoke([system, *history])
    return {"messages": [AIMessage(strip_think(reply.content))]}


def not_found_node(state: RAGState):
    return {"messages": [AIMessage(NOT_FOUND)], "sources": [], "citations": []}


@lru_cache(maxsize=1)
def get_graph():
    b = StateGraph(RAGState)
    b.add_node("condense", condense_node)
    b.add_node("retrieve", retrieve_node)
    b.add_node("generate", generate_node)
    b.add_node("not_found", not_found_node)

    b.add_edge(START, "condense")
    b.add_edge("condense", "retrieve")
    b.add_conditional_edges(
        "retrieve", route, {"generate": "generate", "not_found": "not_found"}
    )
    b.add_edge("generate", END)
    b.add_edge("not_found", END)

    # In-memory checkpointer: works offline, per process.
    return b.compile(checkpointer=MemorySaver())