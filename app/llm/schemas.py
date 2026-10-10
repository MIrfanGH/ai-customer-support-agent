from pydantic import BaseModel


class RAGAnswer(BaseModel):

    answer: str
    sources_used: list[str]
    refused: bool

class AskRequest(BaseModel):
     query : str


class AnswerToolArgs(BaseModel):
    answer : str
    sources_used : list[str]


class EscalateToolArgs(BaseModel):
    reason : str
    summary: str


class AskResponse(BaseModel):
    """
    Response model for the /ask endpoint.
    """
    escalated: bool
    top_score: float
    answer: str | None = None   # Default to None so incase the query was escalated to a human agent 
    sources_used: list[str] | None = None
    ticket_id: int | None = None 
    message: str | None = None