from app.llm.llm_utils import call_llm_with_retry
from app.llm.prompts import RAG_SYSTEM_PROMPT
from app.llm.schemas import RAGAnswer, AskRequest
from app.retrieval.context import build_context
from app.retrieval.vector_store import VectorStore
from app.db.session import get_db
from fastapi import APIRouter, Depends


router = APIRouter()

@router.post("/ask")
async def ask_query(query: str, top_k=5, db=Depends(get_db)):

    vs = VectorStore(db)
    chunks = vs.search(query, top_k)
    context_str = build_context(chunks)

    user_message = f"Query: {query}\n\n context: {context_str}"

    result = call_llm_with_retry(
        system_prompt=RAG_SYSTEM_PROMPT,
        user_message=user_message,
        schema=RAGAnswer
    )

    return result
