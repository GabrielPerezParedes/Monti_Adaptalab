"""Opaque auth sessions (hashed bearer tokens)."""
from __future__ import annotations

from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import AuthEvent, AuthSession, User, as_utc, now


def hash_token(token: str) -> str:
    return sha256(token.encode('utf-8')).hexdigest()


def create_session(
    db: Session,
    user: User,
    *,
    ttl_minutes: int,
    user_agent: str | None = None,
    ip_hint: str | None = None,
) -> tuple[str, AuthSession]:
    token = token_urlsafe(32)
    stamp = now()
    row = AuthSession(
        id=str(uuid4()),
        user_id=user.id,
        token_hash=hash_token(token),
        created_at=stamp,
        expires_at=stamp + timedelta(minutes=ttl_minutes),
        last_seen_at=stamp,
        user_agent=(user_agent or '')[:255] or None,
        ip_hint=(ip_hint or '')[:64] or None,
    )
    db.add(row)
    db.commit()
    return token, row


def resolve_session(db: Session, token: str) -> User | None:
    digest = hash_token(token)
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == digest))
    if not session or session.revoked_at is not None:
        return None
    if as_utc(session.expires_at) <= now():
        return None
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        return None
    session.last_seen_at = now()
    db.commit()
    return user


def revoke_session(db: Session, token: str) -> bool:
    digest = hash_token(token)
    session = db.scalar(select(AuthSession).where(AuthSession.token_hash == digest))
    if not session or session.revoked_at is not None:
        return False
    session.revoked_at = now()
    db.commit()
    return True


def revoke_user_sessions(db: Session, user_id: str) -> int:
    rows = list(
        db.scalars(
            select(AuthSession).where(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
            )
        )
    )
    stamp = now()
    for row in rows:
        row.revoked_at = stamp
    db.commit()
    return len(rows)


def record_event(
    db: Session,
    *,
    event_type: str,
    user_id: str | None = None,
    login_attempted: str | None = None,
    meta: dict | None = None,
) -> None:
    db.add(
        AuthEvent(
            user_id=user_id,
            login_attempted=login_attempted,
            event_type=event_type,
            meta=meta or {},
        )
    )
    db.commit()
