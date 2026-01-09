import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from langchain_community.document_loaders import PyPDFLoader

from langchain_qdrant import QdrantVectorStore
from dotenv import load_dotenv

from utils import (DATA_DIR, QDRANT_URL, COLLECTION_NAME, get_text_splitter,get_embeddings)
load_dotenv()

def ingest_data():
    documents = []
    for file in os.listdir(DATA_DIR):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(DATA_DIR, file))
            documents.extend(loader.load())

    splitter = get_text_splitter()
    docs = splitter.split_documents(documents)

    client = QdrantClient(url=QDRANT_URL)

    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=768,
            distance=Distance.COSINE
        )
    )

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=get_embeddings()
    )

    vectorstore.add_documents(docs)

    print(f"✅ Ingested {len(docs)} chunks")

if __name__ == "__main__":
    ingest_data()
