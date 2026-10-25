from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from app.config import CHROMA_DIR, DATA_DIR, embeddings


def ingest():
    loader = DirectoryLoader(DATA_DIR, glob="**/*.txt", loader_cls=TextLoader)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_documents(docs)
    Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_DIR)
    print(f"Ingested {len(chunks)} chunks from {len(docs)} files.")


if __name__ == "__main__":
    ingest()