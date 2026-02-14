# Agent Development Guide

Essential information for AI coding agents working in this repository.

> **📖 Project Context:** See `llm.txt` in the project root for a comprehensive reference of all models, APIs, architecture, and file structure.
>
> **💡 Agent Skills Available:** Check `.opencode/skills/` for step-by-step procedures for common tasks.
> - **fix-lint** - Fix linting, formatting, and unused imports (run after implementations)
> - **update-llm-txt** - Update `llm.txt` after implementing changes (run after any structural/API/model changes)
> - Load skills using: `skill({ name: "fix-lint" })` or `skill({ name: "update-llm-txt" })`

## Project Overview

**Parking Reservation Chatbot** - Python app using Hexagonal Architecture (Ports & Adapters) for conversational parking space reservations with LLM-powered chatbot, human-in-the-loop approval, and backend-managed conversation memory.

- **Architecture**: Hexagonal/Clean Architecture with DDD principles
- **Language**: Python 3.13
- **Stack**: Pydantic AI, Streamlit, FastAPI, SQLModel, PostgreSQL, pgvector
- **Package Manager**: `uv`
- **State Management**: Backend-managed conversation sessions (separation of concerns)

## Quick Commands

### Dependencies & Running
```bash
uv sync                                    # Install dependencies
uv run streamlit run main.py              # Run Streamlit UI
uv run python main_api.py                 # Run REST API (needs PostgreSQL)
podman-compose up -d                      # Start PostgreSQL
```

### Testing
```bash
uv run pytest tests/unit -v              # Unit tests only (PREFERRED - no deps)
uv run pytest -v                          # All tests (needs Ollama)
uv run pytest tests/unit/test_reservation.py::TestReservationService::test_create_reservation_success -v  # Single test
uv run pytest -k "reservation" -v        # Pattern matching
uv run pytest -v -m "not integration"    # Skip integration tests (CI)
```

### Linting
```bash
ruff check --fix . && ruff format .        # Lint + format (or load fix-lint skill)
mypy src/                                 # Type checking
```

## Architecture Structure

```
src/
├── core/                     # BUSINESS LOGIC (framework-agnostic)
│   ├── domain/              # Models, value objects, exceptions
│   │   └── models.py        # Domain entities: Reservation, ParkingSpace, User, ConversationSession
│   ├── ports/incoming/      # Use case interfaces (Primary Ports)
│   ├── ports/outgoing/      # Infrastructure interfaces (Secondary Ports)
│   │   └── repositories.py  # Repository protocols: ReservationRepository, ConversationSessionRepository, etc.
│   └── usecases/            # Application orchestration
│       ├── reserve_parking.py
│       ├── check_availability.py
│       ├── manage_reservations.py
│       ├── admin_approval.py
│       ├── manage_parking_spaces.py
│       └── chat_conversation.py  # Backend conversation memory management
├── adapters/
│   ├── incoming/            # UI/API (Streamlit, FastAPI)
│   │   ├── streamlit_app/   # Frontend - pure presentation layer
│   │   └── api/             # REST API endpoints
│   └── outgoing/            # Infrastructure (LLM, DB, i18n)
│       ├── llm/             # Pydantic AI chatbot agent
│       └── persistence/     # Repository implementations
│           ├── in_memory.py # In-memory repos (dev/test)
│           └── postgres.py  # PostgreSQL repos (production)
└── config/                  # Settings & dependency injection
    └── dependencies.py      # Factory functions for all services
```

**Key Principles:**
1. Core is pure (ZERO framework deps)
2. Dependencies point inward (adapters → ports → core)
3. Use `Protocol` classes for interfaces, not ABCs
4. Simple DI via factory functions in `src/config/dependencies.py`
5. **Backend manages ALL conversation state** - Frontend is stateless

## Code Style

### Imports (stdlib → third-party → local)
```python
import os
from typing import Protocol, Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage

from src.core.domain.models import Reservation, ConversationSession
```

### Type Hints (modern Python 3.10+)
```python
def execute(self, user_id: str, request: str) -> Reservation:  # Always typed
    pass

def get_available_spaces(self) -> list[ParkingSpace]:  # Use list[], not List[]
def find_by_id(id: UUID) -> Reservation | None:        # Use |, not Optional[]

class LLMProvider(Protocol):                # Protocol for interfaces
    def create_llm(self) -> Any: ...
```

### Naming
```python
class ReserveParking:                # Classes: PascalCase
def check_availability(date: str):   # Functions: snake_case
MAX_RESERVATION_DAYS = 30            # Constants: UPPER_SNAKE_CASE
def _validate_time_slot(slot: str):  # Private: _leading_underscore
```

### Models
```python
# Domain: @dataclass
@dataclass
class ParkingSpace:
    space_id: str
    location: str
    is_available: bool

# Value objects: frozen
@dataclass(frozen=True)
class TimeSlot:
    start_time: datetime
    end_time: datetime

# API: Pydantic
class ReservationResponse(BaseModel):
    id: UUID
    space_id: str
    status: str  # pending, confirmed, rejected
    class Config:
        from_attributes = True
```

### Error Handling
```python
# Custom exceptions in src/core/domain/exceptions.py
class SpaceNotAvailableError(DomainError):
    """Raised when parking space is not available."""

# Raise with clear messages
raise SpaceNotAvailableError(f"Space {space_id} not available for {date}")

# Catch and re-raise with context
try:
    result = graph.invoke({"messages": messages})
except Exception as e:
    raise ReservationError(f"Failed to create reservation: {e}") from e
```

### Docstrings
```python
"""Module-level: Brief description."""

class ReserveParking:
    """
    Class-level: Purpose and responsibility.
    
    This orchestrates: check availability → create reservation → await approval → notify user.
    """
    
    def execute(self, user_id: str, space_id: str, time_slot: TimeSlot) -> Reservation:
        """
        Method-level with Args/Returns/Raises.
        
        Args:
            user_id: User making the reservation
            space_id: Parking space identifier
            time_slot: Requested time period
        
        Returns:
            Reservation with ID and pending status
        
        Raises:
            SpaceNotAvailableError: If space is not available
        """
```

### Testing
```python
@pytest.mark.unit  # No external dependencies
class TestReservationService:
    def test_create_reservation_success(self):
        """Test description."""
        # Arrange
        mock_db = MockDatabase()
        mock_graph = MockLangGraph()
        # Act
        result = service.create_reservation(user_id="123", space_id="A1")
        # Assert
        assert result.status == "pending"

@pytest.mark.integration  # Requires Ollama/DB
def test_real_chatbot(): pass

@pytest.fixture
def service():
    return ReservationService(...)
```

## Environment Variables

```bash
LOCAL_MODE=false                        # true=Ollama, false=OpenRouter
OPENROUTER_API_KEY=sk-...              # Remote mode
MODEL_NAME=google/gemini-flash-1.5
OLLAMA_MODEL=llama3.2                  # Local mode
OLLAMA_BASE_URL=http://localhost:11434/v1
DATABASE_URL=postgresql://...          # PostgreSQL for dynamic data
OPENAI_API_KEY=sk-...                  # Optional, for embeddings (pgvector)
MAX_RESERVATION_DAYS=30                # Maximum days in advance
ADMIN_APPROVAL_REQUIRED=true           # Enable human-in-the-loop
```

## Common Tasks

**Add Use Case:** Port interface in `ports/incoming/` → Implement in `usecases/` → Create factory function in `config/dependencies.py` → Use in adapter

**Add Adapter:** Create in `adapters/` → Implement port Protocol → Add factory function if needed → Test

**Add Conversation Memory:** Backend manages all state via `ChatConversationService` → Frontend only stores `backend_session_id` → Never store conversation history in frontend

## Conversation Memory Architecture

### **CRITICAL: Backend-Managed State**

The system follows strict separation of concerns for conversation memory:

**✅ Backend Responsibilities:**
- `ConversationSession` domain model stores message history
- `ConversationSessionRepository` persists sessions
- `ChatConversationService` manages session lifecycle
- All Pydantic AI message history stored and managed server-side

**✅ Frontend Responsibilities:**
- Display messages for UI rendering only
- Send user input to backend
- Store `backend_session_id` reference only
- **NEVER** manage conversation history

**Example - Proper Backend Usage:**
```python
# In use case or adapter
chat_service = dependencies.get_chat_conversation_service()
chat_deps = dependencies.get_chat_deps(user_id, user_role)

# Backend manages all state
session = chat_service.get_or_create_session(session_id, user_id, user_role)
response, _ = await chat_service.send_message(session.session_id, message, chat_deps)
```

**Example - Frontend (Streamlit):**
```python
# Streamlit only stores session reference
if "backend_session_id" not in st.session_state:
    st.session_state.backend_session_id = None  # Created on first message

# Send to backend - backend handles all memory
response = _get_chatbot_response(user_message)
```

**🚫 NEVER DO THIS:**
```python
# ❌ BAD: Don't manage conversation history in frontend
st.session_state.conversation_history = []  # WRONG!
st.session_state.messages = result.all_messages()  # WRONG!
```

## Dependency Injection (Simple!)

We use simple factory functions instead of complex containers:

```python
# Get any use case - simple and clear!
from src.config import dependencies

usecase = dependencies.get_reserve_parking_usecase()
reservation = usecase.execute(user_id, space_id, time_slot)
```

All dependencies are cached automatically using `@lru_cache`. No need for complex container classes!

## Critical Rules

- **Never modify core for adapters** - Core is framework-agnostic
- **Unit tests use mocks** - Mark integration tests with `@pytest.mark.integration`
- **DI over globals** - Constructor injection via container
- **Protocols over ABC** - Structural subtyping preferred
- **Run fix-lint skill** - Always run `skill({ name: "fix-lint" })` after implementation tasks

