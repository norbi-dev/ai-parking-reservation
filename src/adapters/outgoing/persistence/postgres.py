"""PostgreSQL repository implementations using SQLModel.

These adapters implement the same Protocol interfaces as the in-memory
repositories, converting between domain models and SQLModel DB models.
"""

from uuid import UUID

from loguru import logger
from sqlmodel import Session, select

from src.adapters.outgoing.persistence.models import (
    ParkingSpaceDB,
    ReservationDB,
    UserDB,
)
from src.core.domain.models import (
    ParkingSpace,
    Reservation,
    ReservationStatus,
    TimeSlot,
    User,
    UserRole,
)


class PostgresReservationRepository:
    """PostgreSQL implementation of ReservationRepository.

    Stores reservations in PostgreSQL using SQLModel.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, reservation: Reservation) -> Reservation:
        """Save a reservation to the database.

        Args:
            reservation: Reservation to save

        Returns:
            The saved reservation
        """
        logger.debug("PostgresDB: save reservation={}", reservation.reservation_id)
        db_model = self._to_db(reservation)
        self._session.add(db_model)
        self._session.commit()
        self._session.refresh(db_model)
        logger.debug("PostgresDB: reservation {} saved", reservation.reservation_id)
        return self._to_domain(db_model)

    def find_by_id(self, reservation_id: UUID) -> Reservation | None:
        """Find a reservation by its ID.

        Args:
            reservation_id: Reservation identifier

        Returns:
            The reservation if found, None otherwise
        """
        logger.debug("PostgresDB: find reservation by id={}", reservation_id)
        db_model = self._session.get(ReservationDB, reservation_id)
        if db_model is None:
            logger.debug("PostgresDB: reservation {} not found", reservation_id)
            return None
        return self._to_domain(db_model)

    def find_by_user_id(
        self, user_id: UUID, status: ReservationStatus | None = None
    ) -> list[Reservation]:
        """Find all reservations for a user.

        Args:
            user_id: User identifier
            status: Optional status filter

        Returns:
            List of matching reservations
        """
        logger.debug("PostgresDB: find reservations by user={}", user_id)
        statement = select(ReservationDB).where(ReservationDB.user_id == user_id)
        if status is not None:
            statement = statement.where(ReservationDB.status == status.value)
        results = self._session.exec(statement).all()
        logger.debug(
            "PostgresDB: found {} reservation(s) for user={}",
            len(results),
            user_id,
        )
        return [self._to_domain(r) for r in results]

    def find_by_status(self, status: ReservationStatus) -> list[Reservation]:
        """Find all reservations with a given status.

        Args:
            status: Status to filter by

        Returns:
            List of matching reservations
        """
        logger.debug("PostgresDB: find reservations by status={}", status.value)
        statement = select(ReservationDB).where(ReservationDB.status == status.value)
        results = self._session.exec(statement).all()
        logger.debug(
            "PostgresDB: found {} reservation(s) with status={}",
            len(results),
            status.value,
        )
        return [self._to_domain(r) for r in results]

    def find_by_space_and_time(
        self, space_id: str, time_slot: TimeSlot
    ) -> list[Reservation]:
        """Find reservations that overlap with the given space and time slot.

        Uses SQL-level overlap detection:
        slot1.start < slot2.end AND slot2.start < slot1.end

        Args:
            space_id: Parking space identifier
            time_slot: Time period to check

        Returns:
            List of overlapping reservations
        """
        logger.debug(
            "PostgresDB: find overlapping reservations space={}, slot={}–{}",
            space_id,
            time_slot.start_time,
            time_slot.end_time,
        )
        statement = select(ReservationDB).where(
            ReservationDB.space_id == space_id,
            ReservationDB.start_time < time_slot.end_time,
            ReservationDB.end_time > time_slot.start_time,
        )
        results = self._session.exec(statement).all()
        logger.debug("PostgresDB: found {} overlapping reservation(s)", len(results))
        return [self._to_domain(r) for r in results]

    def update(self, reservation: Reservation) -> Reservation:
        """Update an existing reservation.

        Args:
            reservation: Reservation with updated data

        Returns:
            The updated reservation
        """
        logger.debug("PostgresDB: update reservation={}", reservation.reservation_id)
        db_model = self._session.get(ReservationDB, reservation.reservation_id)
        if db_model is None:
            logger.debug(
                "PostgresDB: reservation {} not found for update, inserting",
                reservation.reservation_id,
            )
            # If not found, save as new (upsert behavior)
            return self.save(reservation)

        db_model.user_id = reservation.user_id
        db_model.space_id = reservation.space_id
        db_model.start_time = reservation.time_slot.start_time
        db_model.end_time = reservation.time_slot.end_time
        db_model.status = reservation.status.value
        db_model.created_at = reservation.created_at
        db_model.updated_at = reservation.updated_at
        db_model.admin_notes = reservation.admin_notes

        self._session.add(db_model)
        self._session.commit()
        self._session.refresh(db_model)
        logger.debug("PostgresDB: reservation {} updated", reservation.reservation_id)
        return self._to_domain(db_model)

    def delete(self, reservation_id: UUID) -> None:
        """Delete a reservation.

        Args:
            reservation_id: Reservation identifier
        """
        logger.debug("PostgresDB: delete reservation={}", reservation_id)
        db_model = self._session.get(ReservationDB, reservation_id)
        if db_model is not None:
            self._session.delete(db_model)
            self._session.commit()
            logger.debug("PostgresDB: reservation {} deleted", reservation_id)
        else:
            logger.debug(
                "PostgresDB: reservation {} not found for deletion",
                reservation_id,
            )

    @staticmethod
    def _to_db(reservation: Reservation) -> ReservationDB:
        """Convert a domain Reservation to a DB model.

        Args:
            reservation: Domain reservation

        Returns:
            Database reservation model
        """
        return ReservationDB(
            reservation_id=reservation.reservation_id,
            user_id=reservation.user_id,
            space_id=reservation.space_id,
            start_time=reservation.time_slot.start_time,
            end_time=reservation.time_slot.end_time,
            status=reservation.status.value,
            created_at=reservation.created_at,
            updated_at=reservation.updated_at,
            admin_notes=reservation.admin_notes,
        )

    @staticmethod
    def _to_domain(db_model: ReservationDB) -> Reservation:
        """Convert a DB model to a domain Reservation.

        Args:
            db_model: Database reservation model

        Returns:
            Domain reservation
        """
        reservation = Reservation.__new__(Reservation)
        reservation.reservation_id = db_model.reservation_id
        reservation.user_id = db_model.user_id
        reservation.space_id = db_model.space_id
        reservation.time_slot = TimeSlot(
            start_time=db_model.start_time,
            end_time=db_model.end_time,
        )
        reservation.status = ReservationStatus(db_model.status)
        reservation.created_at = db_model.created_at
        reservation.updated_at = db_model.updated_at
        reservation.admin_notes = db_model.admin_notes
        return reservation


class PostgresParkingSpaceRepository:
    """PostgreSQL implementation of ParkingSpaceRepository.

    Stores parking spaces in PostgreSQL using SQLModel.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, space: ParkingSpace) -> ParkingSpace:
        """Save a parking space to the database.

        Args:
            space: Parking space to save

        Returns:
            The saved parking space
        """
        logger.debug("PostgresDB: save space={}", space.space_id)
        db_model = self._to_db(space)
        self._session.merge(db_model)
        self._session.commit()
        logger.debug("PostgresDB: space {} saved", space.space_id)
        return space

    def find_by_id(self, space_id: str) -> ParkingSpace | None:
        """Find a parking space by its ID.

        Args:
            space_id: Space identifier

        Returns:
            The parking space if found, None otherwise
        """
        logger.debug("PostgresDB: find space by id={}", space_id)
        db_model = self._session.get(ParkingSpaceDB, space_id)
        if db_model is None:
            logger.debug("PostgresDB: space {} not found", space_id)
            return None
        return self._to_domain(db_model)

    def find_all(self) -> list[ParkingSpace]:
        """Find all parking spaces.

        Returns:
            List of all parking spaces
        """
        logger.debug("PostgresDB: find_all spaces")
        results = self._session.exec(select(ParkingSpaceDB)).all()
        logger.debug("PostgresDB: found {} space(s)", len(results))
        return [self._to_domain(s) for s in results]

    def find_available(self) -> list[ParkingSpace]:
        """Find all available parking spaces.

        Returns:
            List of available parking spaces
        """
        logger.debug("PostgresDB: find_available spaces")
        statement = select(ParkingSpaceDB).where(
            ParkingSpaceDB.is_available == True  # noqa: E712
        )
        results = self._session.exec(statement).all()
        logger.debug("PostgresDB: found {} available space(s)", len(results))
        return [self._to_domain(s) for s in results]

    def update(self, space: ParkingSpace) -> ParkingSpace:
        """Update a parking space.

        Args:
            space: Parking space with updated data

        Returns:
            The updated parking space
        """
        logger.debug("PostgresDB: update space={}", space.space_id)
        db_model = self._session.get(ParkingSpaceDB, space.space_id)
        if db_model is None:
            logger.debug(
                "PostgresDB: space {} not found for update, inserting",
                space.space_id,
            )
            return self.save(space)

        db_model.location = space.location
        db_model.is_available = space.is_available
        db_model.hourly_rate = space.hourly_rate
        db_model.space_type = space.space_type

        self._session.add(db_model)
        self._session.commit()
        self._session.refresh(db_model)
        logger.debug("PostgresDB: space {} updated", space.space_id)
        return self._to_domain(db_model)

    def delete(self, space_id: str) -> None:
        """Delete a parking space.

        Args:
            space_id: Space identifier
        """
        logger.debug("PostgresDB: delete space={}", space_id)
        db_model = self._session.get(ParkingSpaceDB, space_id)
        if db_model is not None:
            self._session.delete(db_model)
            self._session.commit()
            logger.debug("PostgresDB: space {} deleted", space_id)
        else:
            logger.debug("PostgresDB: space {} not found for deletion", space_id)

    @staticmethod
    def _to_db(space: ParkingSpace) -> ParkingSpaceDB:
        """Convert a domain ParkingSpace to a DB model.

        Args:
            space: Domain parking space

        Returns:
            Database parking space model
        """
        return ParkingSpaceDB(
            space_id=space.space_id,
            location=space.location,
            is_available=space.is_available,
            hourly_rate=space.hourly_rate,
            space_type=space.space_type,
        )

    @staticmethod
    def _to_domain(db_model: ParkingSpaceDB) -> ParkingSpace:
        """Convert a DB model to a domain ParkingSpace.

        Args:
            db_model: Database parking space model

        Returns:
            Domain parking space
        """
        return ParkingSpace(
            space_id=db_model.space_id,
            location=db_model.location,
            is_available=db_model.is_available,
            hourly_rate=db_model.hourly_rate,
            space_type=db_model.space_type,
        )


class PostgresUserRepository:
    """PostgreSQL implementation of UserRepository.

    Stores users in PostgreSQL using SQLModel.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, user: User) -> User:
        """Save a user to the database.

        Args:
            user: User to save

        Returns:
            The saved user
        """
        logger.debug("PostgresDB: save user={}", user.user_id)
        db_model = self._to_db(user)
        self._session.merge(db_model)
        self._session.commit()
        logger.debug("PostgresDB: user {} saved", user.user_id)
        return user

    def find_by_id(self, user_id: UUID) -> User | None:
        """Find a user by ID.

        Args:
            user_id: User identifier

        Returns:
            The user if found, None otherwise
        """
        logger.debug("PostgresDB: find user by id={}", user_id)
        db_model = self._session.get(UserDB, user_id)
        if db_model is None:
            logger.debug("PostgresDB: user {} not found", user_id)
            return None
        return self._to_domain(db_model)

    def find_by_username(self, username: str) -> User | None:
        """Find a user by username.

        Args:
            username: Username to search for

        Returns:
            The user if found, None otherwise
        """
        logger.debug("PostgresDB: find user by username={}", username)
        statement = select(UserDB).where(UserDB.username == username)
        db_model = self._session.exec(statement).first()
        if db_model is None:
            logger.debug("PostgresDB: user '{}' not found", username)
            return None
        return self._to_domain(db_model)

    @staticmethod
    def _to_db(user: User) -> UserDB:
        """Convert a domain User to a DB model.

        Args:
            user: Domain user

        Returns:
            Database user model
        """
        return UserDB(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            full_name=user.full_name,
        )

    @staticmethod
    def _to_domain(db_model: UserDB) -> User:
        """Convert a DB model to a domain User.

        Args:
            db_model: Database user model

        Returns:
            Domain user
        """
        return User(
            user_id=db_model.user_id,
            username=db_model.username,
            email=db_model.email,
            role=UserRole(db_model.role),
            full_name=db_model.full_name,
        )
