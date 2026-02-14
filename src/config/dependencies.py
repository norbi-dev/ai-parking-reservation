"""Dependency injection using simple factory functions with caching.

All dependencies are cached automatically using @lru_cache.
No need for complex container classes!
"""

from functools import lru_cache

from src.adapters.outgoing.persistence.in_memory import (
    InMemoryParkingSpaceRepository,
    InMemoryReservationRepository,
    InMemoryUserRepository,
)
from src.config.settings import Settings
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
def get_reservation_repository() -> InMemoryReservationRepository:
    """Get reservation repository (cached).

    Returns:
        Reservation repository instance
    """
    return InMemoryReservationRepository()


@lru_cache
def get_parking_space_repository() -> InMemoryParkingSpaceRepository:
    """Get parking space repository (cached).

    Returns:
        Parking space repository instance
    """
    repo = InMemoryParkingSpaceRepository()
    _seed_parking_spaces(repo)
    return repo


@lru_cache
def get_user_repository() -> InMemoryUserRepository:
    """Get user repository (cached).

    Returns:
        User repository instance
    """
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


def _seed_parking_spaces(repo: InMemoryParkingSpaceRepository) -> None:
    """Seed the parking space repository with sample data.

    Args:
        repo: Parking space repository to seed
    """
    from src.core.domain.models import ParkingSpace

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
