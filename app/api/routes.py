from app.db.session import get_db
from fastapi import APIRouter, Depends
from app.answering.service import answer_or_escalate
from app.llm.schemas import AskResponse, AskRequest


router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask_query(req: AskRequest, db=Depends(get_db)):
    """Answer a support question from the docs, or escalate it to a human ticket."""
    return answer_or_escalate(query=req.query, top_k=req.top_k, db=db)


    
