from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from monti.auth.seed import seed_admin
from monti.main import create_app


TEACHER = {'X-Teacher-Key': 'monti-local-teacher'}
ADMIN_LOGIN = 'admin@monti.local'
ADMIN_PASSWORD = 'cambia-esta-clave-segura'


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('MONTI_DEV_TEACHER_KEY', TEACHER['X-Teacher-Key'])
    monkeypatch.setenv('MONTI_FEATURE_SCHOOL_AUTH', 'true')
    monkeypatch.setenv('MONTI_FEATURE_GOOGLE_LOGIN', 'true')
    monkeypatch.setenv('SUPABASE_JWT_SECRET', 'test-jwt-secret-for-monti')
    monkeypatch.setenv('MONTI_GOOGLE_ALLOWED_DOMAIN', 'montessorisucre.edu.bo')
    monkeypatch.setenv('MONTI_ADMIN_LOGIN', ADMIN_LOGIN)
    monkeypatch.setenv('MONTI_ADMIN_PASSWORD', ADMIN_PASSWORD)
    db_url = f'sqlite:///{tmp_path / "google.sqlite3"}'
    assert seed_admin(db_url) == 0
    with TestClient(create_app(db_url)) as client:
        yield client


def admin_headers(client):
    login = client.post(
        '/api/auth/login',
        json={'login': ADMIN_LOGIN, 'password': ADMIN_PASSWORD},
    )
    assert login.status_code == 200, login.text
    return {'Authorization': f'Bearer {login.json()["token"]}'}


def seed_roster(client, email='alumno@montessorisucre.edu.bo', role='student'):
    headers = admin_headers(client)
    # ensure grade/subject exist via admin APIs if needed
    grades = client.get('/api/admin/grades', headers=headers).json()
    subjects = client.get('/api/admin/subjects', headers=headers).json()
    if not grades:
        g = client.post('/api/admin/grades', headers=headers, json={'name': '4B', 'sort_order': 1})
        assert g.status_code == 201
        grades = [g.json()]
    if not subjects:
        s = client.post('/api/admin/subjects', headers=headers, json={'name': 'Fisica'})
        assert s.status_code == 201
        subjects = [s.json()]
    body = {
        'email': email,
        'role': role,
        'display_name': 'Prueba',
        'grade_id': grades[0]['id'] if role == 'student' else None,
        'subject_id': subjects[0]['id'],
        'active': True,
    }
    r = client.post('/api/admin/roster', headers=headers, json=body)
    assert r.status_code == 201, r.text
    return r.json(), headers


def test_health_exposes_google_flag(client):
    health = client.get('/api/health').json()
    assert health['google_login'] is True
    assert health['google_allowed_domain'] == 'montessorisucre.edu.bo'


def test_google_rejects_wrong_domain(client, monkeypatch):
    seed_roster(client, email='ok@montessorisucre.edu.bo')

    def fake_claims(_token):
        return {'email': 'someone@gmail.com', 'sub': 'sub-1', 'email_verified': True}

    monkeypatch.setattr('monti.auth.google_bridge.claims_from_access_token', fake_claims)
    response = client.post('/api/auth/google', json={'access_token': 'fake.token.value'})
    assert response.status_code == 403
    assert 'montessorisucre.edu.bo' in response.json()['detail']


def test_google_rejects_missing_roster(client, monkeypatch):
    def fake_claims(_token):
        return {
            'email': 'nuevo@montessorisucre.edu.bo',
            'sub': 'sub-missing',
            'email_verified': True,
        }

    monkeypatch.setattr('monti.auth.google_bridge.claims_from_access_token', fake_claims)
    response = client.post('/api/auth/google', json={'access_token': 'fake.token.value'})
    assert response.status_code == 403
    assert 'roster' in response.json()['detail'].lower()


def test_google_login_issues_monti_session(client, monkeypatch):
    seed_roster(client, email='alumno@montessorisucre.edu.bo', role='student')

    def fake_claims(_token):
        return {
            'email': 'alumno@montessorisucre.edu.bo',
            'sub': 'google-sub-alumno',
            'email_verified': True,
            'name': 'Alumno Demo',
        }

    monkeypatch.setattr('monti.auth.google_bridge.claims_from_access_token', fake_claims)
    response = client.post('/api/auth/google', json={'access_token': 'fake.token.value'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['user']['role'] == 'student'
    assert data['user']['auth_provider'] == 'google'
    assert data['token']
    me = client.get('/api/auth/me', headers={'Authorization': f'Bearer {data["token"]}'})
    assert me.status_code == 200
    assert me.json()['email'] == 'alumno@montessorisucre.edu.bo'


def test_roster_csv_rejects_password_column(client):
    headers = admin_headers(client)
    bad = 'email,role,password\na@montessorisucre.edu.bo,student,secret\n'
    response = client.post('/api/admin/roster/import-csv', headers=headers, json={'csv_text': bad})
    assert response.status_code == 422
    assert 'prohibida' in response.json()['detail'].lower() or 'password' in response.json()['detail'].lower()


def test_roster_csv_import_and_role_change(client, monkeypatch):
    headers = admin_headers(client)
    subjects = client.get('/api/admin/subjects', headers=headers).json()
    if not subjects:
        s = client.post('/api/admin/subjects', headers=headers, json={'name': 'Fisica'})
        subjects = [s.json()]
    csv_text = (
        'email,role,display_name,subject_id,active\n'
        f'docente@montessorisucre.edu.bo,teacher,Docente,{subjects[0]["id"]},true\n'
    )
    imported = client.post('/api/admin/roster/import-csv', headers=headers, json={'csv_text': csv_text})
    assert imported.status_code == 200, imported.text
    assert imported.json()['created'] == 1

    def fake_claims(_token):
        return {
            'email': 'docente@montessorisucre.edu.bo',
            'sub': 'sub-teacher',
            'email_verified': True,
        }

    monkeypatch.setattr('monti.auth.google_bridge.claims_from_access_token', fake_claims)
    first_resp = client.post('/api/auth/google', json={'access_token': 'fake.token.t1'})
    assert first_resp.status_code == 200, first_resp.text
    first = first_resp.json()
    assert first['user']['role'] == 'teacher'

    rows = client.get('/api/admin/roster', headers=headers).json()
    row = next(r for r in rows if r['email'] == 'docente@montessorisucre.edu.bo')
    patched = client.patch(
        f'/api/admin/roster/{row["id"]}',
        headers=headers,
        json={'role': 'admin'},
    )
    assert patched.status_code == 200
    second_resp = client.post('/api/auth/google', json={'access_token': 'fake.token.t2'})
    assert second_resp.status_code == 200, second_resp.text
    second = second_resp.json()
    assert second['user']['role'] == 'admin'
