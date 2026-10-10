from app.db.session import Base, engine
from app.db import models # we dont need to import models directly, but this ensures that the models are registered with SQLAlchemy's metadata

"""
This script initializes the database by creating all tables defined in the SQLAlchemy models.
"""
Base.metadata.create_all(bind=engine)
print("Tables created")