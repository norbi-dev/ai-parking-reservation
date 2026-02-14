"""Database engine and session factory for PostgreSQL persistence.

Provides engine creation and session management for SQLModel-based repositories.
"""

from collections.abc import Generator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine


def create_db_engine(database_url: str) -> Engine:
    """Create a SQLModel/SQLAlchemy engine.

    Args:
        database_url: PostgreSQL connection string

    Returns:
        SQLAlchemy Engine instance
    """
    engine: Engine = create_engine(database_url, echo=False)
    return engine


def create_tables(database_url: str) -> None:
    """Create all database tables from SQLModel metadata.

    Args:
        database_url: PostgreSQL connection string
    """
    # Import models to ensure they are registered with SQLModel.metadata
    from src.adapters.outgoing.persistence.models import (  # noqa: F401
        ParkingSpaceDB,
        ReservationDB,
        UserDB,
    )

    engine = create_db_engine(database_url)
    SQLModel.metadata.create_all(engine)


def get_session(database_url: str) -> Generator[Session]:
    """Create a database session (generator for dependency injection).

    Args:
        database_url: PostgreSQL connection string

    Yields:
        SQLModel Session
    """
    engine = create_db_engine(database_url)
    with Session(engine) as session:
        yield session
