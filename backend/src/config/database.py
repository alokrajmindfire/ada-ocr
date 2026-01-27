from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.env import settings

if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
