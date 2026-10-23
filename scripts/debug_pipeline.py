from app.retrieval.context import build_context
from app.retrieval.vector_store import VectorStore
from app.db.session import SessionLocal
import json
from app.llm.llm_utils import call_llm_with_tools
from app.llm.prompts import RAG_TOOLS_SYSTEM_PROMPT
from app.llm.tools import TOOLS
from app.llm.client import client

"""
A quick debuggin scripts to pin point which layer is responsible for for certain error.
"""

session = SessionLocal()
vs = VectorStore(session)

q = str(input("Query: "))
top_k = vs.search(q, top_k=5)
top_score = top_k[0]["score"]

context_str = build_context(top_k)

user_message = f"Query: {q} \n\n Context: {context_str}"

tool_name, tool_args = call_llm_with_tools(
    client=client,
    system_prompt=RAG_TOOLS_SYSTEM_PROMPT,
    user_message=user_message,
    tools=TOOLS,
    max_retries=3
)

# Print the results
print("top score: ",top_score)
print("tool name: ", tool_name)
print("tool args: ", tool_args)
print(json.dumps(top_k, indent=2, ensure_ascii=False))
print("Context : ", "\n\n\n")
print(context_str)
