import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

CHROMA_DIR = "chroma_db"
DATA_DIR = "data"
MAX_RETRIES = 2

llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")