from functools import lru_cache
from typing import Optional

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _env_bool(var_name: str, default: bool = False) -> bool:
    """Return boolean interpretation of an environment variable."""
    value = os.getenv(var_name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "on"}


def _env_int(var_name: str, default: int) -> int:
    """Parse integer environment variables safely."""
    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(var_name: str, default: float) -> float:
    """Parse float environment variables safely."""
    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


class Settings(BaseModel):
    """Application configuration loaded from environment variables."""

    app_name: str = Field(default="AI Gateway")
    version: str = Field(default="0.1.0")
    environment: str = Field(default_factory=lambda: os.getenv("APP_ENV", "local"))

    BANK_NAME: Optional[str] = Field(
        default_factory=lambda: os.getenv("BANK_NAME")
    )

    azure_openai_endpoint: Optional[str] = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    azure_openai_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_API_KEY")
    )
    azure_openai_deployment: Optional[str] = Field(
        default_factory=lambda: os.getenv("AZURE_OPENAI_DEPLOYMENT")
    )
    azure_openai_max_retries: int = Field(
        default_factory=lambda: _env_int("AZURE_OPENAI_MAX_RETRIES", 2),
        description="Number of times to retry Azure OpenAI calls after failures.",
    )
    azure_openai_retry_base_delay: float = Field(
        default_factory=lambda: _env_float("AZURE_OPENAI_RETRY_BASE_DELAY", 0.5),
        description="Base backoff delay (seconds) for Azure OpenAI retries.",
    )
    azure_openai_retry_max_delay: float = Field(
        default_factory=lambda: _env_float("AZURE_OPENAI_RETRY_MAX_DELAY", 8.0),
        description="Maximum backoff delay (seconds) for Azure OpenAI retries.",
    )

    chatbot_api_base_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("CHATBOT_API_BASE_URL")
    )

    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
        description="Root logger level.",
    )
    log_json: bool = Field(
        default_factory=lambda: _env_bool("LOG_JSON", False),
        description="Toggle JSON log formatting.",
    )
    request_id_header: str = Field(
        default_factory=lambda: os.getenv("REQUEST_ID_HEADER", "X-Request-ID"),
        description="HTTP header carrying correlation IDs.",
    )
    trust_client_ip_header: bool = Field(
        default_factory=lambda: _env_bool("TRUST_CLIENT_IP_HEADER", False),
        description="Trust forwarded client IP header when extracting remote address.",
    )
    client_ip_header: str = Field(
        default_factory=lambda: os.getenv("CLIENT_IP_HEADER", "X-Forwarded-For"),
        description="Header containing original client IP when behind proxies.",
    )
    log_file_path: str = Field(
        default_factory=lambda: os.getenv(
            "LOG_FILE_PATH", str(PROJECT_ROOT / "logs" / "app.log")
        ),
        description="Path to the rotating log file.",
    )
    log_file_max_bytes: int = Field(
        default_factory=lambda: _env_int("LOG_FILE_MAX_BYTES", 5 * 1024 * 1024),
        description="Maximum size in bytes before the log file rotates.",
    )
    log_file_backup_count: int = Field(
        default_factory=lambda: _env_int("LOG_FILE_BACKUP_COUNT", 5),
        description="Number of rotated log files to retain.",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
