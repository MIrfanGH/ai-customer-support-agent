from pydantic import BaseModel, Field


class RAGAnswer(BaseModel):

    answer: str
    sources_used: list[str]
    refused: bool


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20) # the number 5 is a reasonable default for top_k, but we allow the user to specify a different value between 1 and 20.


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