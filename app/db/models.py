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

