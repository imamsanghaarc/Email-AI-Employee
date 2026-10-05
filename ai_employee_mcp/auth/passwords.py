"""Argon2id password hashing plus a minimal strength policy.

The strength policy is enforced at registration so a weak password is rejected
before it becomes a liability in the credentials table's sibling row.
"""

from __future__ import annotations

import re

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from ..errors import ValidationError

_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16)

MIN_LENGTH = 12
MAX_LENGTH = 256
_COMMON = {
    "password",
    "password1",
    "password123",
    "12345678",
    "123456789",
    "qwertyuiop",
    "letmein123",
    "iloveyou1",
    "administrator",
    "changeme123",
}


class PasswordPolicyError(ValidationError):
    code = "weak_password"

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("Password does not meet policy: " + "; ".join(problems))

    def payload(self, **extra):
        return super().payload(problems=self.problems, **extra)


def validate_password_strength(password: str) -> None:
    problems: list[str] = []
    if len(password) < MIN_LENGTH:
        problems.append(f"must be at least {MIN_LENGTH} characters")
    if len(password) > MAX_LENGTH:
        problems.append(f"must be at most {MAX_LENGTH} characters")
    if password.lower() in _COMMON:
        problems.append("is a commonly used password")
    if not re.search(r"[a-z]", password):
        problems.append("must contain a lowercase letter")
    if not re.search(r"[A-Z]", password):
        problems.append("must contain an uppercase letter")
    if not re.search(r"\d", password):
        problems.append("must contain a digit")
    if not re.search(r"[^\w\s]", password):
        problems.append("must contain a symbol")
    if problems:
        raise PasswordPolicyError(problems)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    return True


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True