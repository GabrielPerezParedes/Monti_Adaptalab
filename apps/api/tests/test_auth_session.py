from tests.conftest import auth_header, login_admin


def test_health_school_flag(school_client):
    data = school_client.get('/api/health').json()
    assert data['school_auth'] is True
    assert data['mode'] == 'school-auth'
    assert data['rag'] is False


def test_login_logout_me(school_client):
    token = login_admin(school_client)
    me = school_client.get('/api/auth/me', headers=auth_header(token))
    assert me.status_code == 200
    assert me.json()['role'] == 'admin'
    assert school_client.post('/api/auth/logout', headers=auth_header(token)).status_code == 204
    assert school_client.get('/api/auth/me', headers=auth_header(token)).status_code == 401


def test_bad_credentials_generic(school_client):
    login_admin(school_client)
    r = school_client.post('/api/auth/login', json={'login': 'admin@test.local', 'password': 'wrong-password'})
    assert r.status_code == 401
    assert 'válidas' in r.json()['detail'].lower() or 'valid' in r.json()['detail'].lower() or 'Credenciales' in r.json()['detail']


def test_teacher_key_rejected_when_school_auth(school_client):
    login_admin(school_client)
    r = school_client.get('/api/teacher/labs', headers={'X-Teacher-Key': 'monti-local-teacher'})
    assert r.status_code in {401, 403}
