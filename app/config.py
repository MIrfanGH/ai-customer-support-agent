from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    database_url : str
    open_ai_key : str
    embedding_model : str = "text-embedding-3-small"

    class Config:
        env_file = ".env"

settings = Settings()
