"""Shared pytest fixtures for MONTI API."""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from monti.auth.seed import seed_admin as run_seed
from monti.main import create_app


@pytest.fixture
def school_env(monkeypatch):
    monkeypatch.setenv('MONTI_FEATURE_SCHOOL_AUTH', 'true')
    monkeypatch.setenv('MONTI_ADMIN_LOGIN', 'admin@test.local')
    monkeypatch.setenv('MONTI_ADMIN_PASSWORD', 'password-admin-1')
    monkeypatch.setenv('MONTI_LOGIN_MAX_FAILURES', '3')
    monkeypatch.setenv('MONTI_LOGIN_LOCKOUT_MINUTES', '15')
    monkeypatch.setenv('MONTI_SESSION_TTL_MINUTES', '60')


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('MONTI_FEATURE_SCHOOL_AUTH', 'false')
    with TestClient(create_app(f'sqlite:///{tmp_path / "legacy.sqlite3"}')) as c:
        yield c


@pytest.fixture
def school_client(tmp_path, school_env):
    with TestClient(create_app(f'sqlite:///{tmp_path / "school.sqlite3"}')) as c:
        yield c


def auth_header(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def client_db_url(client: TestClient) -> str:
    with client.app.state.session_factory() as session:
        return str(session.get_bind().url)


def login_admin(client: TestClient) -> str:
    assert run_seed(client_db_url(client)) == 0
    response = client.post(
        '/api/auth/login',
        json={'login': os.environ['MONTI_ADMIN_LOGIN'], 'password': os.environ['MONTI_ADMIN_PASSWORD']},
    )
    assert response.status_code == 200, response.text
    return response.json()['token']
