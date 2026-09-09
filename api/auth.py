import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a plaintext password for storage.

    Never store or log plaintext passwords - only ever persist the
    output of this function.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Check a plaintext password attempt against a stored bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))