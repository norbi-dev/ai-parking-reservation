"""Integration tests for PostgreSQL repository implementations.

These tests run against a real PostgreSQL database started via podman-compose.
Mark: @pytest.mark.integration
"""

from datetime import datetime
from uuid import uuid4

import pytest

from src.adapters.outgoing.persistence.postgres import (
    PostgresParkingSpaceRepository,
    PostgresReservationRepository,
    PostgresUserRepository,
)
from src.core.domain.models import (
    ParkingSpace,
    Reservation,
    ReservationStatus,
    TimeSlot,
    User,
    UserRole,
)


@pytest.mark.integration
class TestPostgresReservationRepository:
    """Integration tests for PostgresReservationRepository."""

    def test_save_and_find_by_id(self, db_session) -> None:
        """Test saving and retrieving a reservation from PostgreSQL."""
        repo = PostgresReservationRepository(db_session)
        reservation = Reservation(
            user_id=uuid4(),
            space_id="A1",
            time_slot=TimeSlot(
                start_time=datetime(2024, 1, 15, 9, 0),
                end_time=datetime(2024, 1, 15, 11, 0),
            ),
        )

        saved = repo.save(reservation)
        found = repo.find_by_id(saved.reservation_id)

        assert found is not None
        assert found.reservation_id == reservation.reservation_id
        assert found.space_id == "A1"
        assert found.status == ReservationStatus.PENDING

    def test_find_by_id_not_found(self, db_session) -> None:
        """Test finding a non-existent reservation returns None."""
        repo = PostgresReservationRepository(db_session)
        assert repo.find_by_id(uuid4()) is None

    def test_find_by_user_id(self, db_session) -> None:
        """Test finding reservations by user ID."""
        repo = PostgresReservationRepository(db_session)
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

    def test_find_by_user_id_with_status_filter(self, db_session) -> None:
        """Test finding user reservations with status filter."""
        repo = PostgresReservationRepository(db_session)
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

    def test_find_by_status(self, db_session) -> None:
        """Test finding reservations by status."""
        repo = PostgresReservationRepository(db_session)
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

        confirmed = repo.find_by_status(ReservationStatus.CONFIRMED)
        assert len(confirmed) == 1

    def test_find_by_space_and_time_overlap(self, db_session) -> None:
        """Test finding overlapping reservations."""
        repo = PostgresReservationRepository(db_session)

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

    def test_find_by_space_and_time_no_overlap(self, db_session) -> None:
        """Test finding non-overlapping reservations returns empty."""
        repo = PostgresReservationRepository(db_session)

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

    def test_update(self, db_session) -> None:
        """Test updating a reservation status."""
        repo = PostgresReservationRepository(db_session)
        reservation = Reservation(
            user_id=uuid4(),
            space_id="A1",
            time_slot=TimeSlot(
                start_time=datetime(2024, 1, 15, 9, 0),
                end_time=datetime(2024, 1, 15, 11, 0),
            ),
        )
        saved = repo.save(reservation)

        # Approve via domain model and update in DB
        saved.approve("Approved")
        repo.update(saved)

        found = repo.find_by_id(saved.reservation_id)
        assert found is not None
        assert found.status == ReservationStatus.CONFIRMED
        assert found.admin_notes == "Approved"

    def test_delete(self, db_session) -> None:
        """Test deleting a reservation."""
        repo = PostgresReservationRepository(db_session)
        reservation = Reservation(
            user_id=uuid4(),
            space_id="A1",
            time_slot=TimeSlot(
                start_time=datetime(2024, 1, 15, 9, 0),
                end_time=datetime(2024, 1, 15, 11, 0),
            ),
        )
        saved = repo.save(reservation)
        repo.delete(saved.reservation_id)

        assert repo.find_by_id(saved.reservation_id) is None

    def test_time_slot_roundtrip(self, db_session) -> None:
        """Test that TimeSlot values survive the DB roundtrip accurately."""
        repo = PostgresReservationRepository(db_session)
        original_start = datetime(2024, 6, 15, 14, 30)
        original_end = datetime(2024, 6, 15, 18, 0)

        reservation = Reservation(
            user_id=uuid4(),
            space_id="C1",
            time_slot=TimeSlot(
                start_time=original_start,
                end_time=original_end,
            ),
        )
        saved = repo.save(reservation)
        found = repo.find_by_id(saved.reservation_id)

        assert found is not None
        assert found.time_slot.start_time == original_start
        assert found.time_slot.end_time == original_end
        assert found.time_slot.duration_hours == 3.5


@pytest.mark.integration
class TestPostgresParkingSpaceRepository:
    """Integration tests for PostgresParkingSpaceRepository."""

    def test_save_and_find_by_id(self, db_session) -> None:
        """Test saving and retrieving a parking space."""
        repo = PostgresParkingSpaceRepository(db_session)
        space = ParkingSpace(space_id="A1", location="Level 1")

        repo.save(space)
        found = repo.find_by_id("A1")

        assert found is not None
        assert found.space_id == "A1"
        assert found.location == "Level 1"

    def test_find_by_id_not_found(self, db_session) -> None:
        """Test finding a non-existent space returns None."""
        repo = PostgresParkingSpaceRepository(db_session)
        assert repo.find_by_id("NONEXISTENT") is None

    def test_find_all(self, db_session) -> None:
        """Test finding all parking spaces."""
        repo = PostgresParkingSpaceRepository(db_session)
        repo.save(ParkingSpace(space_id="A1", location="Level 1"))
        repo.save(ParkingSpace(space_id="A2", location="Level 1"))

        assert len(repo.find_all()) == 2

    def test_find_available(self, db_session) -> None:
        """Test finding available parking spaces."""
        repo = PostgresParkingSpaceRepository(db_session)
        repo.save(ParkingSpace(space_id="A1", location="Level 1", is_available=True))
        repo.save(ParkingSpace(space_id="A2", location="Level 1", is_available=False))

        available = repo.find_available()
        assert len(available) == 1
        assert available[0].space_id == "A1"

    def test_update(self, db_session) -> None:
        """Test updating a parking space."""
        repo = PostgresParkingSpaceRepository(db_session)
        repo.save(
            ParkingSpace(
                space_id="A1",
                location="Level 1",
                hourly_rate=5.0,
            )
        )

        updated_space = ParkingSpace(
            space_id="A1",
            location="Level 1 - Updated",
            hourly_rate=10.0,
        )
        repo.update(updated_space)

        found = repo.find_by_id("A1")
        assert found is not None
        assert found.location == "Level 1 - Updated"
        assert found.hourly_rate == 10.0

    def test_delete(self, db_session) -> None:
        """Test deleting a parking space."""
        repo = PostgresParkingSpaceRepository(db_session)
        repo.save(ParkingSpace(space_id="A1", location="Level 1"))
        repo.delete("A1")

        assert repo.find_by_id("A1") is None

    def test_space_types_and_rates(self, db_session) -> None:
        """Test that space types and hourly rates persist correctly."""
        repo = PostgresParkingSpaceRepository(db_session)
        repo.save(
            ParkingSpace(
                space_id="B1",
                location="Level 1, Section B",
                hourly_rate=7.0,
                space_type="electric",
            )
        )
        repo.save(
            ParkingSpace(
                space_id="D1",
                location="Level 2, Section D",
                hourly_rate=6.0,
                space_type="handicap",
            )
        )

        b1 = repo.find_by_id("B1")
        d1 = repo.find_by_id("D1")

        assert b1 is not None
        assert b1.space_type == "electric"
        assert b1.hourly_rate == 7.0

        assert d1 is not None
        assert d1.space_type == "handicap"
        assert d1.hourly_rate == 6.0


@pytest.mark.integration
class TestPostgresUserRepository:
    """Integration tests for PostgresUserRepository."""

    def test_save_and_find_by_id(self, db_session) -> None:
        """Test saving and retrieving a user."""
        repo = PostgresUserRepository(db_session)
        user = User(username="testuser", email="test@test.com")

        repo.save(user)
        found = repo.find_by_id(user.user_id)

        assert found is not None
        assert found.username == "testuser"
        assert found.email == "test@test.com"

    def test_find_by_id_not_found(self, db_session) -> None:
        """Test finding a non-existent user returns None."""
        repo = PostgresUserRepository(db_session)
        assert repo.find_by_id(uuid4()) is None

    def test_find_by_username(self, db_session) -> None:
        """Test finding a user by username."""
        repo = PostgresUserRepository(db_session)
        user = User(username="testuser", email="test@test.com")
        repo.save(user)

        found = repo.find_by_username("testuser")
        assert found is not None
        assert found.user_id == user.user_id

    def test_find_by_username_not_found(self, db_session) -> None:
        """Test finding a non-existent username returns None."""
        repo = PostgresUserRepository(db_session)
        assert repo.find_by_username("nobody") is None

    def test_user_role_roundtrip(self, db_session) -> None:
        """Test that user role enum survives the DB roundtrip."""
        repo = PostgresUserRepository(db_session)
        admin = User(
            username="admin",
            email="admin@test.com",
            role=UserRole.ADMIN,
            full_name="Admin User",
        )
        repo.save(admin)

        found = repo.find_by_username("admin")
        assert found is not None
        assert found.role == UserRole.ADMIN
        assert found.full_name == "Admin User"
