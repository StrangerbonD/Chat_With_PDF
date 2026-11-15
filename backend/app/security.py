import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt
from fastapi import HTTPException, status

from app.config import get_settings


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def _truncate(plain: str) -> bytes:
    """bcrypt silently truncates at 72 bytes; we do it explicitly."""
    return plain.encode("utf-8")[:72]


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain* (truncated to 72 bytes)."""
    return bcrypt.hashpw(_truncate(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Check *plain* against a stored bcrypt *hashed* string."""
    return bcrypt.checkpw(_truncate(plain), hashed.encode("utf-8"))


# ---------------------------------------------------------------------------
# Verification-code helpers
# ---------------------------------------------------------------------------

def generate_code() -> str:
    """Return a random 6-digit string (zero-padded)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_code(code: str) -> str:
    """Return the SHA-256 hex digest of *code*."""
    return hashlib.sha256(code.encode()).hexdigest()


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def generate_token_id() -> str:
    return str(uuid4())


def _settings():
    return get_settings()


def create_access_token(user_id: str, role: str) -> str:
    s = _settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=s.access_token_minutes),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def create_refresh_token(user_id: str, role: str, jti: str | None = None) -> str:
    s = _settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "refresh",
        "jti": jti or str(uuid4()),
        "iat": now,
        "exp": now + timedelta(days=s.refresh_token_days),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def decode_token(token: str, expected_type: str) -> dict:
    """
    Decode and validate *token*.

    Raises HTTP 401 if the token is invalid, expired, or of the wrong type.
    Returns the raw payload dict on success.
    """
    s = _settings()
    try:
        payload: dict = jwt.decode(token, s.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Expected token type '{expected_type}'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload
