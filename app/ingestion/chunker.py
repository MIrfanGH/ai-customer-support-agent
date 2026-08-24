
import tiktoken

"""
added metadata chunk level so each chunk remains self-contained 
(text + source + metadata + chunk_index).

"""

ENCODING = tiktoken.get_encoding("cl100k_base") # will give token count of provided text, and also encode/decode to/from tokens


def text_splitter(text, source, separator:list, chunk_size, metadata=None):

    """
    Goal: Prevent oversized chunks, thus guarantee safety (no chunk > limit).

    Recursively split text into token‑bounded chunks using a hierarchy of separators.
    Ensures each chunk fits within the specified chunk_size limit.
    """

    sep = separator[0]
    chunks = []
   
       
    if sep == "": # if "no separator left" — force-split by tokens
        tokens = ENCODING.encode(text)
        for start in range(0, len(tokens), chunk_size):
            chunks.append({
                "text": ENCODING.decode(tokens[start:start + chunk_size]),
                "strategy": "recursive",
                "source": source,
                "chunk_index": len(chunks), # taking the length of the chunks list as the chunk_index because it is unique for each chunk and can be sued as a dedup key for re-ingestion,
                "metadata": metadata or {}
            })
        return chunks
    
    text_list = text.split(sep) 

    # if sep is not empty, we can split by the separator and check the length of each piece
    for piece in text_list:
        if len(ENCODING.encode(piece)) <= chunk_size:
            chunks.append({
                "text": piece,
                "strategy": "recursive",
                "source": source,
                "chunk_index": len(chunks), # taking the length of the piece in tokens as the chunk_index because it is unique for each chunk and can be sued as a dedup key for re-ingestion
                "metadata": metadata or {}
            })
        else:           
            # recursively call the function with the next separato
            chunks.extend(text_splitter(piece, source, separator[1:], chunk_size, metadata))

    return chunks # it will contain all the chunks from the recursive calls and the chunks that were small enough to be added directly



def chunk_merger(chunks, source, chunk_size, overlap, metadata=None):
    
    """
    Goal: Avoid too many tiny chunks, guarantees efficiency (chunks aren’t too small, context preserved).

    Greedily accumulate pieces into a buffer until adding the next one
    would exceed chunk_size, then flush. Carry back `overlap` tokens.
    Merges the chunks into larger chunks of a specified size with optional overlap.
    """

    merged_chunks = [] # list of meged chunks, each entry/chunk is group of smaller chunks so that, merged-chunk <= token_size
                       #  1 dict = 1 chunk + its metadata
    buffer_tokens = []

    def flush():  # Purpose: Commit whatever is in buffer_tokens into merged_chunks
        if buffer_tokens:
            merged_chunks.append({
                "text": ENCODING.decode(buffer_tokens),
                "strategy": "merged",
                "source": source,
                "chunk_index": len(merged_chunks),  # taking the length of the merged list as the chunk_index because it is unique for each chunk and can be sued as a dedup key for re-ingestion
                "metadata": metadata or {}
            })

    for chunk in chunks:
        piece_tokens = ENCODING.encode(chunk['text'] + '\n')  # Add a newline to separate pieces when merging for better readability

        if buffer_tokens and len(buffer_tokens) + len(piece_tokens) > chunk_size: # means the current buffer is full and adding the next piece would exceed the chunk_size
            flush() # whatever is in the buffer at this point is a chunk(single or group of pieces), flush it to the merged list and start a new buffer with the current piece
            buffer_tokens = buffer_tokens[-overlap:] if overlap > 0 else []  # carry back `overlap` tokens 
        
        buffer_tokens += piece_tokens  # add the current piece to the buffer
    
    flush()  # flush any remaining tokens in the buffer after the loop ends so last chunk is not lost
    return merged_chunks


def recursive_chunker(text, source, separator:list, chunk_size, overlap, metadata):
     chunks = text_splitter(text, source, separator, chunk_size - overlap, metadata) # subtracting overlap from chunk_size to ensure that the final merged chunks do not exceed the specified chunk_size
     return chunk_merger(chunks, source, chunk_size, overlap, metadata)



