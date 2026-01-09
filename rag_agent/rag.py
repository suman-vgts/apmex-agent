from qdrant_client import QdrantClient
from langchain_qdrant import QdrantVectorStore
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

from .utils import (
    QDRANT_URL,
    COLLECTION_NAME,
    get_embeddings,
    get_langchain_llm
)

def build_rag_chain():
    client = QdrantClient(url=QDRANT_URL)

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=get_embeddings()
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}
    )

    prompt = PromptTemplate(
        template="""
            You are a strict Information Retrieval Bot. 

            1. Use the provided context to answer the user's question.
            2. If the answer is not explicitly stated in the context, you MUST say: "I cannot answer this question because the provided documents do not contain the necessary information."
            3. Do NOT use your own knowledge. 
            4. Do NOT say "Based on the documents provided..." just give the answer directly.
            5. Do NOT answer any questions that are unrelated to the context provided.


            Context:
            {context}

            Question:
            {question}

            Answer:
""",
        input_variables=["context", "question"]
    )

    return RetrievalQA.from_chain_type(
        llm=get_langchain_llm(), 
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=False
    )
