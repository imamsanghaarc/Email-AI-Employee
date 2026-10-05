"""Runtime configuration.

Everything is read from the environment with the ``AI_EMPLOYEE_`` prefix so a
single Cloud Run service's env config drives all of it. Nothing here has a
usable default for secrets: a missing master key is a hard startup failure
rather than a silent downgrade to plaintext.
"""

from __future__ import annotations

import base64
import functools
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AI_EMPLOYEE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["local", "staging", "production"] = "local"

    master_key: SecretStr = Field(
        default=SecretStr(""),
        description="base64-encoded 32 bytes. Required outside local development.",
    )
    jwt_secret: SecretStr = Field(default=SecretStr(""))
    session_ttl_seconds: int = 60 * 60 * 12

    supabase_url: str = ""
    supabase_service_key: SecretStr = Field(default=SecretStr(""))

    static_token: str = Field(
        default="",
        description=(
            "Bearer token accepted instead of a JWT, for stdio local development and "
            "single-user smoke tests. Must be paired with static_user_id."
        ),
    )
    static_user_id: str = Field(
        default="",
        description="User id that static_token authenticates as. Empty disables it.",
    )

    require_approval_for_side_effects: bool = True
    approval_timeout_seconds: int = 60 * 60
    login_max_attempts: int = 8
    login_window_seconds: int = 15 * 60

    host: str = "127.0.0.1"  # Cloud Run sets BIND_HOST if needed; localhost safe by default
    port: int = 8080

    odoo_default_url: str = "http://localhost:8069"

    @field_validator("master_key")
    @classmethod
    def _validate_master_key(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if not raw:
            return value
        try:
            decoded = base64.b64decode(raw, validate=True)
        except Exception as exc:
            raise ValueError("AI_EMPLOYEE_MASTER_KEY must be valid base64") from exc
        if len(decoded) != 32:
            raise ValueError(
                f"AI_EMPLOYEE_MASTER_KEY must decode to exactly 32 bytes, got {len(decoded)}"
            )
        return value

    def resolved_master_key(self) -> bytes:
        raw = self.master_key.get_secret_value()
        if not raw:
            raise RuntimeError(
                "AI_EMPLOYEE_MASTER_KEY is not set. Generate one with "
                "`python -m ai_employee_mcp keygen`. Refusing to start with "
                "credentials stored unencrypted."
            )
        return base64.b64decode(raw)

    def resolved_jwt_secret(self) -> str:
        raw = self.jwt_secret.get_secret_value()
        if raw:
            return raw
        if self.environment == "production":
            raise RuntimeError("AI_EMPLOYEE_JWT_SECRET is required in production")
        master = self.master_key.get_secret_value()
        if master:
            return master
        raise RuntimeError("AI_EMPLOYEE_JWT_SECRET is not set")

    def is_local(self) -> bool:
        return self.environment == "local"


@functools.lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()