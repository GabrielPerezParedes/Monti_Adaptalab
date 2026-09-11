"""FastAPI auth dependencies and school-auth helpers."""
from __future__ import annotations

import os

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import Enrollment, LoginThrottle, TeacherSubjectAssignment, User, as_utc, now
from .sessions import resolve_session


def school_auth_enabled() -> bool:
    return os.getenv('MONTI_FEATURE_SCHOOL_AUTH', 'false').strip().lower() in {'1', 'true', 'yes', 'on'}


def normalize_login(login: str) -> str:
    return login.strip().lower()


def session_ttl_minutes() -> int:
    return int(os.getenv('MONTI_SESSION_TTL_MINUTES', '480'))


def max_failures() -> int:
    return int(os.getenv('MONTI_LOGIN_MAX_FAILURES', '5'))


def lockout_minutes() -> int:
    return int(os.getenv('MONTI_LOGIN_LOCKOUT_MINUTES', '15'))


def throttle_key(login: str, ip: str | None) -> str:
    return f'{normalize_login(login)}|{ip or "-"}'


def check_lockout(db: Session, key: str) -> int | None:
    row = db.get(LoginThrottle, key)
    locked = as_utc(row.locked_until) if row else None
    if locked and locked > now():
        return max(1, int((locked - now()).total_seconds()))
    return None


def register_failure(db: Session, key: str) -> int | None:
    from datetime import timedelta

    row = db.get(LoginThrottle, key)
    stamp = now()
    window = timedelta(minutes=lockout_minutes())
    started = as_utc(row.window_started_at) if row else None
    if not row or not started or (stamp - started) > window:
        row = LoginThrottle(key=key, failure_count=1, window_started_at=stamp, locked_until=None)
        db.merge(row)
        db.commit()
        return None
    row.failure_count += 1
    if row.failure_count >= max_failures():
        row.locked_until = stamp + timedelta(minutes=lockout_minutes())
        db.commit()
        return max(1, int((row.locked_until - stamp).total_seconds()))
    db.commit()
    return None


def clear_throttle(db: Session, key: str) -> None:
    row = db.get(LoginThrottle, key)
    if row:
        db.delete(row)
        db.commit()


def bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(' ', 1)
    if len(parts) != 2 or parts[0].lower() != 'bearer' or not parts[1].strip():
        return None
    return parts[1].strip()


def current_user(
    request: Request,
    authorization: str | None = Header(default=None),
) -> User:
    token = bearer_token(authorization)
    if not token:
        raise HTTPException(401, 'Debes iniciar sesión.')
    factory = request.app.state.session_factory
    with factory() as db:
        user = resolve_session(db, token)
        if not user:
            raise HTTPException(401, 'Sesión no válida o expirada.')
        db.expunge(user)
        return user


def require_roles(*roles: str):
    def _inner(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, 'No tienes permiso para esta acción.')
        return user

    return _inner


def teacher_subject_ids(db: Session, user: User) -> list[str]:
    if user.role == 'admin':
        return []
    rows = db.scalars(
        select(TeacherSubjectAssignment.subject_id).where(
            TeacherSubjectAssignment.teacher_user_id == user.id
        )
    )
    return list(rows)


def require_teacher_subject(db: Session, user: User, subject_id: str | None) -> None:
    if user.role == 'admin':
        return
    if not subject_id:
        raise HTTPException(403, 'La actividad no tiene asignatura asignada.')
    allowed = teacher_subject_ids(db, user)
    if subject_id not in allowed:
        raise HTTPException(403, 'No tienes acceso a esta asignatura.')


def student_enrollment_ids(db: Session, user: User) -> list[str]:
    rows = db.scalars(
        select(Enrollment.id).where(
            Enrollment.student_user_id == user.id,
            Enrollment.is_active.is_(True),
        )
    )
    return list(rows)


def user_public(user: User) -> dict:
    return {
        'id': user.id,
        'login': user.login,
        'display_name': user.display_name,
        'role': user.role,
    }


def build_scope(db: Session, user: User) -> dict:
    if user.role == 'teacher':
        return {'subject_ids': teacher_subject_ids(db, user), 'enrollment_ids': []}
    if user.role == 'student':
        return {'subject_ids': [], 'enrollment_ids': student_enrollment_ids(db, user)}
    return {'subject_ids': [], 'enrollment_ids': []}
