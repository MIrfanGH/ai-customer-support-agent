from app.db.session import SessionLocal
from app.retrieval.vector_store import VectorStore

"""
- To figure out the rigth retrieval threshold for this RAG system.
- The goal is to find a threshold that separates in-scope queries (which should be answered by the LLM) 
  from out-of-scope queries (which should be escalated to a human).
- The script prints the top-k search results for a set of in-scope and out-of-s
"""

IN_SCOPE = [
    "How do I reset my password?",
    "What happens if my payment fails?",
    "How are user roles handled?",
    "How are blog posts cached?",
    "Which subscription plans are available?",
]
OUT_SCOPE = [
    "What is your refund policy?",
    "How do I delete my account?",
    "Can you help me book a flight to Dubai?",
    "What's the weather today?",
]

vs = VectorStore(SessionLocal())
for label, qs in (("IN", IN_SCOPE), ("OUT", OUT_SCOPE)):
    for q in qs:
        top = vs.search(q, top_k=3)[0]
        print(f"{label:3} {top['score']:.3f} {top['source']:<22} {q}")