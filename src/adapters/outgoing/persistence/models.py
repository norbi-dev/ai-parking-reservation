"""SQLModel database models for PostgreSQL persistence.

These are the persistence-layer representations of domain entities.
Repository adapters convert between these DB models and domain models.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ParkingSpaceDB(SQLModel, table=True):
    """Database table for parking spaces."""

    __tablename__ = "parking_spaces"

    space_id: str = Field(primary_key=True)
    location: str
    is_available: bool = True
    hourly_rate: float = 5.0
    space_type: str = "standard"


class UserDB(SQLModel, table=True):
    """Database table for users."""

    __tablename__ = "users"

    user_id: UUID = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(default="", index=True)
    email: str = ""
    role: str = "client"
    full_name: str = ""


class ReservationDB(SQLModel, table=True):
    """Database table for reservations."""

    __tablename__ = "reservations"

    reservation_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True)
    space_id: str = Field(index=True)
    start_time: datetime
    end_time: datetime
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    admin_notes: str = ""
