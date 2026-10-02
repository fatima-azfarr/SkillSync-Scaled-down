"""
SkillSync — Authentication & Security Subsystem

Senior Security Engineer implementation providing:
- Secure bcrypt password hashing with salt rounds and 72-byte limit enforcement
- Cryptographically signed JWT access tokens with strict expiration
- Password complexity validation to prevent trivial/weak credentials
- Secure token generation with SHA-256 hash persistence for email verification and password reset
- Token-based session invalidation on password change
- Thread-safe sliding-window rate limiting for authentication endpoints
- Strict access control dependencies preventing Broken Object Level Authorization (BOLA/IDOR)
"""

from datetime import datetime, timedelta, timezone
import hashlib
import re
import secrets
import threading
import time
from typing import Optional, Tuple

import bcrypt
from bson import ObjectId
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from api.config import config
from api.database import get_database

# HTTP Bearer scheme (auto_error=False allows customizable error handling and optional auth)
bearer_scheme = HTTPBearer(auto_error=False)


# ─── Password Security & Hashing ─────────────────────────────────────────────

def validate_password_complexity(password: str) -> None:
    """
    Validate that a plaintext password meets defensive security complexity rules.
    
    Rules:
    - Minimum 8 characters
    - Maximum 72 bytes (prevents bcrypt truncation bypass and CPU exhaustion DoS)
    - Contains at least one letter
    - Contains at least one number
    """
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required.",
        )

    byte_len = len(password.encode("utf-8"))
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )
    if byte_len > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot exceed 72 bytes.",
        )
    if not any(c.isalpha() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one letter.",
        )
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number.",
        )


def hash_password(password: str) -> str:
    """
    Hash a plaintext password with bcrypt and work factor salt.
    Enforces the 72-byte maximum bcrypt boundary.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot exceed 72 bytes for hashing.",
        )
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.
    Safe against timing attacks.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ─── Cryptographic Token Utilities ───────────────────────────────────────────

def hash_token(raw_token: str) -> str:
    """
    Compute a SHA-256 hash of a raw one-time token.
    Only the hash is persisted in the database, ensuring raw tokens
    are never exposed even if the database is dumped.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a high-entropy URL-safe random string."""
    return secrets.token_urlsafe(nbytes)


def generate_verification_token() -> Tuple[str, str, datetime]:
    """
    Generate an email verification token, its SHA-256 hash, and expiration timestamp.
    Returns: (raw_token, token_hash, expires_at)
    """
    raw_token = generate_secure_token(32)
    token_hash = hash_token(raw_token)
    expires_at = datetime.utcnow() + timedelta(hours=config.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    return raw_token, token_hash, expires_at


def generate_reset_token() -> Tuple[str, str, datetime]:
    """
    Generate a password reset token, its SHA-256 hash, and expiration timestamp.
    Returns: (raw_token, token_hash, expires_at)
    """
    raw_token = generate_secure_token(32)
    token_hash = hash_token(raw_token)
    expires_at = datetime.utcnow() + timedelta(minutes=config.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    return raw_token, token_hash, expires_at


# ─── Session JWT Management ──────────────────────────────────────────────────

def create_access_token(student_id: str, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate a signed JWT access token for student sessions.
    Strictly sets type='access', subject, email, iat, and exp.
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES))

    payload = {
        "sub": student_id,
        "email": email,
        "type": "access",
        "iat": now.timestamp(),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.
    Raises HTTPException 401 if expired or invalid.
    """
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET_KEY,
            algorithms=[config.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "iat", "type"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


# ─── Sliding-Window Rate Limiter ─────────────────────────────────────────────

class SlidingWindowRateLimiter:
    """
    Thread-safe in-memory sliding-window rate limiter.
    Tracks timestamps per key and rejects excessive attempts within a window.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._attempts = {}

    def is_rate_limited(self, key: str, max_attempts: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Check whether an action for key exceeds max_attempts within window_seconds.
        Returns: (is_limited, retry_after_seconds)
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._attempts.get(key, [])
            # Prune attempts outside the window
            timestamps = [t for t in timestamps if t > cutoff]
            self._attempts[key] = timestamps

            if len(timestamps) >= max_attempts:
                oldest = timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now))
                return True, retry_after

            return False, 0

    def record_attempt(self, key: str) -> None:
        """Record an attempt timestamp for key."""
        now = time.time()
        with self._lock:
            if key not in self._attempts:
                self._attempts[key] = []
            self._attempts[key].append(now)

    def reset(self, key: str) -> None:
        """Reset attempts for a key (e.g. after successful login)."""
        with self._lock:
            self._attempts.pop(key, None)


# Rate limiter instances for auth surfaces
login_rate_limiter = SlidingWindowRateLimiter()
password_reset_rate_limiter = SlidingWindowRateLimiter()
verification_rate_limiter = SlidingWindowRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, taking forwarding headers into account."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ─── FastAPI Security Dependencies ───────────────────────────────────────────

async def get_current_student(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """
    Dependency that enforces valid authentication and returns the student record.
    Rejects missing, expired, tampered, or revoked tokens.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    student_id = payload.get("sub")

    try:
        obj_id = ObjectId(student_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed student identifier in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db = get_database()
    student = await db[config.STUDENTS_COLLECTION].find_one({"_id": obj_id})
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student account not found or has been removed.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Invalidate session if password was changed after token issuance
    password_changed_at = student.get("password_changed_at")
    if password_changed_at:
        if password_changed_at.tzinfo is None:
            pwd_changed_ts = password_changed_at.replace(tzinfo=timezone.utc).timestamp()
        else:
            pwd_changed_ts = password_changed_at.timestamp()
        token_iat = float(payload.get("iat", 0))
        if token_iat < pwd_changed_ts:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session invalidated due to password change. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return student


async def get_optional_student(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[dict]:
    """
    Optional authentication dependency.
    Returns the student dict if a valid token is provided, or None if unauthenticated.
    """
    if not credentials or not credentials.credentials:
        return None

    try:
        return await get_current_student(credentials)
    except HTTPException:
        return None


def require_student_ownership(student_id: str, current_student: dict) -> None:
    """
    Ensure the authenticated student owns the resource they are mutating (prevents IDOR).
    Raises 403 Forbidden if attempting to access another student's account.
    """
    if str(current_student["_id"]) != str(student_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access or modify this student resource.",
        )