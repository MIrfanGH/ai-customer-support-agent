from sqlalchemy import text

from app.db.session import Base, engine
from app.db import models  # noqa: F401, suppresses the unused import warning for this line, registers models with Base.metadata

"""
Initializes the database: enables the pgvector extension, then creates all tables.
The extension must exist BEFORE create_all, 
    because doc_chunks has a Vector column and an HNSW index that depend on it.
"""

def main():
    with engine.begin() as conn:        # begin() is a context manager from sqlalchemy.engine.Connection that automatically commits or rolls back the transaction
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector")) # execute() is a method from sqlalchemy.engine.Connection that executes a SQL statement and returns a Result object

    Base.metadata.create_all(bind=engine)
    print("Extension and tables created")

if __name__ == "__main__":
    main()