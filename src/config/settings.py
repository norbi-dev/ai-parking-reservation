"""Application settings using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Attributes:
        local_mode: Use Ollama (true) or OpenRouter (false)
        openrouter_api_key: API key for OpenRouter
        model_name: Model name for remote mode
        ollama_model: Model name for local Ollama
        ollama_base_url: Base URL for Ollama API
        database_url: PostgreSQL connection string
        use_postgres: Use PostgreSQL repos (true) or in-memory (false)
        openai_api_key: API key for OpenAI embeddings
        max_reservation_days: Maximum days in advance for reservations
        admin_approval_required: Enable human-in-the-loop approval
        api_host: FastAPI server host
        api_port: FastAPI server port
    """

    local_mode: bool = True
    openrouter_api_key: str = ""
    model_name: str = "google/gemini-flash-1.5"
    ollama_model: str = "gpt-oss:20b"
    ollama_base_url: str = "http://localhost:11434/v1"
    database_url: str = (
        "postgresql://parkinguser:parkingpass@localhost:5432/parkingreservation"
    )
    use_postgres: bool = False
    openai_api_key: str = ""
    max_reservation_days: int = 30
    admin_approval_required: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
