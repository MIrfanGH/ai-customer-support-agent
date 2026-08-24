from app.ingestion.extractor import doc_extractor
from app.ingestion.chunker import recursive_chunker
from app.retrieval.vector_store import VectorStore
from app.db.session import SessionLocal

SEPARATOR = ["\n\n", "\n", ". ", ""]
all_chunks = [] # list of dict, each dict represents one final chunk plus its metadata.

docs = doc_extractor("data/documents")
for doc in docs:

    chunks = recursive_chunker(
        text = doc["content"],
        source= doc["source"],
        separator=SEPARATOR,
        chunk_size=50,
        overlap=10,
        metadata= doc["metadata"],

    )
    all_chunks.extend(chunks)

session = SessionLocal()
vs = VectorStore(session)

result = vs.upsert(all_chunks)

print(result)

