"""Dependency injection using simple factory functions with caching.

All dependencies are cached automatically using @lru_cache.
When USE_POSTGRES=true, PostgreSQL repositories are used; otherwise in-memory.
"""

import os
from functools import lru_cache
from typing import Any
from uuid import UUID

from loguru import logger

from src.adapters.outgoing.persistence.in_memory import (
    InMemoryConversationSessionRepository,
    InMemoryParkingSpaceRepository,
    InMemoryReservationRepository,
    InMemoryUserRepository,
)
from src.config.settings import Settings
from src.core.domain.models import ParkingSpace, UserRole
from src.core.ports.outgoing.repositories import (
    ConversationSessionRepository,
    ParkingSpaceRepository,
    ReservationRepository,
    UserRepository,
)
from src.core.usecases.admin_approval import AdminApprovalService
from src.core.usecases.chat_conversation import ChatConversationService
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
    settings = Settings()
    logger.info(
        "Settings loaded: local_mode={}, use_postgres={}",
        settings.local_mode,
        settings.use_postgres,
    )
    return settings


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
    logger.debug("Creating database session for PostgreSQL")
    create_tables(settings.database_url)
    engine = create_db_engine(settings.database_url)
    session = Session(engine)
    logger.info("Database session created")
    return session


@lru_cache
def get_reservation_repository() -> ReservationRepository:
    """Get reservation repository (cached).

    Uses PostgreSQL when USE_POSTGRES=true, otherwise in-memory.

    Returns:
        Reservation repository instance
    """
    settings = get_settings()
    if settings.use_postgres:
        logger.debug("Using PostgreSQL reservation repository")
        from src.adapters.outgoing.persistence.postgres import (
            PostgresReservationRepository,
        )

        return PostgresReservationRepository(session=_get_db_session())

    logger.debug("Using in-memory reservation repository")
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
        logger.debug("Using PostgreSQL parking space repository")
        from src.adapters.outgoing.persistence.postgres import (
            PostgresParkingSpaceRepository,
        )

        repo: ParkingSpaceRepository = PostgresParkingSpaceRepository(
            session=_get_db_session()
        )
        _seed_parking_spaces(repo)
        return repo

    logger.debug("Using in-memory parking space repository")
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
        logger.debug("Using PostgreSQL user repository")
        from src.adapters.outgoing.persistence.postgres import (
            PostgresUserRepository,
        )

        return PostgresUserRepository(session=_get_db_session())

    logger.debug("Using in-memory user repository")
    return InMemoryUserRepository()


@lru_cache
def get_conversation_session_repository() -> ConversationSessionRepository:
    """Get conversation session repository (cached).

    Currently only supports in-memory storage.
    TODO: Add PostgreSQL implementation for production.

    Returns:
        Conversation session repository instance
    """
    logger.debug("Using in-memory conversation session repository")
    return InMemoryConversationSessionRepository()


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
        logger.debug("Parking spaces already seeded, skipping")
        return

    logger.info("Seeding {} sample parking spaces", 10)

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


def get_chatbot_model_name() -> str:
    """Get the pydantic-ai model name string for the configured LLM.

    For Ollama, sets the OLLAMA_BASE_URL env var (required by pydantic-ai)
    and returns 'ollama:<model_name>'.

    Returns:
        Model name string for pydantic-ai Agent
    """
    settings = get_settings()
    if settings.local_mode:
        # pydantic-ai reads OLLAMA_BASE_URL from the environment
        os.environ.setdefault("OLLAMA_BASE_URL", settings.ollama_base_url)
        model = f"ollama:{settings.ollama_model}"
    else:
        model = f"openrouter:{settings.model_name}"
    logger.debug("LLM model resolved: {}", model)
    return model


@lru_cache
def get_parking_agent() -> Any:
    """Get the parking chatbot agent (cached).

    Returns:
        Configured pydantic-ai Agent for parking reservations
    """
    from src.adapters.outgoing.llm.chatbot import create_parking_agent

    model_name = get_chatbot_model_name()
    logger.info("Creating parking chatbot agent with model '{}'", model_name)
    return create_parking_agent(model_name)


def get_chat_deps(user_id: UUID, user_role: UserRole) -> Any:
    """Create ChatDeps for a specific user session.

    Args:
        user_id: Current user's UUID
        user_role: Current user's role

    Returns:
        ChatDeps instance wired with all use cases
    """
    from src.adapters.outgoing.llm.chatbot import ChatDeps

    logger.debug("Creating ChatDeps: user={}, role={}", user_id, user_role.value)
    return ChatDeps(
        user_id=user_id,
        user_role=user_role,
        reserve_parking=get_reserve_parking_usecase(),
        check_availability=get_check_availability_usecase(),
        manage_reservations=get_manage_reservations_usecase(),
        admin_approval=get_admin_approval_usecase(),
        manage_spaces=get_manage_parking_spaces_usecase(),
    )


@lru_cache
def get_chat_conversation_service() -> ChatConversationService:
    """Get chat conversation service (cached).

    Returns:
        ChatConversationService wired with agent and session repository
    """
    logger.debug("Creating chat conversation service")
    return ChatConversationService(
        session_repo=get_conversation_session_repository(),
        agent=get_parking_agent(),
    )
