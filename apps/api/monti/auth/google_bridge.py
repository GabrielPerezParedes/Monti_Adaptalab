"""Google Workspace → MONTI session bridge (via Supabase Auth JWT)."""
from __future__ import annotations

import os
from uuid import uuid4

import jwt
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import Enrollment, PilotRoster, TeacherSubjectAssignment, User, now


FORBIDDEN_ROSTER_COLUMN_MARKERS = ('password', 'passwd', 'clave', 'secret', 'token')


def google_login_enabled() -> bool:
    flag = os.getenv('MONTI_FEATURE_GOOGLE_LOGIN', 'false').strip().lower() in {'1', 'true', 'yes', 'on'}
    secret = (os.getenv('SUPABASE_JWT_SECRET') or '').strip()
    return flag and bool(secret) and secret != 'TU_JWT_SECRET'


def allowed_google_domain() -> str:
    return os.getenv('MONTI_GOOGLE_ALLOWED_DOMAIN', 'montessorisucre.edu.bo').strip().lower()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def email_domain(email: str) -> str:
    parts = normalize_email(email).rsplit('@', 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise HTTPException(400, 'Email institucional no válido.')
    return parts[1]


def assert_allowed_domain(email: str) -> None:
    domain = email_domain(email)
    allowed = allowed_google_domain()
    if domain != allowed:
        raise HTTPException(403, f'Solo se admiten cuentas @{allowed}.')


def claims_from_access_token(access_token: str) -> dict:
    """Verify Supabase JWT and return claims. Monkeypatch in tests."""
    secret = (os.getenv('SUPABASE_JWT_SECRET') or '').strip()
    if not secret or secret == 'TU_JWT_SECRET':
        raise HTTPException(503, 'Login Google no está configurado (SUPABASE_JWT_SECRET).')
    try:
        return jwt.decode(
            access_token,
            secret,
            algorithms=['HS256'],
            audience='authenticated',
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(401, 'Token de Google/Supabase no válido.') from exc


def require_roster(db: Session, email: str) -> PilotRoster:
    row = db.scalar(
        select(PilotRoster).where(
            PilotRoster.email == normalize_email(email),
            PilotRoster.active.is_(True),
        )
    )
    if not row:
        raise HTTPException(403, 'No estás en el roster del piloto. Pide alta al administrador MONTI.')
    return row


def upsert_google_user(db: Session, *, email: str, sub: str, roster: PilotRoster, display_name: str | None) -> User:
    email_n = normalize_email(email)
    user = db.scalar(select(User).where((User.email == email_n) | (User.google_sub == sub) | (User.login == email_n)))
    name = (roster.display_name or display_name or email_n.split('@', 1)[0])[:120]
    if user:
        user.email = email_n
        user.google_sub = sub
        user.auth_provider = 'google'
        user.display_name = name
        user.role = roster.role
        user.is_active = True
        user.password_hash = None
        user.updated_at = now()
    else:
        user = User(
            id=str(uuid4()),
            login=email_n,
            email=email_n,
            google_sub=sub,
            display_name=name,
            role=roster.role,
            password_hash=None,
            auth_provider='google',
            is_active=True,
        )
        db.add(user)
    db.flush()
    apply_roster_scope(db, user, roster)
    db.commit()
    db.refresh(user)
    return user


def apply_roster_scope(db: Session, user: User, roster: PilotRoster) -> None:
    if user.role == 'student' and roster.grade_id and roster.subject_id:
        existing = db.scalar(
            select(Enrollment).where(
                Enrollment.student_user_id == user.id,
                Enrollment.grade_id == roster.grade_id,
                Enrollment.subject_id == roster.subject_id,
            )
        )
        if existing:
            existing.is_active = True
        else:
            db.add(
                Enrollment(
                    id=str(uuid4()),
                    student_user_id=user.id,
                    grade_id=roster.grade_id,
                    subject_id=roster.subject_id,
                    is_active=True,
                )
            )
    if user.role == 'teacher' and roster.subject_id:
        existing = db.scalar(
            select(TeacherSubjectAssignment).where(
                TeacherSubjectAssignment.teacher_user_id == user.id,
                TeacherSubjectAssignment.subject_id == roster.subject_id,
            )
        )
        if not existing:
            db.add(
                TeacherSubjectAssignment(
                    id=str(uuid4()),
                    teacher_user_id=user.id,
                    subject_id=roster.subject_id,
                )
            )


def validate_roster_headers(headers: list[str]) -> None:
    for raw in headers:
        name = raw.strip().lower()
        if any(marker in name for marker in FORBIDDEN_ROSTER_COLUMN_MARKERS):
            raise HTTPException(
                422,
                f'Columna prohibida en roster: "{raw}". Solo datos sin secretos (email, role, …).',
            )


def complete_google_login(db: Session, access_token: str) -> User:
    if not google_login_enabled():
        raise HTTPException(503, 'Login Google deshabilitado.')
    claims = claims_from_access_token(access_token)
    email = claims.get('email')
    sub = claims.get('sub')
    if not email or not sub:
        raise HTTPException(401, 'El token no incluye email/sub verificados.')
    if claims.get('email_verified') is False:
        raise HTTPException(403, 'El email de Google no está verificado.')
    assert_allowed_domain(str(email))
    roster = require_roster(db, str(email))
    name = claims.get('user_metadata', {}).get('full_name') if isinstance(claims.get('user_metadata'), dict) else None
    name = name or claims.get('name')
    return upsert_google_user(
        db,
        email=str(email),
        sub=str(sub),
        roster=roster,
        display_name=str(name) if name else None,
    )
