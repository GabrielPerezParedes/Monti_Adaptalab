"""Auth and admin catalog routes."""
from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import (
    Enrollment,
    Grade,
    Subject,
    TeacherSubjectAssignment,
    User,
    now,
)
from ..schemas import StrictModel
from .deps import (
    bearer_token,
    build_scope,
    check_lockout,
    clear_throttle,
    current_user,
    normalize_login,
    register_failure,
    require_roles,
    school_auth_enabled,
    session_ttl_minutes,
    teacher_subject_ids,
    throttle_key,
    user_public,
)
from .passwords import hash_password, verify_password
from .sessions import create_session, record_event, revoke_session, revoke_user_sessions


class LoginBody(StrictModel):
    login: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=200)


class UserCreate(StrictModel):
    login: str = Field(min_length=1, max_length=120)
    display_name: str = Field(min_length=1, max_length=120)
    role: str = Field(pattern='^(admin|teacher|student)$')
    password: str = Field(min_length=10, max_length=200)
    is_active: bool = True


class UserPatch(StrictModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=10, max_length=200)
    role: str | None = Field(default=None, pattern='^(admin|teacher|student)$')


class GradeBody(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    sort_order: int = 0
    is_active: bool = True


class GradePatch(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    sort_order: int | None = None
    is_active: bool | None = None


class SubjectBody(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    is_active: bool = True


class SubjectPatch(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None


class AssignmentBody(StrictModel):
    teacher_user_id: str = Field(min_length=1, max_length=36)
    subject_id: str = Field(min_length=1, max_length=36)


class EnrollmentBody(StrictModel):
    student_user_id: str = Field(min_length=1, max_length=36)
    grade_id: str = Field(min_length=1, max_length=36)
    subject_id: str = Field(min_length=1, max_length=36)
    is_active: bool = True


class EnrollmentPatch(StrictModel):
    is_active: bool | None = None


def get_db(request: Request):
    with request.app.state.session_factory() as session:
        try:
            yield session
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(409, 'Conflicto de datos: revisa duplicados.') from e


def create_auth_router() -> APIRouter:
    router = APIRouter()

    @router.post('/api/auth/login')
    def login(body: LoginBody, request: Request, session: Session = Depends(get_db)):
        login_norm = normalize_login(body.login)
        ip = request.client.host if request.client else None
        key = throttle_key(login_norm, ip)
        wait = check_lockout(session, key)
        if wait:
            record_event(session, event_type='lockout', login_attempted=login_norm, meta={'retry_after_seconds': wait})
            return JSONResponse(
                status_code=429,
                content={'detail': 'Demasiados intentos. Espera e inténtalo de nuevo.', 'retry_after_seconds': wait},
            )
        user = session.scalar(select(User).where(User.login == login_norm))
        if not user or not user.is_active or not verify_password(body.password, user.password_hash):
            wait = register_failure(session, key)
            record_event(session, event_type='login_failure', user_id=user.id if user else None, login_attempted=login_norm)
            if wait:
                record_event(session, event_type='lockout', login_attempted=login_norm, meta={'retry_after_seconds': wait})
                return JSONResponse(
                    status_code=429,
                    content={'detail': 'Demasiados intentos. Espera e inténtalo de nuevo.', 'retry_after_seconds': wait},
                )
            raise HTTPException(401, 'Credenciales no válidas.')
        clear_throttle(session, key)
        token, auth_session = create_session(
            session,
            user,
            ttl_minutes=session_ttl_minutes(),
            user_agent=request.headers.get('user-agent'),
            ip_hint=ip,
        )
        record_event(session, event_type='login_success', user_id=user.id, login_attempted=login_norm)
        return {
            'token': token,
            'expires_at': auth_session.expires_at.isoformat(),
            'user': user_public(user),
        }

    @router.post('/api/auth/logout', status_code=204)
    def logout(
        response: Response,
        authorization: str | None = Header(default=None),
        session: Session = Depends(get_db),
    ):
        token = bearer_token(authorization)
        if token:
            revoke_session(session, token)
            record_event(session, event_type='logout')
        response.status_code = 204
        return Response(status_code=204)

    @router.get('/api/auth/me')
    def me(request: Request, user: User = Depends(current_user), session: Session = Depends(get_db)):
        return {**user_public(user), 'scope': build_scope(session, user)}

    @router.get('/api/student/enrollments')
    def my_enrollments(user: User = Depends(require_roles('student', 'admin')), session: Session = Depends(get_db)):
        query = select(Enrollment).where(Enrollment.is_active.is_(True))
        if user.role == 'student':
            query = query.where(Enrollment.student_user_id == user.id)
        rows = list(session.scalars(query))
        return [
            {
                'id': e.id,
                'student_user_id': e.student_user_id,
                'grade_id': e.grade_id,
                'subject_id': e.subject_id,
                'is_active': e.is_active,
            }
            for e in rows
        ]

    @router.get('/api/teacher/scope')
    def teacher_scope(user: User = Depends(require_roles('admin', 'teacher')), session: Session = Depends(get_db)):
        subjects = list(session.scalars(select(Subject).where(Subject.is_active.is_(True)).order_by(Subject.name)))
        grades = list(session.scalars(select(Grade).where(Grade.is_active.is_(True)).order_by(Grade.sort_order, Grade.name)))
        allowed = set(teacher_subject_ids(session, user)) if user.role == 'teacher' else {s.id for s in subjects}
        return {
            'subjects': [{'id': s.id, 'name': s.name} for s in subjects if s.id in allowed or user.role == 'admin'],
            'grades': [{'id': g.id, 'name': g.name, 'sort_order': g.sort_order} for g in grades],
            'subject_ids': list(allowed) if user.role == 'teacher' else [s.id for s in subjects],
        }

    @router.get('/api/teacher/enrollments')
    def teacher_enrollments(
        subject_id: str,
        user: User = Depends(require_roles('admin', 'teacher')),
        session: Session = Depends(get_db),
    ):
        if user.role == 'teacher' and subject_id not in teacher_subject_ids(session, user):
            raise HTTPException(403, 'No tienes acceso a esta asignatura.')
        rows = list(
            session.scalars(
                select(Enrollment).where(
                    Enrollment.subject_id == subject_id,
                    Enrollment.is_active.is_(True),
                )
            )
        )
        return [
            {
                'id': e.id,
                'student_user_id': e.student_user_id,
                'grade_id': e.grade_id,
                'subject_id': e.subject_id,
                'is_active': e.is_active,
            }
            for e in rows
        ]

    # --- Admin users ---
    @router.get('/api/admin/users')
    def list_users(_: User = Depends(require_roles('admin')), session: Session = Depends(get_db)):
        users = list(session.scalars(select(User).order_by(User.login)))
        return [{**user_public(u), 'is_active': u.is_active} for u in users]

    @router.post('/api/admin/users', status_code=201)
    def create_user(body: UserCreate, _: User = Depends(require_roles('admin')), session: Session = Depends(get_db)):
        user = User(
            id=str(uuid4()),
            login=normalize_login(body.login),
            display_name=body.display_name.strip(),
            role=body.role,
            password_hash=hash_password(body.password),
            is_active=body.is_active,
        )
        session.add(user)
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(409, 'El identificador de acceso ya existe.') from e
        return {**user_public(user), 'is_active': user.is_active}

    @router.patch('/api/admin/users/{user_id}')
    def patch_user(
        user_id: str,
        body: UserPatch,
        _: User = Depends(require_roles('admin')),
        session: Session = Depends(get_db),
    ):
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(404, 'Usuario no encontrado.')
        data = body.model_dump(exclude_unset=True)
        if 'display_name' in data and data['display_name'] is not None:
            user.display_name = data['display_name'].strip()
        if 'role' in data and data['role'] is not None:
            user.role = data['role']
        if 'password' in data and data['password']:
            user.password_hash = hash_password(data['password'])
            revoke_user_sessions(session, user.id)
            record_event(session, event_type='password_reset', user_id=user.id)
        if 'is_active' in data and data['is_active'] is not None:
            user.is_active = data['is_active']
            if not user.is_active:
                user.deactivated_at = now()
                revoke_user_sessions(session, user.id)
                record_event(session, event_type='session_revoked', user_id=user.id, meta={'reason': 'deactivated'})
            else:
                user.deactivated_at = None
        user.updated_at = now()
        session.commit()
        return {**user_public(user), 'is_active': user.is_active}

    @router.get('/api/admin/grades')
    def list_grades(_: User = Depends(require_roles('admin')), session: Session = Depends(get_db)):
        rows = list(session.scalars(select(Grade).order_by(Grade.sort_order, Grade.name)))
        return [{'id': g.id, 'name': g.name, 'sort_order': g.sort_order, 'is_active': g.is_active} for g in rows]

    @router.post('/api/admin/grades', status_code=201)
    def create_grade(body: GradeBody, _: User = Depends(require_roles('admin')), session: Session = Depends(get_db)):
        grade = Grade(id=str(uuid4()), name=body.name.strip(), sort_order=body.sort_order, is_active=body.is_active)
        session.add(grade)
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(409, 'Ya existe un grado con ese nombre.') from e
        return {'id': grade.id, 'name': grade.name, 'sort_order': grade.sort_order, 'is_active': grade.is_active}

    @router.patch('/api/admin/grades/{grade_id}')
    def patch_grade(
        grade_id: str,
        body: GradePatch,
        _: User = Depends(require_roles('admin')),
        session: Session = Depends(get_db),
    ):
        grade = session.get(Grade, grade_id)
        if not grade:
            raise HTTPException(404, 'Grado no encontrado.')
        data = body.model_dump(exclude_unset=True)
        if 'name' in data and data['name'] is not None:
            grade.name = data['name'].strip()
        if 'sort_order' in data and data['sort_order'] is not None:
            grade.sort_order = data['sort_order']
        if 'is_active' in data and data['is_active'] is not None:
            grade.is_active = data['is_active']
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(409, 'Ya existe un grado con ese nombre.') from e
        return {'id': grade.id, 'name': grade.name, 'sort_order': grade.sort_order, 'is_active': grade.is_active}

    @router.get('/api/admin/subjects')
    def list_subjects(_: User = Depends(require_roles('admin')), session: Session = Depends(get_db)):
        rows = list(session.scalars(select(Subject).order_by(Subject.name)))
        return [{'id': s.id, 'name': s.name, 'is_active': s.is_active} for s in rows]

    @router.post('/api/admin/subjects', status_code=201)
    def create_subject(body: SubjectBody, _: User = Depends(require_roles('admin')), session: Session = Depends(get_db)):
        subject = Subject(id=str(uuid4()), name=body.name.strip(), is_active=body.is_active)
        session.add(subject)
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(409, 'Ya existe una asignatura con ese nombre.') from e
        return {'id': subject.id, 'name': subject.name, 'is_active': subject.is_active}

    @router.patch('/api/admin/subjects/{subject_id}')
    def patch_subject(
        subject_id: str,
        body: SubjectPatch,
        _: User = Depends(require_roles('admin')),
        session: Session = Depends(get_db),
    ):
        subject = session.get(Subject, subject_id)
        if not subject:
            raise HTTPException(404, 'Asignatura no encontrada.')
        data = body.model_dump(exclude_unset=True)
        if 'name' in data and data['name'] is not None:
            subject.name = data['name'].strip()
        if 'is_active' in data and data['is_active'] is not None:
            subject.is_active = data['is_active']
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(409, 'Ya existe una asignatura con ese nombre.') from e
        return {'id': subject.id, 'name': subject.name, 'is_active': subject.is_active}

    @router.get('/api/admin/teacher-assignments')
    def list_assignments(_: User = Depends(require_roles('admin')), session: Session = Depends(get_db)):
        rows = list(session.scalars(select(TeacherSubjectAssignment)))
        return [
            {'id': a.id, 'teacher_user_id': a.teacher_user_id, 'subject_id': a.subject_id, 'created_at': a.created_at.isoformat()}
            for a in rows
        ]

    @router.post('/api/admin/teacher-assignments', status_code=201)
    def create_assignment(
        body: AssignmentBody,
        _: User = Depends(require_roles('admin')),
        session: Session = Depends(get_db),
    ):
        teacher = session.get(User, body.teacher_user_id)
        subject = session.get(Subject, body.subject_id)
        if not teacher or teacher.role != 'teacher':
            raise HTTPException(422, 'El usuario debe tener rol profesor.')
        if not subject:
            raise HTTPException(422, 'Asignatura no encontrada.')
        row = TeacherSubjectAssignment(id=str(uuid4()), teacher_user_id=teacher.id, subject_id=subject.id)
        session.add(row)
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(409, 'La asignación ya existe.') from e
        return {'id': row.id, 'teacher_user_id': row.teacher_user_id, 'subject_id': row.subject_id}

    @router.delete('/api/admin/teacher-assignments/{assignment_id}', status_code=204)
    def delete_assignment(
        assignment_id: str,
        _: User = Depends(require_roles('admin')),
        session: Session = Depends(get_db),
    ):
        row = session.get(TeacherSubjectAssignment, assignment_id)
        if not row:
            raise HTTPException(404, 'Asignación no encontrada.')
        session.delete(row)
        session.commit()
        return Response(status_code=204)

    @router.get('/api/admin/enrollments')
    def list_enrollments(_: User = Depends(require_roles('admin')), session: Session = Depends(get_db)):
        rows = list(session.scalars(select(Enrollment)))
        return [
            {
                'id': e.id,
                'student_user_id': e.student_user_id,
                'grade_id': e.grade_id,
                'subject_id': e.subject_id,
                'is_active': e.is_active,
            }
            for e in rows
        ]

    @router.post('/api/admin/enrollments', status_code=201)
    def create_enrollment(
        body: EnrollmentBody,
        _: User = Depends(require_roles('admin')),
        session: Session = Depends(get_db),
    ):
        student = session.get(User, body.student_user_id)
        if not student or student.role != 'student':
            raise HTTPException(422, 'El usuario debe tener rol alumno.')
        if not session.get(Grade, body.grade_id) or not session.get(Subject, body.subject_id):
            raise HTTPException(422, 'Grado o asignatura no válidos.')
        row = Enrollment(
            id=str(uuid4()),
            student_user_id=student.id,
            grade_id=body.grade_id,
            subject_id=body.subject_id,
            is_active=body.is_active,
        )
        session.add(row)
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(409, 'La matrícula ya existe.') from e
        return {
            'id': row.id,
            'student_user_id': row.student_user_id,
            'grade_id': row.grade_id,
            'subject_id': row.subject_id,
            'is_active': row.is_active,
        }

    @router.patch('/api/admin/enrollments/{enrollment_id}')
    def patch_enrollment(
        enrollment_id: str,
        body: EnrollmentPatch,
        _: User = Depends(require_roles('admin')),
        session: Session = Depends(get_db),
    ):
        row = session.get(Enrollment, enrollment_id)
        if not row:
            raise HTTPException(404, 'Matrícula no encontrada.')
        if body.is_active is not None:
            row.is_active = body.is_active
        session.commit()
        return {
            'id': row.id,
            'student_user_id': row.student_user_id,
            'grade_id': row.grade_id,
            'subject_id': row.subject_id,
            'is_active': row.is_active,
        }

    # Silence unused import warning for flag documentation
    _ = school_auth_enabled
    return router
