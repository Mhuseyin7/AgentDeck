import re
from collections.abc import Callable

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import HTTPException, status

password_hasher = PasswordHasher()
_SECRET_PATTERN = re.compile(
    r"(?i)(authorization\s*[:=]\s*bearer\s+|api[_-]?key\s*[:=]\s*|token\s*[:=]\s*)[^\s\"']+"
)


def hash_password(value: str) -> str:
    return password_hasher.hash(value)


def verify_password(hash_: str, value: str) -> bool:
    try:
        return password_hasher.verify(hash_, value)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def redact(value: str) -> str:
    return _SECRET_PATTERN.sub(lambda match: match.group(1) + "[REDACTED]", value)


def require_role(*allowed: str) -> Callable[..., None]:
    # Router dependencies bind this to authenticated organization membership.
    def checker() -> None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required"
        )

    return checker
