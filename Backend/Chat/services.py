from langchain_core.messages import HumanMessage

from .graph import get_graph


def ask_ollama(
    message: str,
    thread_id: str = "default",
    doc_ids: list[str] | None = None,
) -> dict:
    """
    Runs the question through the LangGraph RAG workflow.
    Strictly uses the local on-premise Ollama instance without external AI fallback.
    """
    result = get_graph().invoke(
        {"messages": [HumanMessage(message)], "doc_ids": doc_ids or []},
        config={"configurable": {"thread_id": thread_id}},
    )
    return {
        "answer": result["messages"][-1].content,
        "sources": result.get("sources", []),
    }