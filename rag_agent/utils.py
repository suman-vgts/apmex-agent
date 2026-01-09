import os
from dotenv import load_dotenv
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import (
    GoogleGenerativeAIEmbeddings,
    ChatGoogleGenerativeAI
)
load_dotenv()

DATA_DIR = os.getenv("DATA_DIR")
QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
MODEL_NAME = os.getenv("MODEL_NAME")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")


# -------------------------
# Text splitter
# -------------------------
def get_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

# -------------------------
# Embeddings
# -------------------------
def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL
    )

# -------------------------
# LangChain LLM (REQUIRED)
# -------------------------
def get_langchain_llm():
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=0.2,
    )
