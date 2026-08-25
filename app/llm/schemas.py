from pydantic import BaseModel


class RAGAnswer(BaseModel):

    answer: str
    sources_used: list[str]
    refused: bool

class AskRequest(BaseModel):
     query : str