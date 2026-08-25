from app.retrieval.context import build_context
from app.retrieval.vector_store import VectorStore
from app.db.session import SessionLocal


"""
print top-k (raw search result )  and context to verify which layer is causing the error 
"""

session = SessionLocal()
vs = VectorStore(session)

res = vs.search("Which subscription plans are available?", top_k=5)
print(res)

print("\n\n\n")

context_str = build_context(res)
print(context_str)