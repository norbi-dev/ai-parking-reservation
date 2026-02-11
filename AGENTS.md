# Agent Development Guide

Essential information for AI coding agents working in this repository.

> **💡 Agent Skills Available:** Check `.opencode/skills/` for step-by-step procedures for common tasks.
> - **fix-pre-commit** - Fix code quality issues before committing (run after implementations)
> - Load skills using: `skill({ name: "fix-pre-commit" })`

## Project Overview

**Parking Reservation Chatbot** - Python app using Hexagonal Architecture (Ports & Adapters) for conversational parking space reservations with LLM-powered chatbot, human-in-the-loop approval, and vector-based static data retrieval.

- **Architecture**: Hexagonal/Clean Architecture with DDD principles
- **Language**: Python 3.14
- **Stack**: LangGraph, Streamlit, FastAPI, PostgreSQL, pgvector
- **Package Manager**: `uv`

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
mypy src/                                 # Type checking
ruff check --fix .                        # Linting/formatting
```

## Architecture Structure

```
src/
├── core/                     # BUSINESS LOGIC (framework-agnostic)
│   ├── domain/              # Models, value objects, exceptions
│   ├── ports/incoming/      # Use case interfaces (Primary Ports)
│   ├── ports/outgoing/      # Infrastructure interfaces (Secondary Ports)
│   └── usecases/            # Application orchestration
├── adapters/
│   ├── incoming/            # UI/API (Streamlit, FastAPI)
│   └── outgoing/            # Infrastructure (LLM, DB, i18n)
└── config/                  # Settings & dependency injection
```

**Key Principles:**
1. Core is pure (ZERO framework deps)
2. Dependencies point inward (adapters → ports → core)
3. Use `Protocol` classes for interfaces, not ABCs
4. Simple DI via factory functions in `src/config/dependencies.py`

## Code Style

### Imports (stdlib → third-party → local)
```python
import os
from typing import Protocol, Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

from src.core.domain.models import Reservation
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
class SpaceNotAvailableError(DomainException):
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
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=postgresql://...          # PostgreSQL for dynamic data
OPENAI_API_KEY=sk-...                  # Optional, for embeddings (pgvector)
MAX_RESERVATION_DAYS=30                # Maximum days in advance
ADMIN_APPROVAL_REQUIRED=true           # Enable human-in-the-loop
```

## Common Tasks

**Add Use Case:** Port interface in `ports/incoming/` → Implement in `usecases/` → Create factory function in `config/dependencies.py` → Use in adapter

**Add Adapter:** Create in `adapters/` → Implement port Protocol → Add factory function if needed → Test

**Add LangGraph Node:** Define node function → Add to StateGraph → Wire state transitions → Test with mock state

**Add Static Data:** Update vector DB → Test retrieval in chatbot context → Verify RAG pipeline integration

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
- **Run fix-pre-commit skill** - Always run `skill({ name: "fix-pre-commit" })` after implementation tasks

## Documentation

All project documentation is organized in the `docs/` directory:
- `docs/architecture/` - System architecture and design
- `docs/development/` - Development guidelines and tools
- `docs/guides/` - User and developer guides
- See `docs/README.md` for full documentation index
