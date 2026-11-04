import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL

# SQLite Database File Path (used when DATABASE_URL isn't set)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "campus_os.db")

def _normalize_postgres_url(url: str) -> str:
    # Supabase shows "postgres://" URLs, which SQLAlchemy 2 rejects, and SQLAlchemy 2.1 maps a
    # bare "postgresql://" to psycopg 3. Pin the psycopg2 driver that requirements.txt installs.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix):]
    return url


SQLALCHEMY_DATABASE_URL = _normalize_postgres_url(DATABASE_URL) if DATABASE_URL else f"sqlite:///{DB_PATH}"

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}  # Needed for SQLite in multi-threaded FastAPI
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
