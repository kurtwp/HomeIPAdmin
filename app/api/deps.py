"""API dependencies — database sessions and authentication."""

from collections.abc import Generator

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database.db import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for the duration of the request."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-KEY")) -> str:
    """Validate the API key from the request header."""
    from config import API_KEY

    if not API_KEY:
        raise HTTPException(
            status_code=503,
            detail="API key not configured. Set API_KEY in your .env file.",
        )
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
