"""Unit tests for reservation use cases."""

from datetime import datetime
from uuid import uuid4

import pytest

from src.adapters.outgoing.persistence.in_memory import (
    InMemoryParkingSpaceRepository,
    InMemoryReservationRepository,
)
from src.core.domain.exceptions import (
    AuthorizationError,
    ReservationConflictError,
    ReservationNotFoundError,
    SpaceNotAvailableError,
    SpaceNotFoundError,
)
from src.core.domain.models import (
    ParkingSpace,
    Reservation,
    ReservationStatus,
    TimeSlot,
)
from src.core.usecases.admin_approval import AdminApprovalService
from src.core.usecases.check_availability import CheckAvailabilityService
from src.core.usecases.manage_parking_spaces import ManageParkingSpacesService
from src.core.usecases.manage_reservations import ManageReservationsService
from src.core.usecases.reserve_parking import ReserveParkingService


@pytest.fixture
def reservation_repo() -> InMemoryReservationRepository:
    """Create a fresh in-memory reservation repository."""
    return InMemoryReservationRepository()


@pytest.fixture
def space_repo() -> InMemoryParkingSpaceRepository:
    """Create an in-memory parking space repository with sample data."""
    repo = InMemoryParkingSpaceRepository()
    repo.save(
        ParkingSpace(space_id="A1", location="Level 1, Section A", hourly_rate=5.0)
    )
    repo.save(
        ParkingSpace(space_id="A2", location="Level 1, Section A", hourly_rate=5.0)
    )
    repo.save(
        ParkingSpace(
            space_id="B1",
            location="Level 1, Section B",
            hourly_rate=7.0,
            space_type="electric",
        )
    )
    repo.save(ParkingSpace(space_id="X1", location="Level 2", is_available=False))
    return repo


@pytest.fixture
def time_slot() -> TimeSlot:
    """Create a standard 2-hour time slot."""
    return TimeSlot(
        start_time=datetime(2024, 6, 15, 9, 0),
        end_time=datetime(2024, 6, 15, 11, 0),
    )


@pytest.mark.unit
class TestReserveParkingService:
    """Tests for the ReserveParking use case."""

    def test_create_reservation_success(
        self,
        reservation_repo: InMemoryReservationRepository,
        space_repo: InMemoryParkingSpaceRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test successful reservation creation."""
        service = ReserveParkingService(reservation_repo, space_repo)
        user_id = uuid4()

        result = service.execute(user_id=user_id, space_id="A1", time_slot=time_slot)

        assert result.status == ReservationStatus.PENDING
        assert result.user_id == user_id
        assert result.space_id == "A1"
        assert result.time_slot == time_slot
        assert reservation_repo.find_by_id(result.reservation_id) is not None

    def test_create_reservation_space_not_found(
        self,
        reservation_repo: InMemoryReservationRepository,
        space_repo: InMemoryParkingSpaceRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test reservation creation with non-existent space."""
        service = ReserveParkingService(reservation_repo, space_repo)

        with pytest.raises(SpaceNotFoundError, match="Z99"):
            service.execute(user_id=uuid4(), space_id="Z99", time_slot=time_slot)

    def test_create_reservation_space_not_available(
        self,
        reservation_repo: InMemoryReservationRepository,
        space_repo: InMemoryParkingSpaceRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test reservation creation with unavailable space."""
        service = ReserveParkingService(reservation_repo, space_repo)

        with pytest.raises(SpaceNotAvailableError, match="X1"):
            service.execute(user_id=uuid4(), space_id="X1", time_slot=time_slot)

    def test_create_reservation_conflict(
        self,
        reservation_repo: InMemoryReservationRepository,
        space_repo: InMemoryParkingSpaceRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test reservation creation with conflicting existing reservation."""
        service = ReserveParkingService(reservation_repo, space_repo)
        user1 = uuid4()
        user2 = uuid4()

        # First reservation succeeds
        service.execute(user_id=user1, space_id="A1", time_slot=time_slot)

        # Second reservation for same space and overlapping time fails
        with pytest.raises(ReservationConflictError, match="A1"):
            service.execute(user_id=user2, space_id="A1", time_slot=time_slot)

    def test_create_reservation_no_conflict_different_space(
        self,
        reservation_repo: InMemoryReservationRepository,
        space_repo: InMemoryParkingSpaceRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test that reservations for different spaces don't conflict."""
        service = ReserveParkingService(reservation_repo, space_repo)
        user_id = uuid4()

        r1 = service.execute(user_id=user_id, space_id="A1", time_slot=time_slot)
        r2 = service.execute(user_id=user_id, space_id="A2", time_slot=time_slot)

        assert r1.space_id == "A1"
        assert r2.space_id == "A2"


@pytest.mark.unit
class TestCheckAvailabilityService:
    """Tests for the CheckAvailability use case."""

    def test_all_spaces_available(
        self,
        reservation_repo: InMemoryReservationRepository,
        space_repo: InMemoryParkingSpaceRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test that all available spaces are returned when no reservations exist."""
        service = CheckAvailabilityService(reservation_repo, space_repo)
        available = service.execute(time_slot)

        # X1 is marked unavailable, so only 3 spaces
        assert len(available) == 3
        space_ids = {s.space_id for s in available}
        assert "X1" not in space_ids

    def test_space_unavailable_after_reservation(
        self,
        reservation_repo: InMemoryReservationRepository,
        space_repo: InMemoryParkingSpaceRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test that a space becomes unavailable after reservation."""
        # Create a reservation for A1
        reservation = Reservation(
            user_id=uuid4(),
            space_id="A1",
            time_slot=time_slot,
        )
        reservation_repo.save(reservation)

        service = CheckAvailabilityService(reservation_repo, space_repo)
        available = service.execute(time_slot)

        assert len(available) == 2
        space_ids = {s.space_id for s in available}
        assert "A1" not in space_ids

    def test_is_space_available_true(
        self,
        reservation_repo: InMemoryReservationRepository,
        space_repo: InMemoryParkingSpaceRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test checking specific space availability - available."""
        service = CheckAvailabilityService(reservation_repo, space_repo)
        assert service.is_space_available("A1", time_slot) is True

    def test_is_space_available_false_not_exists(
        self,
        reservation_repo: InMemoryReservationRepository,
        space_repo: InMemoryParkingSpaceRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test checking availability for non-existent space."""
        service = CheckAvailabilityService(reservation_repo, space_repo)
        assert service.is_space_available("Z99", time_slot) is False

    def test_is_space_available_false_marked_unavailable(
        self,
        reservation_repo: InMemoryReservationRepository,
        space_repo: InMemoryParkingSpaceRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test checking availability for space marked unavailable."""
        service = CheckAvailabilityService(reservation_repo, space_repo)
        assert service.is_space_available("X1", time_slot) is False


@pytest.mark.unit
class TestManageReservationsService:
    """Tests for the ManageReservations use case."""

    def test_get_user_reservations(
        self,
        reservation_repo: InMemoryReservationRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test getting all reservations for a user."""
        user_id = uuid4()
        reservation_repo.save(
            Reservation(user_id=user_id, space_id="A1", time_slot=time_slot)
        )
        reservation_repo.save(
            Reservation(user_id=user_id, space_id="A2", time_slot=time_slot)
        )
        reservation_repo.save(
            Reservation(user_id=uuid4(), space_id="B1", time_slot=time_slot)
        )

        service = ManageReservationsService(reservation_repo)
        results = service.get_user_reservations(user_id)

        assert len(results) == 2

    def test_cancel_reservation_success(
        self,
        reservation_repo: InMemoryReservationRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test successful reservation cancellation."""
        user_id = uuid4()
        reservation = Reservation(user_id=user_id, space_id="A1", time_slot=time_slot)
        reservation_repo.save(reservation)

        service = ManageReservationsService(reservation_repo)
        result = service.cancel_reservation(reservation.reservation_id, user_id)

        assert result.status == ReservationStatus.CANCELLED

    def test_cancel_reservation_not_found(
        self,
        reservation_repo: InMemoryReservationRepository,
    ) -> None:
        """Test cancelling a non-existent reservation."""
        service = ManageReservationsService(reservation_repo)

        with pytest.raises(ReservationNotFoundError):
            service.cancel_reservation(uuid4(), uuid4())

    def test_cancel_reservation_wrong_user(
        self,
        reservation_repo: InMemoryReservationRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test cancelling a reservation by a different user."""
        owner_id = uuid4()
        other_id = uuid4()
        reservation = Reservation(user_id=owner_id, space_id="A1", time_slot=time_slot)
        reservation_repo.save(reservation)

        service = ManageReservationsService(reservation_repo)

        with pytest.raises(AuthorizationError):
            service.cancel_reservation(reservation.reservation_id, other_id)

    def test_get_reservation_success(
        self,
        reservation_repo: InMemoryReservationRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test getting a specific reservation by ID."""
        reservation = Reservation(user_id=uuid4(), space_id="A1", time_slot=time_slot)
        reservation_repo.save(reservation)

        service = ManageReservationsService(reservation_repo)
        result = service.get_reservation(reservation.reservation_id)

        assert result.reservation_id == reservation.reservation_id

    def test_get_reservation_not_found(
        self,
        reservation_repo: InMemoryReservationRepository,
    ) -> None:
        """Test getting a non-existent reservation."""
        service = ManageReservationsService(reservation_repo)

        with pytest.raises(ReservationNotFoundError):
            service.get_reservation(uuid4())


@pytest.mark.unit
class TestAdminApprovalService:
    """Tests for the AdminApproval use case."""

    def test_get_pending_reservations(
        self,
        reservation_repo: InMemoryReservationRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test getting all pending reservations."""
        # Add pending and confirmed reservations
        pending = Reservation(user_id=uuid4(), space_id="A1", time_slot=time_slot)
        reservation_repo.save(pending)

        confirmed = Reservation(user_id=uuid4(), space_id="A2", time_slot=time_slot)
        confirmed.approve("OK")
        reservation_repo.save(confirmed)

        service = AdminApprovalService(reservation_repo)
        results = service.get_pending_reservations()

        assert len(results) == 1
        assert results[0].reservation_id == pending.reservation_id

    def test_approve_reservation_success(
        self,
        reservation_repo: InMemoryReservationRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test successful reservation approval."""
        reservation = Reservation(user_id=uuid4(), space_id="A1", time_slot=time_slot)
        reservation_repo.save(reservation)

        service = AdminApprovalService(reservation_repo)
        result = service.approve_reservation(
            reservation.reservation_id, "Approved by admin"
        )

        assert result.status == ReservationStatus.CONFIRMED
        assert result.admin_notes == "Approved by admin"

    def test_approve_reservation_not_found(
        self,
        reservation_repo: InMemoryReservationRepository,
    ) -> None:
        """Test approving a non-existent reservation."""
        service = AdminApprovalService(reservation_repo)

        with pytest.raises(ReservationNotFoundError):
            service.approve_reservation(uuid4())

    def test_reject_reservation_success(
        self,
        reservation_repo: InMemoryReservationRepository,
        time_slot: TimeSlot,
    ) -> None:
        """Test successful reservation rejection."""
        reservation = Reservation(user_id=uuid4(), space_id="A1", time_slot=time_slot)
        reservation_repo.save(reservation)

        service = AdminApprovalService(reservation_repo)
        result = service.reject_reservation(
            reservation.reservation_id, "Space under maintenance"
        )

        assert result.status == ReservationStatus.REJECTED
        assert result.admin_notes == "Space under maintenance"

    def test_reject_reservation_not_found(
        self,
        reservation_repo: InMemoryReservationRepository,
    ) -> None:
        """Test rejecting a non-existent reservation."""
        service = AdminApprovalService(reservation_repo)

        with pytest.raises(ReservationNotFoundError):
            service.reject_reservation(uuid4())


@pytest.mark.unit
class TestManageParkingSpacesService:
    """Tests for the ManageParkingSpaces use case."""

    def test_add_space(
        self,
        space_repo: InMemoryParkingSpaceRepository,
    ) -> None:
        """Test adding a new parking space."""
        service = ManageParkingSpacesService(space_repo)
        new_space = ParkingSpace(space_id="F1", location="Level 3")

        result = service.add_space(new_space)

        assert result.space_id == "F1"
        assert space_repo.find_by_id("F1") is not None

    def test_update_space(
        self,
        space_repo: InMemoryParkingSpaceRepository,
    ) -> None:
        """Test updating an existing parking space."""
        service = ManageParkingSpacesService(space_repo)
        updated = ParkingSpace(
            space_id="A1", location="Level 1, Section A", hourly_rate=10.0
        )

        result = service.update_space(updated)

        assert result.hourly_rate == 10.0

    def test_update_space_not_found(
        self,
        space_repo: InMemoryParkingSpaceRepository,
    ) -> None:
        """Test updating a non-existent parking space."""
        service = ManageParkingSpacesService(space_repo)
        space = ParkingSpace(space_id="Z99", location="Nowhere")

        with pytest.raises(SpaceNotFoundError):
            service.update_space(space)

    def test_remove_space(
        self,
        space_repo: InMemoryParkingSpaceRepository,
    ) -> None:
        """Test removing a parking space."""
        service = ManageParkingSpacesService(space_repo)
        service.remove_space("A1")

        assert space_repo.find_by_id("A1") is None

    def test_remove_space_not_found(
        self,
        space_repo: InMemoryParkingSpaceRepository,
    ) -> None:
        """Test removing a non-existent parking space."""
        service = ManageParkingSpacesService(space_repo)

        with pytest.raises(SpaceNotFoundError):
            service.remove_space("Z99")

    def test_get_all_spaces(
        self,
        space_repo: InMemoryParkingSpaceRepository,
    ) -> None:
        """Test getting all parking spaces."""
        service = ManageParkingSpacesService(space_repo)
        spaces = service.get_all_spaces()

        assert len(spaces) == 4  # A1, A2, B1, X1
