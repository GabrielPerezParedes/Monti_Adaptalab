import os
from datetime import datetime, timezone
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, UniqueConstraint, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

def now():
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass

class Lab(Base):
    __tablename__ = 'labs'
    id: Mapped[str] = mapped_column(String(12), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

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
