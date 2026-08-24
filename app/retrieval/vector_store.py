from app.db.session import SessionLocal
from app.ingestion.embedder import get_embedding
from app.db.models import Chunk
from sqlalchemy.dialects.postgresql import insert


class VectorStore:

    def __init__(self, session):
        self.session = session


    def upsert(self, chunks):

        if not chunks:
            return {"status": "Success", "message": "No chunks to upsert!"}

        doc_texts = [chunk["text"] for chunk in chunks]
        doc_embeddings = get_embedding(doc_texts)

        rows = [{
            "content": c["text"],
            "embedding": e,
            "source": c["source"],
            "chunk_index": c["chunk_index"],
            "metadata_": c["metadata"],
        }
        for e, c in zip(doc_embeddings, chunks)
        ]


        # Stage the initial batch insert
        db_upsert = insert(Chunk).values(rows) # it prepares an SQL INSERT statement for the Document table,Each dictionary corresponds to a row to be inserted into the database.
        # db_upsert contains the SQL statement that will be executed to insert the rows into the Document table. 

        db_upsert = db_upsert.on_conflict_do_update(
            index_elements= ["source", "chunk_index"], # specifies the column(s) that should be used to detect conflicts, id gets from the Document model(which is pk)
            set_ = {
                "content": db_upsert.excluded.content, # The excluded object represents the row that was proposed for insertion but was rejected due to a conflict.
                "embedding": db_upsert.excluded.embedding,
                "metadata_": db_upsert.excluded.metadata_,
            }
        )

        try:
            # Execute everything in a single database round-trip
            db_result = self.session.execute(db_upsert)
            self.session.commit() 
            return {"status": "success", "count": db_result.rowcount}
        
        except Exception as e :
            self.session.rollback() # In case of an error, rollback the transaction to maintain database integrity
            return {"status": "error!", "message": e}

        
        