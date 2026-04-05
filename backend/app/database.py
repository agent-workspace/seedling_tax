from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

from app.config import settings

engine_kwargs = {"pool_pre_ping": True}

# SQLite needs this for multithreaded FastAPI request handling
if settings.DATABASE_URL.startswith("sqlite") or settings.DATABASE_URL.startswith("sqlite+"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
