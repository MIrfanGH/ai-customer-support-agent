from openai import OpenAI
import json
from app.config import settings
from pydantic import BaseModel, ValidationError
from app.llm.schemas import AnswerToolArgs, EscalateToolArgs



def call_llm_with_tools(client, system_prompt: str, user_message: str, tools, max_retries: int = 3) -> tuple[str, object]:
    """
    Force the LLM to pick exactly one tool (answer_query or escalate_to_human) and
    return its name and validated arguments
    On a malformed or missing tool call (no tool_calls, bad JSON, failed Pydantic
    validation), appends an error-feedback message and retries.

    Args:
        client: instantiated OpenAI/Anthropic client.
        system_prompt: instructs the model when to pick each tool (see RAG_TOOLS_SYSTEM_PROMPT).
        user_message: query + retrieved context, already assembled by build_context().
        tools: list of tool definitions

    Returns:
        tool_name, validated_args

    Raises:
        ValueError: if no valid tool call is produced after MAX_RETRIES attempts.
    """


    last_error = str()
    messages = [
        { "role": "system", "content": system_prompt},
        { "role": "user", "content": user_message},
    ]  

    for _ in range(max_retries):

        response = client.chat.completions.create(
            model = settings.llm_model,
            messages = messages,
            tools = tools,
            tool_choice = "required",
            parallel_tool_calls=False, # Disabled parallel tool calls to allow only one tool call at a time for clear query vs. human escalation
            temperature=0.0,  # prevent randomness in the model's output, ensuring consistent tool selection and argument generation
        )

        message = response.choices[0].message
        tool_calls = message.tool_calls # tool_calls: is a list of tool calls made by the model in this message.It can be empty if the model didn't call any tools.

        if not tool_calls:
            messages.append({       # we append a user message to the conversation history, telling the model that it must call one of the provided tools.
                "role": "user",     # This feedback is intended to guide the model to make a valid tool call in the next attempt.
                  "content": "You must call one of the provided tools"
                })
            continue

        messages.append(message) 
        call = tool_calls[0]  

        try:
            args_dict = json.loads(call.function.arguments)
            if call.function.name == "answer_query":
                validated = AnswerToolArgs.model_validate(args_dict)
            elif call.function.name == "escalate_to_human":
                validated = EscalateToolArgs.model_validate(args_dict)
            else:
                raise ValueError(f"Unknown tool name: {call.function.name}")
            
            return call.function.name, validated  # Returns the tool name selected by the LLM and its arguments,
                                                    # after the arguments are validated against the corresponding Pydantic schema.
            

        except Exception as e:
            # Report the failure as a TOOL result tied to that specific call,
            # not as a fabricated user message. so that the model can see the error in context and correct it in the next attempt.
            last_error = str(e)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": f"Error: {e}. Please call a valid tool with corrected arguments.",
            })
            continue # continue ensures that the loop will retry calling the LLM with the updated messages, and not break out of the loop until a valid tool call is made or max_retries is reached.

    raise ValueError(f"LLM failed to produce a valid tool call after {max_retries} attempts: {last_error}")




def call_llm_with_retry(client, system_prompt: str, user_message: str, schema: type[BaseModel] | None=None,  max_retries:int = 3):

    """
    When there is no tool call, we can use this function to call the LLM and validate its output against a Pydantic schema. 
    If the output is invalid, we provide feedback to the model and retry up to max_retries times.
    """
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
