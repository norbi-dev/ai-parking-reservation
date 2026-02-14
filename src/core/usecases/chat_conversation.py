"""Use case for managing chat conversations with the LLM agent.

This use case handles conversation session management, ensuring that
conversation history is maintained on the backend rather than the frontend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from loguru import logger

from src.core.domain.models import ConversationSession, UserRole

if TYPE_CHECKING:
    from pydantic_ai import Agent
    from pydantic_ai.messages import ModelMessage

    from src.core.ports.outgoing.repositories import ConversationSessionRepository


class ChatConversationService:
    """Service for managing chat conversations with conversation memory.

    This service ensures separation of concerns by managing all conversation
    state on the backend. The frontend only needs to send messages and receive
    responses, without maintaining any conversation history.

    Attributes:
        session_repo: Repository for storing conversation sessions
        agent: Pydantic AI agent for chat interactions
    """

    def __init__(
        self,
        session_repo: ConversationSessionRepository,
        agent: Agent[Any, str],
    ) -> None:
        self.session_repo = session_repo
        self.agent = agent

    def get_or_create_session(
        self, session_id: UUID | None, user_id: UUID, user_role: UserRole
    ) -> ConversationSession:
        """Get an existing session or create a new one.

        Args:
            session_id: Optional session ID to retrieve
            user_id: User identifier
            user_role: User role (client or admin)

        Returns:
            The conversation session
        """
        if session_id:
            logger.debug(
                "ChatService: retrieving session {} for user {}",
                session_id,
                user_id,
            )
            session = self.session_repo.find_by_id(session_id)
            if session:
                logger.debug(
                    "ChatService: found session with {} messages",
                    len(session.message_history),
                )
                return session
            logger.debug("ChatService: session {} not found, creating new", session_id)

        # Create new session
        session = ConversationSession(user_id=user_id, user_role=user_role)
        self.session_repo.save(session)
        logger.info(
            "ChatService: created new session {} for user {}",
            session.session_id,
            user_id,
        )
        return session

    async def send_message(
        self,
        session_id: UUID,
        user_message: str,
        deps: Any,
    ) -> tuple[str, UUID]:
        """Send a message and get a response, updating conversation history.

        Args:
            session_id: Conversation session identifier
            user_message: User's message text
            deps: Dependencies for the agent (ChatDeps)

        Returns:
            Tuple of (response text, session ID)

        Raises:
            ValueError: If session not found
        """
        logger.debug(
            "ChatService: processing message for session {}, message='{}'",
            session_id,
            user_message[:100],
        )

        # Retrieve session
        session = self.session_repo.find_by_id(session_id)
        if not session:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        # Deserialize message history for Pydantic AI
        from pydantic_ai.messages import ModelMessagesTypeAdapter

        message_history: list[ModelMessage] = []
        if session.message_history:
            try:
                # Use Pydantic AI's TypeAdapter to deserialize messages from JSON bytes
                message_history = ModelMessagesTypeAdapter.validate_json(
                    session.message_history
                )
                logger.debug(
                    "ChatService: loaded {} messages from history",
                    len(message_history),
                )
            except Exception as e:
                logger.warning(
                    "ChatService: failed to deserialize message history: {}", e
                )

        # Run agent with conversation history
        try:
            result = await self.agent.run(
                user_message,
                deps=deps,
                message_history=message_history or None,
            )

            # Serialize and update conversation history using Pydantic AI's method
            session.message_history = result.all_messages_json()
            self.session_repo.update(session)

            logger.debug(
                "ChatService: updated session with {} total messages",
                len(session.message_history),
            )

            return str(result.output), session.session_id

        except Exception as e:
            logger.exception("ChatService: error processing message: {}", e)
            raise

    def clear_session_history(self, session_id: UUID) -> None:
        """Clear all messages from a conversation session.

        Args:
            session_id: Session identifier

        Raises:
            ValueError: If session not found
        """
        logger.debug("ChatService: clearing history for session {}", session_id)
        session = self.session_repo.find_by_id(session_id)
        if not session:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        session.clear_history()
        self.session_repo.update(session)
        logger.info("ChatService: cleared history for session {}", session_id)

    def delete_session(self, session_id: UUID) -> None:
        """Delete a conversation session.

        Args:
            session_id: Session identifier
        """
        logger.debug("ChatService: deleting session {}", session_id)
        self.session_repo.delete(session_id)
        logger.info("ChatService: deleted session {}", session_id)
