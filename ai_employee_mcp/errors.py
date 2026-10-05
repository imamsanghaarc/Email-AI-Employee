"""Public error contracts for AI Employee MCP tools.

Every failure a tool can produce is one of these. The important one is
``CredentialsRequired``: MCP tool calls cannot pause and prompt a human, so a
tool that needs credentials it does not have must hand the agent a structured
instruction it can act on.
"""

from __future__ import annotations

from typing import Any

STATUS_OK = "ok"
STATUS_ERROR = "error"
STATUS_CREDENTIALS_REQUIRED = "credentials_required"
STATUS_AUTH_REQUIRED = "auth_required"
STATUS_APPROVAL_REQUIRED = "approval_required"


class ToolError(Exception):
    status = STATUS_ERROR
    code = "tool_error"

    def payload(self, **extra: Any) -> dict[str, Any]:
        body: dict[str, Any] = {
            "status": self.status,
            "code": self.code,
            "error": str(self),
        }
        body.update(extra)
        return body


class CredentialsRequired(ToolError):
    status = STATUS_CREDENTIALS_REQUIRED
    code = "credentials_required"

    def __init__(self, provider: str, missing: list[str], hint: str | None = None) -> None:
        self.provider = provider
        self.missing = missing
        self.hint = hint
        detail = f"{provider} credentials are not configured"
        super().__init__(detail)

    def payload(self, **extra: Any) -> dict[str, Any]:
        hint = self.hint or (
            f"Ask the user for the missing {self.provider} details, then call "
            f"save_credentials(provider='{self.provider}', ...). "
            "Do not ask the user to paste secrets into chat if an OAuth flow exists."
        )
        return super().payload(
            provider=self.provider,
            missing=self.missing,
            next_tool="save_credentials",
            hint=hint,
            **extra,
        )


class AuthenticationRequired(ToolError):
    status = STATUS_AUTH_REQUIRED
    code = "auth_required"

    def __init__(self, detail: str = "No valid bearer token was supplied.") -> None:
        super().__init__(detail)

    def payload(self, **extra: Any) -> dict[str, Any]:
        return super().payload(next_tool="login", **extra)


class ApprovalRequired(ToolError):
    status = STATUS_APPROVAL_REQUIRED
    code = "approval_required"

    def __init__(self, action: str, approval_id: str, detail: str) -> None:
        self.action = action
        self.approval_id = approval_id
        super().__init__(detail)

    def payload(self, **extra: Any) -> dict[str, Any]:
        return super().payload(
            action=self.action,
            approval_id=self.approval_id,
            next_tool="approval_status",
            hint=(
                "A human must approve this action. Poll approval_status, then retry "
                "only when status is 'approved'. Do not attempt to bypass this gate."
            ),
            **extra,
        )


class ProviderError(ToolError):
    code = "provider_error"


class ValidationError(ToolError):
    code = "validation_error"


class RateLimitError(ToolError):
    code = "rate_limited"

    def __init__(self, detail: str, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(detail)

    def payload(self, **extra: Any) -> dict[str, Any]:
        return super().payload(retry_after_seconds=self.retry_after_seconds, **extra)


def ok(**fields: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"status": STATUS_OK}
    body.update(fields)
    return body