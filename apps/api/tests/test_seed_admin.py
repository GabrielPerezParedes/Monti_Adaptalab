from monti.auth.seed import seed_admin
from tests.conftest import client_db_url, login_admin


def test_seed_idempotent(school_client):
    url = client_db_url(school_client)
    assert seed_admin(url) == 0
    assert seed_admin(url) == 0
    token = login_admin(school_client)
    assert token
