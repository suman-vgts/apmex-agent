from google.adk.agents import Agent
import os
from .rag import build_rag_chain

rag_chain = build_rag_chain()

def rag_tool(question: str) -> dict:
    result = rag_chain.invoke(question)
    return {
        "status": "success",
        "answer": result["result"]
    }

root_agent = Agent(
    name="root_agent",
    model=os.getenv("MODEL_NAME"),
    description="Document-based RAG assistant",
    instruction="""
        Use this tool to answer questions strictly from the ingested documents.
        If the question requires document-based knowledge, call this tool.
""",
    tools=[rag_tool],
)
