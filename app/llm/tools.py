from app.llm.schemas import AnswerToolArgs, EscalateToolArgs


"""
These TOOLS are used to define the functions that the LLM can call. Each tool has a name, description, and parameters.
The parameters are defined using Pydantic models, which automatically generate JSON schemas for validation.
LLM looks at the description to decide which tool to call based on the context and the query.
The LLM is forced to pick exactly one tool (answer_query or escalate_to_human)
"""

ANSWER_TOOL = {
    "type": "function",
    "function": {
        "name": "answer_query",
        "description": "Use when the provided context is sufficient to answer the user's question. "
                        "Answer strictly from the context, never from outside knowledge.",

    "parameters": AnswerToolArgs.model_json_schema(), # parameters: tells the LLM what arguments it must provide when it decides to call this tool.
    },                                                
}                                                     

ESCALATE_TOOL = {
    "type": "function",
    "function": {
        "name": "escalate_to_human",
        "description": "Use when the context does NOT contain enough information to confidently "
                        "answer the question. Do not guess or use outside knowledge.",

    "parameters": EscalateToolArgs.model_json_schema(),
    
    }
}


TOOLS = [ANSWER_TOOL, ESCALATE_TOOL]
