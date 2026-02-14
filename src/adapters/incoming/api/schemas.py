"""Pydantic models for API request/response serialization."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TimeSlotRequest(BaseModel):
    """Request model for a time slot."""

    start_time: datetime = Field(description="Start of the reservation period")
    end_time: datetime = Field(description="End of the reservation period")


class CreateReservationRequest(BaseModel):
    """Request model for creating a reservation."""

    user_id: UUID = Field(description="User making the reservation")
    space_id: str = Field(description="Parking space identifier")
    time_slot: TimeSlotRequest = Field(description="Requested time period")


class AdminActionRequest(BaseModel):
    """Request model for admin approval/rejection."""

    admin_notes: str = Field(
        default="", description="Optional notes from the administrator"
    )


class ReservationResponse(BaseModel):
    """Response model for a reservation."""

    reservation_id: UUID
    user_id: UUID
    space_id: str
    status: str
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime
    admin_notes: str

    model_config = {"from_attributes": True}


class ParkingSpaceResponse(BaseModel):
    """Response model for a parking space."""

    space_id: str
    location: str
    is_available: bool
    hourly_rate: float
    space_type: str

    model_config = {"from_attributes": True}


class ParkingSpaceRequest(BaseModel):
    """Request model for creating/updating a parking space."""

    space_id: str = Field(description="Unique space identifier")
    location: str = Field(description="Physical location description")
    is_available: bool = Field(
        default=True, description="Whether the space is available"
    )
    hourly_rate: float = Field(default=5.0, description="Cost per hour")
    space_type: str = Field(default="standard", description="Type of parking space")


class AvailabilityRequest(BaseModel):
    """Request model for checking availability."""

    time_slot: TimeSlotRequest = Field(description="Time period to check")


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: str = Field(description="Message role: 'user' or 'assistant'")
    content: str = Field(description="Message content")


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""

    message: str = Field(description="User's message to the chatbot")
    user_id: UUID = Field(description="User making the request")
    user_role: str = Field(
        default="client",
        description="User role: 'client' or 'admin'",
    )
    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous messages in the conversation for context",
    )


class ChatResponse(BaseModel):
    """Response model for the chat endpoint."""

    response: str = Field(description="Chatbot's response message")
    user_id: UUID = Field(description="User who made the request")
