"""LangGraph query-processing flow:

START -> condense -> retrieve -> (generate | not_found) -> END
"""

import re
from functools import lru_cache

from django.conf import settings
from langchain_core.messages import AIMessage, SystemMessage, trim_messages
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from .rag import retrieve

GENERATE_PROMPT = (
    "You are an on-premise assistant that answers questions about the user's uploaded documents.\n"
    "Use ONLY the context below. If the answer is not in the context, say you could not find it.\n"
    "Be concise.\n\nCONTEXT:\n{context}"
)

CONDENSE_PROMPT = (
    "Given the conversation and a follow-up question, rewrite the follow-up as a standalone "
    "question that can be understood without the conversation. Return ONLY the question.\n\n"
    "Conversation:\n{history}\n\nFollow-up: {question}\n\nStandalone question:"
)

NOT_FOUND = "I couldn't find anything relevant to that in your uploaded documents."

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def strip_think(text: str) -> str:
    """Remove Qwen3-style <think>...</think> reasoning blocks."""
    return _THINK_RE.sub("", text).strip()


class RAGState(MessagesState):
    doc_ids: list[str]
    question: str
    context: str
    sources: list[str]


@lru_cache(maxsize=1)
def get_llm() -> ChatOllama:
    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_URL,
        temperature=0.2,
        client_kwargs={"timeout": 120},
    )


def condense_node(state: RAGState):
    """Rewrite follow-up questions into standalone ones."""
    msgs = state["messages"]
    question = msgs[-1].content
    if len(msgs) < 3:  # first turn, nothing to resolve
        return {"question": question}
    recent = msgs[:-1][-6:]
    history = "\n".join(
        f"{'User' if m.type == 'human' else 'Assistant'}: {m.content}" for m in recent
    )
    rewritten = strip_think(
        get_llm().invoke(CONDENSE_PROMPT.format(history=history, question=question)).content
    )
    return {"question": rewritten or question}


def retrieve_node(state: RAGState):
    try:
        docs = retrieve(state["question"], state.get("doc_ids") or None)
    except Exception:
        docs = []  # chat still responds if the vector DB is empty/unavailable
    return {
        "context": "\n\n---\n\n".join(d.page_content for d in docs),
        "sources": sorted({d.metadata.get("source", "unknown") for d in docs}),
    }


def route(state: RAGState) -> str:
    return "generate" if state["context"] else "not_found"


def generate_node(state: RAGState):
    history = trim_messages(
        state["messages"],
        strategy="last",
        max_tokens=10,
        token_counter=len,      # count messages; no tokenizer download needed offline
        start_on="human",
        include_system=False,
    )
    system = SystemMessage(GENERATE_PROMPT.format(context=state["context"]))
    reply = get_llm().invoke([system, *history])
    return {"messages": [AIMessage(strip_think(reply.content))]}


def not_found_node(state: RAGState):
    return {"messages": [AIMessage(NOT_FOUND)], "sources": []}


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

    return b.compile(checkpointer=MemorySaver())