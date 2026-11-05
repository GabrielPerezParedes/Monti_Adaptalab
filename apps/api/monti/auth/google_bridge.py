"""Google Workspace → MONTI session bridge (Firebase ID token o Supabase JWT)."""
from __future__ import annotations

import os
from uuid import uuid4

import httpx
import jwt
from fastapi import HTTPException
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import Enrollment, PilotRoster, TeacherSubjectAssignment, User, now


FORBIDDEN_ROSTER_COLUMN_MARKERS = ('password', 'passwd', 'clave', 'secret', 'token')
_FIREBASE_JWKS_URL = 'https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com'
_firebase_jwk_client: PyJWKClient | None = None


def _flag_on(name: str) -> bool:
    return os.getenv(name, 'false').strip().lower() in {'1', 'true', 'yes', 'on'}


def firebase_project_id() -> str:
    return (os.getenv('FIREBASE_PROJECT_ID') or os.getenv('VITE_FIREBASE_PROJECT_ID') or '').strip()


def firebase_web_api_key() -> str:
    key = (os.getenv('FIREBASE_WEB_API_KEY') or os.getenv('VITE_FIREBASE_API_KEY') or '').strip()
    if key:
        return key
    # Si la API arrancó antes de añadir la variable, leer .env en caliente.
    try:
        from pathlib import Path

        from dotenv import dotenv_values

        env_path = Path(__file__).resolve().parents[2] / '.env'
        values = dotenv_values(env_path)
        return (values.get('FIREBASE_WEB_API_KEY') or values.get('VITE_FIREBASE_API_KEY') or '').strip()
    except Exception:
        return ''


def _supabase_ready() -> bool:
    secret = (os.getenv('SUPABASE_JWT_SECRET') or '').strip()
    return bool(secret) and secret != 'TU_JWT_SECRET'


def _firebase_ready() -> bool:
    return bool(firebase_project_id())


def google_login_enabled() -> bool:
    return _flag_on('MONTI_FEATURE_GOOGLE_LOGIN') and (_firebase_ready() or _supabase_ready())


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


def _firebase_jwks() -> PyJWKClient:
    global _firebase_jwk_client
    if _firebase_jwk_client is None:
        _firebase_jwk_client = PyJWKClient(_FIREBASE_JWKS_URL, cache_keys=True)
    return _firebase_jwk_client


def _claims_via_identity_toolkit(id_token: str) -> dict:
    """Valida el ID token con Identity Toolkit (no requiere paquete cryptography)."""
    api_key = firebase_web_api_key()
    if not api_key:
        raise HTTPException(503, 'Login Google no está configurado (FIREBASE_WEB_API_KEY).')
    try:
        response = httpx.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}',
            json={'idToken': id_token},
            timeout=15.0,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(503, 'No se pudo verificar el token con Firebase.') from exc
    if response.status_code != 200:
        raise HTTPException(401, 'Token de Google/Firebase no válido.')
    users = (response.json() or {}).get('users') or []
    if not users:
        raise HTTPException(401, 'Token de Google/Firebase no válido.')
    user = users[0]
    verified = user.get('emailVerified')
    email_verified = verified is True or str(verified).lower() == 'true'
    return {
        'email': user.get('email'),
        'email_verified': email_verified,
        'sub': user.get('localId'),
        'name': user.get('displayName'),
    }


def claims_from_firebase_id_token(access_token: str) -> dict:
    project_id = firebase_project_id()
    if not project_id:
        raise HTTPException(503, 'Login Google no está configurado (FIREBASE_PROJECT_ID).')
    try:
        key = _firebase_jwks().get_signing_key_from_jwt(access_token)
        return jwt.decode(
            access_token,
            key.key,
            algorithms=['RS256'],
            audience=project_id,
            issuer=f'https://securetoken.google.com/{project_id}',
        )
    except jwt.exceptions.MissingCryptographyError:
        return _claims_via_identity_toolkit(access_token)
    except jwt.PyJWTError:
        # Token firmado pero JWKS falló, o cryptography ausente en otro camino
        try:
            return _claims_via_identity_toolkit(access_token)
        except HTTPException:
            raise
    except Exception:
        return _claims_via_identity_toolkit(access_token)


def claims_from_supabase_jwt(access_token: str) -> dict:
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


def claims_from_access_token(access_token: str) -> dict:
    """Verify Firebase ID token (RS256) or Supabase JWT (HS256). Monkeypatch in tests."""
    try:
        header = jwt.get_unverified_header(access_token)
    except jwt.PyJWTError as exc:
        raise HTTPException(401, 'Token de Google no válido.') from exc
    alg = str(header.get('alg') or '')
    if alg == 'RS256' and _firebase_ready():
        return claims_from_firebase_id_token(access_token)
    if alg == 'HS256' and _supabase_ready():
        return claims_from_supabase_jwt(access_token)
    if _firebase_ready():
        return claims_from_firebase_id_token(access_token)
    if _supabase_ready():
        return claims_from_supabase_jwt(access_token)
    raise HTTPException(503, 'Login Google no está configurado (Firebase o Supabase).')


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
