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


def _sync_columns() -> list[str]:
    """Add columns the models have but an existing database lacks.

    create_all only creates missing tables, so a database made by an earlier version
    (e.g. Supabase in production) would miss columns added since. They're added as
    nullable, which existing rows need; the models supply defaults for new rows.
    Returns "table.column" for each one added.
    """
    from sqlalchemy import inspect, text

    added = []
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in tables:
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing:
                    continue
                sql_type = column.type.compile(dialect=engine.dialect)
                conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN "{column.name}" {sql_type}'))
                added.append(f"{table.name}.{column.name}")
    return added


def schema_status() -> dict:
    """Tables or columns the models expect but the database doesn't have (for /api/health)."""
    from sqlalchemy import inspect

    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        missing = []
        for table in Base.metadata.sorted_tables:
            if table.name not in tables:
                missing.append(table.name)
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            missing.extend(f"{table.name}.{c.name}" for c in table.columns if c.name not in existing)
        return {"ok": not missing, "dialect": engine.dialect.name, "tables": len(tables), "missing": missing}
    except Exception as exc:
        return {"ok": False, "dialect": engine.dialect.name, "error": str(exc)}


def init_db():
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    added = _sync_columns()
    if added:
        print(f"Database: added columns {', '.join(added)}")
