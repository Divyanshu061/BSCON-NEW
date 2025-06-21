# Path: app/utils/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# ---------------------------------------------------------
# Create SQLAlchemy engine
# ---------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # helps with dropped connections
    # echo=True,             # uncomment for SQL logging
)

# ---------------------------------------------------------
# Session factory
# ---------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ---------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------
Base = declarative_base()

# ---------------------------------------------------------
# Dependency to inject DB session into path operations
# ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
