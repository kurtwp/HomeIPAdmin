"""Authentication service — simple user login with hashed passwords."""

import hashlib
import logging
import secrets
from datetime import datetime, timezone

import bcrypt
from sqlalchemy.orm import Session

from app.database.db import get_session
from app.models.user import User

logger = logging.getLogger(__name__)


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except (ValueError, AttributeError):
        return False


def _is_legacy_hash(password_hash: str) -> bool:
    """Check if a password hash is in the old SHA-256 format (salt:hash)."""
    if ":" not in password_hash:
        return False
    parts = password_hash.split(":")
    if len(parts) != 2:
        return False
    salt, hashed = parts
    return len(salt) == 32 and len(hashed) == 64


def create_user(session: Session, username: str, password: str, role: str = "admin") -> User:
    """Create a new user account."""
    user = User(
        username=username.strip().lower(),
        password_hash=_hash_password(password),
        role=role,
    )
    session.add(user)
    session.commit()
    return user


def authenticate(session: Session, username: str, password: str) -> User | None:
    """Authenticate a user. Returns the User if valid, None otherwise."""
    user = session.query(User).filter(
        User.username == username.strip().lower(),
        User.is_active == True,
    ).first()
    if user and _verify_password(password, user.password_hash):
        if _is_legacy_hash(user.password_hash):
            logger.info("Re-hashing legacy password for user %s", username)
            user.password_hash = _hash_password(password)
        user.last_login = datetime.now(timezone.utc)
        session.commit()
        return user
    return None


def get_user_count(session: Session) -> int:
    """Get the number of registered users."""
    return session.query(User).count()


def change_password(session: Session, user_id: int, new_password: str) -> bool:
    """Change a user's password."""
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        user.password_hash = _hash_password(new_password)
        session.commit()
        return True
    return False


def is_auth_enabled() -> bool:
    """Check if authentication is enabled (at least one user exists)."""
    with get_session() as session:
        return session.query(User).count() > 0
