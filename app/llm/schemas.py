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