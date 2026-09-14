from tests.conftest import auth_header, login_admin


def _create_catalog(client, token):
    h = auth_header(token)
    g1 = client.post('/api/admin/grades', headers=h, json={'name': '1.º de secundaria', 'sort_order': 1}).json()
    g4 = client.post('/api/admin/grades', headers=h, json={'name': '4.º de secundaria', 'sort_order': 4}).json()
    fisica = client.post('/api/admin/subjects', headers=h, json={'name': 'Física'}).json()
    quimica = client.post('/api/admin/subjects', headers=h, json={'name': 'Química'}).json()
    teacher = client.post(
        '/api/admin/users',
        headers=h,
        json={
            'login': 'prof@test.local',
            'display_name': 'Prof Física',
            'role': 'teacher',
            'password': 'password-teacher',
        },
    ).json()
    client.post(
        '/api/admin/teacher-assignments',
        headers=h,
        json={'teacher_user_id': teacher['id'], 'subject_id': fisica['id']},
    )
    return {'g1': g1, 'g4': g4, 'fisica': fisica, 'quimica': quimica, 'teacher': teacher}


def test_teacher_scope_all_grades_one_subject(school_client):
    token = login_admin(school_client)
    catalog = _create_catalog(school_client, token)
    login = school_client.post('/api/auth/login', json={'login': 'prof@test.local', 'password': 'password-teacher'})
    assert login.status_code == 200
    th = auth_header(login.json()['token'])
    scope = school_client.get('/api/teacher/scope', headers=th).json()
    assert catalog['fisica']['id'] in scope['subject_ids']
    assert catalog['quimica']['id'] not in scope['subject_ids']
    assert len(scope['grades']) >= 2

    denied = school_client.get(f"/api/teacher/enrollments?subject_id={catalog['quimica']['id']}", headers=th)
    assert denied.status_code == 403

    admin_denied = school_client.get('/api/admin/users', headers=th)
    assert admin_denied.status_code == 403
