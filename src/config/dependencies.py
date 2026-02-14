"""Dependency injection using simple factory functions with caching.

All dependencies are cached automatically using @lru_cache.
When USE_POSTGRES=true, PostgreSQL repositories are used; otherwise in-memory.
"""

from functools import lru_cache
from typing import Any

from src.adapters.outgoing.persistence.in_memory import (
    InMemoryParkingSpaceRepository,
    InMemoryReservationRepository,
    InMemoryUserRepository,
)
from src.config.settings import Settings
from src.core.domain.models import ParkingSpace
from src.core.ports.outgoing.repositories import (
    ParkingSpaceRepository,
    ReservationRepository,
    UserRepository,
)
from src.core.usecases.admin_approval import AdminApprovalService
from src.core.usecases.check_availability import CheckAvailabilityService
from src.core.usecases.manage_parking_spaces import ManageParkingSpacesService
from src.core.usecases.manage_reservations import ManageReservationsService
from src.core.usecases.reserve_parking import ReserveParkingService


@lru_cache
def get_settings() -> Settings:
    """Get application settings (cached).

    Returns:
        Application settings loaded from environment
    """
    return Settings()


@lru_cache
def _get_db_session() -> Any:
    """Get a SQLModel database session (cached).

    Returns:
        SQLModel Session connected to PostgreSQL
    """
    from sqlmodel import Session

    from src.adapters.outgoing.persistence.database import (
        create_db_engine,
        create_tables,
    )

    settings = get_settings()
    create_tables(settings.database_url)
    engine = create_db_engine(settings.database_url)
    return Session(engine)


@lru_cache
def get_reservation_repository() -> ReservationRepository:
    """Get reservation repository (cached).

    Uses PostgreSQL when USE_POSTGRES=true, otherwise in-memory.

    Returns:
        Reservation repository instance
    """
    settings = get_settings()
    if settings.use_postgres:
        from src.adapters.outgoing.persistence.postgres import (
            PostgresReservationRepository,
        )

        return PostgresReservationRepository(session=_get_db_session())

    return InMemoryReservationRepository()


@lru_cache
def get_parking_space_repository() -> ParkingSpaceRepository:
    """Get parking space repository (cached).

    Uses PostgreSQL when USE_POSTGRES=true, otherwise in-memory with seed data.

    Returns:
        Parking space repository instance
    """
    settings = get_settings()
    if settings.use_postgres:
        from src.adapters.outgoing.persistence.postgres import (
            PostgresParkingSpaceRepository,
        )

        repo: ParkingSpaceRepository = PostgresParkingSpaceRepository(
            session=_get_db_session()
        )
        _seed_parking_spaces(repo)
        return repo

    in_memory_repo = InMemoryParkingSpaceRepository()
    _seed_parking_spaces(in_memory_repo)
    return in_memory_repo


@lru_cache
def get_user_repository() -> UserRepository:
    """Get user repository (cached).

    Uses PostgreSQL when USE_POSTGRES=true, otherwise in-memory.

    Returns:
        User repository instance
    """
    settings = get_settings()
    if settings.use_postgres:
        from src.adapters.outgoing.persistence.postgres import (
            PostgresUserRepository,
        )

        return PostgresUserRepository(session=_get_db_session())

    return InMemoryUserRepository()


def get_reserve_parking_usecase() -> ReserveParkingService:
    """Get reserve parking use case.

    Returns:
        ReserveParkingService wired with repositories
    """
    return ReserveParkingService(
        reservation_repo=get_reservation_repository(),
        space_repo=get_parking_space_repository(),
    )


def get_check_availability_usecase() -> CheckAvailabilityService:
    """Get check availability use case.

    Returns:
        CheckAvailabilityService wired with repositories
    """
    return CheckAvailabilityService(
        reservation_repo=get_reservation_repository(),
        space_repo=get_parking_space_repository(),
    )


def get_manage_reservations_usecase() -> ManageReservationsService:
    """Get manage reservations use case.

    Returns:
        ManageReservationsService wired with repositories
    """
    return ManageReservationsService(
        reservation_repo=get_reservation_repository(),
    )


def get_admin_approval_usecase() -> AdminApprovalService:
    """Get admin approval use case.

    Returns:
        AdminApprovalService wired with repositories
    """
    return AdminApprovalService(
        reservation_repo=get_reservation_repository(),
    )


def get_manage_parking_spaces_usecase() -> ManageParkingSpacesService:
    """Get manage parking spaces use case.

    Returns:
        ManageParkingSpacesService wired with repositories
    """
    return ManageParkingSpacesService(
        space_repo=get_parking_space_repository(),
    )


def _seed_parking_spaces(repo: ParkingSpaceRepository) -> None:
    """Seed the parking space repository with sample data.

    Checks if data already exists to avoid duplicates (important for PostgreSQL).

    Args:
        repo: Parking space repository to seed
    """
    # Skip seeding if spaces already exist
    if repo.find_all():
        return

    sample_spaces = [
        ParkingSpace(
            space_id="A1",
            location="Level 1, Section A",
            hourly_rate=5.0,
            space_type="standard",
        ),
        ParkingSpace(
            space_id="A2",
            location="Level 1, Section A",
            hourly_rate=5.0,
            space_type="standard",
        ),
        ParkingSpace(
            space_id="A3",
            location="Level 1, Section A",
            hourly_rate=5.0,
            space_type="standard",
        ),
        ParkingSpace(
            space_id="B1",
            location="Level 1, Section B",
            hourly_rate=7.0,
            space_type="electric",
        ),
        ParkingSpace(
            space_id="B2",
            location="Level 1, Section B",
            hourly_rate=7.0,
            space_type="electric",
        ),
        ParkingSpace(
            space_id="C1",
            location="Level 2, Section C",
            hourly_rate=4.0,
            space_type="standard",
        ),
        ParkingSpace(
            space_id="C2",
            location="Level 2, Section C",
            hourly_rate=4.0,
            space_type="standard",
        ),
        ParkingSpace(
            space_id="D1",
            location="Level 2, Section D",
            hourly_rate=6.0,
            space_type="handicap",
        ),
        ParkingSpace(
            space_id="E1",
            location="Outdoor, Section E",
            hourly_rate=3.0,
            space_type="standard",
        ),
        ParkingSpace(
            space_id="E2",
            location="Outdoor, Section E",
            hourly_rate=3.0,
            space_type="standard",
        ),
    ]

    for space in sample_spaces:
        repo.save(space)
