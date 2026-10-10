from app.llm.llm_utils import call_llm_with_tools
from app.retrieval.context import build_context
from app.retrieval.vector_store import VectorStore
from app.db.session import get_db
from fastapi import APIRouter, Depends
from app.config import settings
from app.ticket.service import create_ticket
from app.llm.client import client
from app.llm.prompts import RAG_TOOLS_SYSTEM_PROMPT
from app.llm.schemas import AskResponse
from app.llm.tools import TOOLS
from app.llm.messages import ESCALATION_MESSAGE, LOW_RETRIEVAL_MESSAGE, ANSWER_QUERY_MESSAGE

router = APIRouter()

@router.post("/ask", response_model=AskResponse)
async def ask_query(query: str, top_k: int=5,db=Depends(get_db)):

    vs = VectorStore(db)
    chunks = vs.search(query, top_k=top_k)

    top_score = chunks[0]["score"] if chunks else 0.0

    # Gate 1 — deterministic, pre-LLM , if the retrieval confidence is too low, we escalate to a human and create a ticket
    if not chunks or top_score < settings.retrieval_threshold:
        ticket = create_ticket(session=db, query=query, reason= "low retrieval confidence")

        return AskResponse(
            escalated=True,
            top_score=round(top_score, 3),
            ticket_id=ticket.id,
            message=LOW_RETRIEVAL_MESSAGE.format(ticket_id=ticket.id)
        )

    context_str = build_context(chunks)
    user_message = f"Query: {query}\n\n context: {context_str}"

    # This is where the LLM is called to decide whether to answer the query or escalate to a human. 
    # The LLM is forced to pick exactly one tool (answer_query or escalate_to_human) and return its name and validated arguments. 
    # If the LLM fails to call a tool, retry up to max_retries times.
    name, args = call_llm_with_tools(
        client = client,
        system_prompt = RAG_TOOLS_SYSTEM_PROMPT,
        user_message = user_message,
        tools = TOOLS,
    )

    # Gate 2 — LLM decision, if the LLM decides to escalate to a human, we create a ticket with the reason and summary provided by the LLM
    if name == "escalate_to_human":
        ticket = create_ticket(
            session= db,
            query=query, 
            reason= args.reason,
            summary= args.summary,
            retrieved_sources = [chunk["source"] for chunk in chunks],
        )
        return AskResponse(
            escalated=True,
            top_score=round(top_score, 3),
            ticket_id=ticket.id,
            answer=args.summary,
            message=ESCALATION_MESSAGE.format(ticket_id=ticket.id)
        )

    # name == "answer_query"
    return AskResponse(
        escalated=False,
        top_score=round(top_score, 3),
        answer=args.answer,
        sources_used=args.sources_used,
        message=ANSWER_QUERY_MESSAGE
    )


    
