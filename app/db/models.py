from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, Index, func
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB
from app.db.session import Base



class Chunk(Base):
    __tablename__ = "doc_chunks"

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    source = Column(String, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    metadata_ = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # Ensure each source + chunk_index pair is unique
        UniqueConstraint("source", "chunk_index", name="uq_source_chunk_index"),

        # HNSW index for fast vector search and avoid full seq scan
        # Must use the same distance operator at query time (cosine here).
        # If ops and query distance mismatch, results can be wrong.
        Index(
            "ix_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )



class Ticket(Base):

    """
    It stores the information about the ticket created. 
    It contains the query, reason (why the ticket was escalated), summary, and retrieved sources.
    """
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    query = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    summary = Column(String, nullable=True)
    retrieved_sources = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

