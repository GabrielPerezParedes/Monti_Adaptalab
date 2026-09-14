"""MONTI persistence models (labs + school identity)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def now():
    # Naive UTC: SQLite drops tzinfo on round-trip; keep comparisons consistent.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Lab(Base):
    __tablename__ = 'labs'
    id: Mapped[str] = mapped_column(String(12), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    grade_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('grades.id'), nullable=True)
    subject_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('subjects.id'), nullable=True)


class Attempt(Base):
    __tablename__ = 'attempts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    lab_id: Mapped[str] = mapped_column(ForeignKey('labs.id'))
    alias: Mapped[str] = mapped_column(String(40))
    token_hash: Mapped[str] = mapped_column(String(64))
    phase: Mapped[str] = mapped_column(String(20), default='exploration')
    explanations: Mapped[list] = mapped_column(JSON, default=list)
    reviews: Mapped[list] = mapped_column(JSON, default=list)
    final_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('users.id'), nullable=True)
    enrollment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('enrollments.id'), nullable=True)


class Run(Base):
    __tablename__ = 'runs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey('attempts.id'))
    initial: Mapped[dict] = mapped_column(JSON)
    landed: Mapped[bool] = mapped_column(Boolean, default=False)
    invalid: Mapped[bool] = mapped_column(Boolean, default=False)
    abandoned: Mapped[bool] = mapped_column(Boolean, default=False)
    penalized: Mapped[bool] = mapped_column(Boolean, default=False)
    checked: Mapped[bool] = mapped_column(Boolean, default=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    phase: Mapped[str] = mapped_column(String(20))


class RecordedEvent(Base):
    __tablename__ = 'events'
    __table_args__ = (UniqueConstraint('attempt_id', 'event_id'),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey('attempts.id'))
    event_id: Mapped[str] = mapped_column(String(36))
    data: Mapped[dict] = mapped_column(JSON)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    login: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20))  # admin | teacher | student
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuthSession(Base):
    __tablename__ = 'auth_sessions'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AuthEvent(Base):
    __tablename__ = 'auth_events'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('users.id'), nullable=True)
    login_attempted: Mapped[str | None] = mapped_column(String(120), nullable=True)
    event_type: Mapped[str] = mapped_column(String(40))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)


class LoginThrottle(Base):
    __tablename__ = 'login_throttles'
    key: Mapped[str] = mapped_column(String(160), primary_key=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Grade(Base):
    __tablename__ = 'grades'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Subject(Base):
    __tablename__ = 'subjects'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TeacherSubjectAssignment(Base):
    __tablename__ = 'teacher_subject_assignments'
    __table_args__ = (UniqueConstraint('teacher_user_id', 'subject_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    teacher_user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'))
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey('subjects.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Enrollment(Base):
    __tablename__ = 'enrollments'
    __table_args__ = (UniqueConstraint('student_user_id', 'grade_id', 'subject_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    student_user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'))
    grade_id: Mapped[str] = mapped_column(String(36), ForeignKey('grades.id'))
    subject_id: Mapped[str] = mapped_column(String(36), ForeignKey('subjects.id'))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


def connect(url=None):
    url = url or os.getenv('MONTI_DATABASE_URL', 'sqlite:///./monti.sqlite3')
    options = {'connect_args': {'check_same_thread': False}} if url.startswith('sqlite') else {}
    engine = create_engine(url, **options)
    if url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def sqlite_pragmas(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)
