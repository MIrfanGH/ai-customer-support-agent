from openai import OpenAI
from app.config import settings

# This file is used to instantiate the OpenAI client with the API key from the settings. 
# Keeps the client instantiation separate from the rest of the code, making it easier to manage and test.
client = OpenAI(api_key=settings.openai_api_key)