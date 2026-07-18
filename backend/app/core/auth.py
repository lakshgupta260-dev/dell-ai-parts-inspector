"""
JWT authentication utilities.

Uses python-jose for token creation/verification and passlib for password hashing.
All secrets loaded from environment — never hardcoded.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


def create_access_token(
    username: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Generate a signed JWT access token.

    Args:
        username:      Subject claim.
        role:          User role (INSPECTOR | QA_MANAGER).
        expires_delta: Token lifetime. Defaults to JWT_EXPIRE_MINUTES from settings.

    Returns:
        Signed JWT string.
    """
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=int(settings.JWT_EXPIRE_MINUTES))
    )
    payload = {
        "sub": username,
        "role": role,
        "exp": expire,
        "iat": datetime.now(tz=timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Returns:
        Decoded payload dict.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[_ALGORITHM])
