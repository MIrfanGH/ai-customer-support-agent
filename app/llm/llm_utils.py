from pydantic import BaseModel, ValidationError
from openai import OpenAI
import os
import json
from app.config import settings



client = OpenAI(api_key=settings.openai_api_key)


def call_llm_with_retry(system_prompt: str, user_message: str, schema: type[BaseModel] | None=None,  max_retries = 3):

    messages = [
        { "role": "system", "content": system_prompt},
        { "role": "user", "content": user_message},
    ]    

    for attempt in range(max_retries):
        # LLM call 
        response = client.chat.completions.create(
            model = settings.llm_model,
            messages= messages,
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        try:
            parsed = json.loads(raw)

            # Validation Check
            validated = schema.model_validate(parsed)
            return validated
        
        except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON: {e}"
    
        except ValidationError as e:
                error_msg = f"Schema validation failed:\n{e}"

        # Retry Logic wuith feedback
        print(f"Attempt {attempt + 1} failed: {error_msg}")
        print("Retrying with feedback to the model...\n")

        messages.append({"role": "assistant", "content": raw})  # Providing the model with its previous output for context
        messages.append({"role": "user", "content": f"Your response had errors:\n{error_msg}\n\n. Please correct the output to match the required format and constraints."})


    raise ValueError(f"Failed after {max_retries} attempts. Last error: {error_msg}")
