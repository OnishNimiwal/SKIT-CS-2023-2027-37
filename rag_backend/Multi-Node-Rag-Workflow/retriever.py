from langchain_chroma import Chroma
from app.config import CHROMA_DIR, embeddings


def get_retriever(k: int = 4):
    store = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    return store.as_retriever(search_kwargs={"k": k})