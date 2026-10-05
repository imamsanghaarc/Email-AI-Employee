"""Stateless session tokens.

A signed JWT carries the subject and the session's JTI. The JTI is what the
storage layer checks for revocation, so logout actually terminates a session
instead of merely asking the client to forget a still-valid token.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

ALGORITHM = "HS256"
AUDIENCE = "ai-employee-mcp"
ISSUER = "ai-employee-mcp"


class TokenError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: str
    jti: str
    expires_at: datetime


def issue_token(user_id: str, secret: str, ttl_seconds: int) -> tuple[str, TokenClaims]:
    jti = uuid.uuid4().hex
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=ttl_seconds)
    payload = {
        "sub": user_id,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "aud": AUDIENCE,
        "iss": ISSUER,
    }
    token = jwt.encode(payload, secret, algorithm=ALGORITHM)
    return token, TokenClaims(user_id=user_id, jti=jti, expires_at=expires_at)


def decode_token(token: str, secret: str) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
            issuer=ISSUER,
            options={"require": ["exp", "sub", "jti"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("session token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError(f"invalid session token: {exc}") from exc
    return TokenClaims(
        user_id=str(payload["sub"]),
        jti=str(payload["jti"]),
        expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
    )