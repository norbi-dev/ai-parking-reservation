"""Database engine and session factory for PostgreSQL persistence.

Provides engine creation and session management for SQLModel-based repositories.
"""

from loguru import logger
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine


def create_db_engine(database_url: str) -> Engine:
    """Create a SQLModel/SQLAlchemy engine.

    Args:
        database_url: PostgreSQL connection string

    Returns:
        SQLAlchemy Engine instance
    """
    logger.debug("Creating database engine for PostgreSQL")
    engine: Engine = create_engine(database_url, echo=False)
    logger.info("Database engine created")
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

    logger.debug("Creating database tables")
    engine = create_db_engine(database_url)
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")
