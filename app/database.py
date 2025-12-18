from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from sqlalchemy.exc import OperationalError
from app.config import DATABASE_URL
import os

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


def create_db_engine_with_retry():
    """Create database engine with retry pattern for PostgreSQL."""
    @retry(
        retry=retry_if_exception_type(OperationalError),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def _create():
        engine = create_engine(DATABASE_URL)
        engine.connect()
        return engine
    return _create()


def create_db_engine():
    """Create database engine (SQLite doesn't need retry)."""
    # SQLite doesn't need retry logic
    if DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        return create_engine(DATABASE_URL, connect_args=connect_args)
    else:
        # PostgreSQL with retry pattern
        return create_db_engine_with_retry()


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
