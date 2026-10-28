from typing import List, TypedDict
from langchain_core.documents import Document


class RAGState(TypedDict):
    question: str            # original user question
    search_query: str        # rewritten query used for retrieval
    documents: List[Document]
    generation: str
    retries: int