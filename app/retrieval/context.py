from pathlib import Path
import tiktoken


ENCODING = tiktoken.get_encoding("cl100k_base")


def build_context(chunks: list[dict], max_tokens=1000) -> str: 
    """
    Build a token-bounded context from retrieved chunks for the LLM.

    Each chunk's source and metadata are converted into a readable label
    so the model can associate the provided content with its source.
    Chunks are added until the maximum token budget is reached.
    """

    pieces = []
    current_c_token = 0


    for chunk in chunks:

        label = f"[Source: {Path(chunk["source"]).name} ]"
        labeled_chunk = f"lable: {label}\n {chunk["content"]}"

        chunk_length = len(ENCODING.encode(labeled_chunk))

        if current_c_token + chunk_length >= max_tokens:
            break

        pieces.append(labeled_chunk)
        current_c_token += chunk_length

    return "\n\n--\n\n".join(pieces)


