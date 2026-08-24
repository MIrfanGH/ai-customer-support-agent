from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url : str
    openai_api_key : str
    embedding_model : str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"

settings = Settings()
