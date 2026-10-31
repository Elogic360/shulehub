from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, DeclarativeBase, Session
from app.core.config import settings

# PostgreSQL 18 Engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session and safely closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_rls_tenant_context(session: Session, school_id: str | None) -> None:
    """Sets PostgreSQL session variable for Row-Level Security isolation."""
    if school_id:
        session.execute(
            text("SELECT set_config('app.current_school_id', :school_id, true)"),
            {"school_id": str(school_id)},
        )
    else:
        session.execute(
            text("SELECT set_config('app.current_school_id', '', true)")
        )
