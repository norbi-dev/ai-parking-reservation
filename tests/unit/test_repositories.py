"""Unit tests for in-memory repository implementations."""

from datetime import datetime
from uuid import uuid4

from src.adapters.outgoing.persistence.in_memory import (
    InMemoryParkingSpaceRepository,
    InMemoryReservationRepository,
    InMemoryUserRepository,
)
from src.core.domain.models import (
    ParkingSpace,
    Reservation,
    ReservationStatus,
    TimeSlot,
    User,
)


class TestInMemoryReservationRepository:
    """Tests for InMemoryReservationRepository."""

    def test_save_and_find_by_id(self) -> None:
        """Test saving and retrieving a reservation."""
        repo = InMemoryReservationRepository()
        reservation = Reservation(
            user_id=uuid4(),
            space_id="A1",
            time_slot=TimeSlot(
                start_time=datetime(2024, 1, 15, 9, 0),
                end_time=datetime(2024, 1, 15, 11, 0),
            ),
        )

        repo.save(reservation)
        found = repo.find_by_id(reservation.reservation_id)

        assert found is not None
        assert found.reservation_id == reservation.reservation_id

    def test_find_by_id_not_found(self) -> None:
        """Test finding a non-existent reservation returns None."""
        repo = InMemoryReservationRepository()
        assert repo.find_by_id(uuid4()) is None

    def test_find_by_user_id(self) -> None:
        """Test finding reservations by user ID."""
        repo = InMemoryReservationRepository()
        user_id = uuid4()
        slot = TimeSlot(
            start_time=datetime(2024, 1, 15, 9, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
        )

        repo.save(Reservation(user_id=user_id, space_id="A1", time_slot=slot))
        repo.save(Reservation(user_id=user_id, space_id="A2", time_slot=slot))
        repo.save(Reservation(user_id=uuid4(), space_id="B1", time_slot=slot))

        results = repo.find_by_user_id(user_id)
        assert len(results) == 2

    def test_find_by_user_id_with_status_filter(self) -> None:
        """Test finding user reservations with status filter."""
        repo = InMemoryReservationRepository()
        user_id = uuid4()
        slot = TimeSlot(
            start_time=datetime(2024, 1, 15, 9, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
        )

        r1 = Reservation(user_id=user_id, space_id="A1", time_slot=slot)
        r2 = Reservation(user_id=user_id, space_id="A2", time_slot=slot)
        r2.approve("OK")

        repo.save(r1)
        repo.save(r2)

        pending = repo.find_by_user_id(user_id, ReservationStatus.PENDING)
        assert len(pending) == 1
        assert pending[0].space_id == "A1"

    def test_find_by_status(self) -> None:
        """Test finding reservations by status."""
        repo = InMemoryReservationRepository()
        slot = TimeSlot(
            start_time=datetime(2024, 1, 15, 9, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
        )

        r1 = Reservation(user_id=uuid4(), space_id="A1", time_slot=slot)
        r2 = Reservation(user_id=uuid4(), space_id="A2", time_slot=slot)
        r2.approve("OK")

        repo.save(r1)
        repo.save(r2)

        pending = repo.find_by_status(ReservationStatus.PENDING)
        assert len(pending) == 1

    def test_find_by_space_and_time_overlap(self) -> None:
        """Test finding overlapping reservations."""
        repo = InMemoryReservationRepository()

        existing_slot = TimeSlot(
            start_time=datetime(2024, 1, 15, 9, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
        )
        repo.save(Reservation(user_id=uuid4(), space_id="A1", time_slot=existing_slot))

        # Overlapping query
        query_slot = TimeSlot(
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 12, 0),
        )
        results = repo.find_by_space_and_time("A1", query_slot)
        assert len(results) == 1

    def test_find_by_space_and_time_no_overlap(self) -> None:
        """Test finding non-overlapping reservations returns empty."""
        repo = InMemoryReservationRepository()

        existing_slot = TimeSlot(
            start_time=datetime(2024, 1, 15, 9, 0),
            end_time=datetime(2024, 1, 15, 11, 0),
        )
        repo.save(Reservation(user_id=uuid4(), space_id="A1", time_slot=existing_slot))

        # Non-overlapping query
        query_slot = TimeSlot(
            start_time=datetime(2024, 1, 15, 11, 0),
            end_time=datetime(2024, 1, 15, 13, 0),
        )
        results = repo.find_by_space_and_time("A1", query_slot)
        assert len(results) == 0

    def test_update(self) -> None:
        """Test updating a reservation."""
        repo = InMemoryReservationRepository()
        reservation = Reservation(
            user_id=uuid4(),
            space_id="A1",
            time_slot=TimeSlot(
                start_time=datetime(2024, 1, 15, 9, 0),
                end_time=datetime(2024, 1, 15, 11, 0),
            ),
        )
        repo.save(reservation)

        reservation.approve("Approved")
        repo.update(reservation)

        found = repo.find_by_id(reservation.reservation_id)
        assert found is not None
        assert found.status == ReservationStatus.CONFIRMED

    def test_delete(self) -> None:
        """Test deleting a reservation."""
        repo = InMemoryReservationRepository()
        reservation = Reservation(
            user_id=uuid4(),
            space_id="A1",
            time_slot=TimeSlot(
                start_time=datetime(2024, 1, 15, 9, 0),
                end_time=datetime(2024, 1, 15, 11, 0),
            ),
        )
        repo.save(reservation)
        repo.delete(reservation.reservation_id)

        assert repo.find_by_id(reservation.reservation_id) is None


class TestInMemoryParkingSpaceRepository:
    """Tests for InMemoryParkingSpaceRepository."""

    def test_save_and_find_by_id(self) -> None:
        """Test saving and retrieving a parking space."""
        repo = InMemoryParkingSpaceRepository()
        space = ParkingSpace(space_id="A1", location="Level 1")

        repo.save(space)
        found = repo.find_by_id("A1")

        assert found is not None
        assert found.space_id == "A1"

    def test_find_all(self) -> None:
        """Test finding all parking spaces."""
        repo = InMemoryParkingSpaceRepository()
        repo.save(ParkingSpace(space_id="A1", location="Level 1"))
        repo.save(ParkingSpace(space_id="A2", location="Level 1"))

        assert len(repo.find_all()) == 2

    def test_find_available(self) -> None:
        """Test finding available parking spaces."""
        repo = InMemoryParkingSpaceRepository()
        repo.save(ParkingSpace(space_id="A1", location="Level 1", is_available=True))
        repo.save(ParkingSpace(space_id="A2", location="Level 1", is_available=False))

        available = repo.find_available()
        assert len(available) == 1
        assert available[0].space_id == "A1"

    def test_delete(self) -> None:
        """Test deleting a parking space."""
        repo = InMemoryParkingSpaceRepository()
        repo.save(ParkingSpace(space_id="A1", location="Level 1"))
        repo.delete("A1")

        assert repo.find_by_id("A1") is None


class TestInMemoryUserRepository:
    """Tests for InMemoryUserRepository."""

    def test_save_and_find_by_id(self) -> None:
        """Test saving and retrieving a user."""
        repo = InMemoryUserRepository()
        user = User(username="testuser", email="test@test.com")

        repo.save(user)
        found = repo.find_by_id(user.user_id)

        assert found is not None
        assert found.username == "testuser"

    def test_find_by_username(self) -> None:
        """Test finding a user by username."""
        repo = InMemoryUserRepository()
        user = User(username="testuser", email="test@test.com")
        repo.save(user)

        found = repo.find_by_username("testuser")
        assert found is not None
        assert found.user_id == user.user_id

    def test_find_by_username_not_found(self) -> None:
        """Test finding a non-existent username returns None."""
        repo = InMemoryUserRepository()
        assert repo.find_by_username("nobody") is None
