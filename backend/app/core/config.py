"""App settings, read from environment / backend/.env."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent  # backend/ (local), ~/todo/ (PROD)

# to distinguish PROD vs. Local
PATH_ON_WEBSERVER = Path("/home/entorb/todo")


class Settings(BaseSettings):
    """Typed settings, validated at startup."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_ignore_empty=True, extra="ignore"
    )

    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_expire_hours: int = 24
    db_path: Path = BASE_DIR / "sqlite.db"
    env: Literal["PROD", "Local"] = "PROD" if PATH_ON_WEBSERVER.is_dir() else "Local"

    @property
    def cors_origins(self) -> list[str]:
        """Allowed frontend origins."""
        if self.env == "PROD":
            return ["https://entorb.net"]
        return ["http://localhost:4173", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()  # type: ignore[call-arg]
