"""Authentication service — user login, failed login tracking, user management."""

import logging
from datetime import datetime, timezone, timedelta

import bcrypt
from sqlalchemy.orm import Session

from app.database.db import get_session
from app.models.user import User
from app.models.login_attempt import LoginAttempt

logger = logging.getLogger(__name__)

# Lockout policy
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


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


def authenticate(session: Session, username: str, password: str, ip_address: str | None = None) -> User | None:
    """Authenticate a user. Records the attempt and enforces lockout. Returns the User if valid, None otherwise."""
    now = datetime.now(timezone.utc)
    lockout_cutoff = now - timedelta(minutes=LOCKOUT_MINUTES)

    # Check lockout
    recent_fails = (
        session.query(LoginAttempt)
        .filter(
            LoginAttempt.username == username.strip().lower(),
            LoginAttempt.success == False,
            LoginAttempt.timestamp >= lockout_cutoff,
        )
        .count()
    )
    if recent_fails >= MAX_FAILED_ATTEMPTS:
        logger.warning("Locked out user %s (%d recent failures)", username, recent_fails)
        _record_attempt(session, username, False, ip_address)
        return None

    user = session.query(User).filter(
        User.username == username.strip().lower(),
        User.is_active == True,
    ).first()
    if user and _verify_password(password, user.password_hash):
        if _is_legacy_hash(user.password_hash):
            logger.info("Re-hashing legacy password for user %s", username)
            user.password_hash = _hash_password(password)
        user.last_login = now
        _record_attempt(session, username, True, ip_address)
        session.commit()
        return user

    _record_attempt(session, username, False, ip_address)
    session.commit()
    return None


def _record_attempt(session: Session, username: str, success: bool, ip_address: str | None) -> None:
    """Record a login attempt."""
    attempt = LoginAttempt(
        username=username.strip().lower(),
        success=success,
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc),
    )
    session.add(attempt)


def is_locked_out(session: Session, username: str) -> bool:
    """Check if a user is currently locked out."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_MINUTES)
    fail_count = (
        session.query(LoginAttempt)
        .filter(
            LoginAttempt.username == username.strip().lower(),
            LoginAttempt.success == False,
            LoginAttempt.timestamp >= cutoff,
        )
        .count()
    )
    return fail_count >= MAX_FAILED_ATTEMPTS


def get_login_history(session: Session, limit: int = 50) -> list[LoginAttempt]:
    """Get recent login attempts."""
    return (
        session.query(LoginAttempt)
        .order_by(LoginAttempt.timestamp.desc())
        .limit(limit)
        .all()
    )


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


# --- User Management ---

def get_all_users(session: Session) -> list[User]:
    """Return all users ordered by creation date."""
    return session.query(User).order_by(User.created_at.asc()).all()


def delete_user(session: Session, user_id: int) -> bool:
    """Delete a user by ID. Cannot delete the last admin."""
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    # Prevent deleting the last admin
    if user.role == "admin":
        admin_count = session.query(User).filter(User.role == "admin", User.is_active == True).count()
        if admin_count <= 1:
            return False
    session.delete(user)
    session.commit()
    return True


def toggle_user_active(session: Session, user_id: int) -> bool:
    """Toggle a user's active status."""
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    # Prevent deactivating the last admin
    if user.role == "admin" and user.is_active:
        admin_count = session.query(User).filter(User.role == "admin", User.is_active == True).count()
        if admin_count <= 1:
            return False
    user.is_active = not user.is_active
    session.commit()
    return True


def update_user_role(session: Session, user_id: int, new_role: str) -> bool:
    """Update a user's role."""
    if new_role not in ("admin", "viewer"):
        return False
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    # Prevent demoting the last admin
    if user.role == "admin" and new_role != "admin":
        admin_count = session.query(User).filter(User.role == "admin", User.is_active == True).count()
        if admin_count <= 1:
            return False
    user.role = new_role
    session.commit()
    return True
