"""Unit tests for domain models."""

from datetime import datetime
from uuid import uuid4

import pytest

from src.core.domain.models import (
    ParkingSpace,
    Reservation,
    ReservationStatus,
    TimeSlot,
    User,
    UserRole,
)


class TestTimeSlot:
    """Tests for the TimeSlot value object."""

    def test_create_valid_time_slot(self) -> None:
        """Test creating a valid time slot."""
        start = datetime(2024, 1, 15, 9, 0)
        end = datetime(2024, 1, 15, 11, 0)
        slot = TimeSlot(start_time=start, end_time=end)

        assert slot.start_time == start
        assert slot.end_time == end

    def test_create_invalid_time_slot_end_before_start(self) -> None:
        """Test that end_time before start_time raises ValueError."""
        start = datetime(2024, 1, 15, 11, 0)
        end = datetime(2024, 1, 15, 9, 0)

        with pytest.raises(ValueError, match="end_time must be after start_time"):
            TimeSlot(start_time=start, end_time=end)

    def test_create_invalid_time_slot_same_time(self) -> None:
        """Test that equal start and end time raises ValueError."""
        same_time = datetime(2024, 1, 15, 9, 0)

        with pytest.raises(ValueError, match="end_time must be after start_time"):
            TimeSlot(start_time=same_time, end_time=same_time)

    def test_duration_hours(self) -> None:
        """Test duration calculation in hours."""
        start = datetime(2024, 1, 15, 9, 0)
        end = datetime(2024, 1, 15, 11, 30)
        slot = TimeSlot(start_time=start, end_time=end)

        assert slot.duration_hours == 2.5

    def test_time_slot_is_frozen(self) -> None:
        """Test that TimeSlot is immutable."""
        slot = TimeSlot(
            start_time=datetime(2024, 1, 15, 9, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
        )

        with pytest.raises(AttributeError):
            slot.start_time = datetime(2024, 1, 15, 10, 0)  # type: ignore[misc]


class TestParkingSpace:
    """Tests for the ParkingSpace domain model."""

    def test_create_parking_space_defaults(self) -> None:
        """Test creating a parking space with default values."""
        space = ParkingSpace(space_id="A1", location="Level 1")

        assert space.space_id == "A1"
        assert space.location == "Level 1"
        assert space.is_available is True
        assert space.hourly_rate == 5.0
        assert space.space_type == "standard"

    def test_create_parking_space_custom(self) -> None:
        """Test creating a parking space with custom values."""
        space = ParkingSpace(
            space_id="B1",
            location="Level 2",
            is_available=False,
            hourly_rate=7.0,
            space_type="electric",
        )

        assert space.space_id == "B1"
        assert space.is_available is False
        assert space.hourly_rate == 7.0
        assert space.space_type == "electric"


class TestUser:
    """Tests for the User domain model."""

    def test_create_user_defaults(self) -> None:
        """Test creating a user with default values."""
        user = User()

        assert user.user_id is not None
        assert user.role == UserRole.CLIENT

    def test_create_admin_user(self) -> None:
        """Test creating an admin user."""
        user = User(
            username="admin",
            email="admin@parking.com",
            role=UserRole.ADMIN,
            full_name="Admin User",
        )

        assert user.role == UserRole.ADMIN
        assert user.username == "admin"


class TestReservation:
    """Tests for the Reservation domain model."""

    def _make_reservation(
        self, status: ReservationStatus = ReservationStatus.PENDING
    ) -> Reservation:
        """Create a test reservation.

        Args:
            status: Initial status for the reservation

        Returns:
            A test reservation instance
        """
        reservation = Reservation(
            user_id=uuid4(),
            space_id="A1",
            time_slot=TimeSlot(
                start_time=datetime(2024, 1, 15, 9, 0),
                end_time=datetime(2024, 1, 15, 11, 0),
            ),
        )
        reservation.status = status
        return reservation

    def test_create_reservation_default_pending(self) -> None:
        """Test that new reservations default to pending status."""
        reservation = self._make_reservation()

        assert reservation.status == ReservationStatus.PENDING
        assert reservation.reservation_id is not None
        assert reservation.admin_notes == ""

    def test_approve_pending_reservation(self) -> None:
        """Test approving a pending reservation."""
        reservation = self._make_reservation()
        reservation.approve("Looks good")

        assert reservation.status == ReservationStatus.CONFIRMED
        assert reservation.admin_notes == "Looks good"

    def test_approve_non_pending_raises(self) -> None:
        """Test that approving a non-pending reservation raises ValueError."""
        reservation = self._make_reservation(ReservationStatus.CONFIRMED)

        with pytest.raises(ValueError, match="Cannot approve"):
            reservation.approve()

    def test_reject_pending_reservation(self) -> None:
        """Test rejecting a pending reservation."""
        reservation = self._make_reservation()
        reservation.reject("Space under maintenance")

        assert reservation.status == ReservationStatus.REJECTED
        assert reservation.admin_notes == "Space under maintenance"

    def test_reject_non_pending_raises(self) -> None:
        """Test that rejecting a non-pending reservation raises ValueError."""
        reservation = self._make_reservation(ReservationStatus.CONFIRMED)

        with pytest.raises(ValueError, match="Cannot reject"):
            reservation.reject()

    def test_cancel_pending_reservation(self) -> None:
        """Test cancelling a pending reservation."""
        reservation = self._make_reservation()
        reservation.cancel()

        assert reservation.status == ReservationStatus.CANCELLED

    def test_cancel_confirmed_reservation(self) -> None:
        """Test cancelling a confirmed reservation."""
        reservation = self._make_reservation(ReservationStatus.CONFIRMED)
        reservation.cancel()

        assert reservation.status == ReservationStatus.CANCELLED

    def test_cancel_rejected_raises(self) -> None:
        """Test that cancelling a rejected reservation raises ValueError."""
        reservation = self._make_reservation(ReservationStatus.REJECTED)

        with pytest.raises(ValueError, match="Cannot cancel"):
            reservation.cancel()

    def test_cancel_already_cancelled_raises(self) -> None:
        """Test that cancelling an already cancelled reservation raises ValueError."""
        reservation = self._make_reservation(ReservationStatus.CANCELLED)

        with pytest.raises(ValueError, match="Cannot cancel"):
            reservation.cancel()
