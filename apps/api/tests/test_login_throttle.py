from tests.conftest import login_admin


def test_login_throttle_lockout(school_client):
    login_admin(school_client)
    for _ in range(3):
        school_client.post('/api/auth/login', json={'login': 'nobody@test.local', 'password': 'bad-password-xx'})
    locked = school_client.post('/api/auth/login', json={'login': 'nobody@test.local', 'password': 'bad-password-xx'})
    assert locked.status_code == 429
    assert 'retry_after_seconds' in locked.json()
