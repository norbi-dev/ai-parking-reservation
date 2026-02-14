"""Fixtures for integration tests.

Starts PostgreSQL via podman-compose before the test session and provides
a clean database session for each test.
"""

import subprocess
import time

import pytest
from sqlmodel import Session, SQLModel, create_engine, text

DATABASE_URL = "postgresql://parkinguser:parkingpass@localhost:5432/parkingreservation"


def _wait_for_postgres(url: str, timeout: int = 30) -> None:
    """Wait for PostgreSQL to accept connections.

    Args:
        url: Database connection URL
        timeout: Max seconds to wait

    Raises:
        TimeoutError: If PostgreSQL doesn't respond in time
    """
    engine = create_engine(url)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception:  # noqa: BLE001
            time.sleep(1)
    msg = f"PostgreSQL did not start within {timeout}s"
    raise TimeoutError(msg)


@pytest.fixture(scope="session", autouse=True)
def _postgres_container():
    """Start PostgreSQL container for the integration test session.

    Uses podman-compose to start only the postgres service from
    docker-compose.yml. The container is stopped after all tests complete.
    """
    # Start only the postgres service
    subprocess.run(
        ["podman-compose", "up", "-d", "postgres"],
        check=True,
        capture_output=True,
    )

    # Wait for it to be ready
    _wait_for_postgres(DATABASE_URL)

    yield

    # Teardown: stop the postgres service
    subprocess.run(
        ["podman-compose", "down", "-v", "postgres"],
        check=True,
        capture_output=True,
    )


@pytest.fixture
def db_session(_postgres_container):
    """Provide a clean database session for each test.

    Creates all tables before the test and drops them after,
    ensuring complete isolation between tests.

    Yields:
        SQLModel Session
    """
    # Import DB models to register them with SQLModel metadata
    from src.adapters.outgoing.persistence.models import (  # noqa: F401
        ParkingSpaceDB,
        ReservationDB,
        UserDB,
    )

    engine = create_engine(DATABASE_URL)

    # Create fresh tables
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    # Drop all tables for a clean slate
    SQLModel.metadata.drop_all(engine)
