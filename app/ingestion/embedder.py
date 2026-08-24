from openai import OpenAI
from app.config import settings



client = OpenAI(api_key=settings.openai_api_key)


def get_embedding(text: list[str]):
    response = client.embeddings.create(
            input=text,
            model=settings.embedding_model,
      )
    return [d.embedding for d in response.data]  # return lsit of vectors, 1 vector for each text input 
 