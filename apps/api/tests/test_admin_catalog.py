from tests.conftest import auth_header, login_admin


def test_admin_catalog_and_duplicates(school_client):
    token = login_admin(school_client)
    h = auth_header(token)
    g = school_client.post('/api/admin/grades', headers=h, json={'name': '4.º de secundaria', 'sort_order': 4})
    assert g.status_code == 201
    assert school_client.post('/api/admin/grades', headers=h, json={'name': '4.º de secundaria', 'sort_order': 4}).status_code == 409
    s = school_client.post('/api/admin/subjects', headers=h, json={'name': 'Física'})
    assert s.status_code == 201
    teacher = school_client.post(
        '/api/admin/users',
        headers=h,
        json={'login': 't@test.local', 'display_name': 'T', 'role': 'teacher', 'password': 'password-teacher'},
    ).json()
    student = school_client.post(
        '/api/admin/users',
        headers=h,
        json={'login': 's@test.local', 'display_name': 'S', 'role': 'student', 'password': 'password-student'},
    ).json()
    a = school_client.post(
        '/api/admin/teacher-assignments',
        headers=h,
        json={'teacher_user_id': teacher['id'], 'subject_id': s.json()['id']},
    )
    assert a.status_code == 201
    assert (
        school_client.post(
            '/api/admin/teacher-assignments',
            headers=h,
            json={'teacher_user_id': teacher['id'], 'subject_id': s.json()['id']},
        ).status_code
        == 409
    )
    e = school_client.post(
        '/api/admin/enrollments',
        headers=h,
        json={'student_user_id': student['id'], 'grade_id': g.json()['id'], 'subject_id': s.json()['id']},
    )
    assert e.status_code == 201
    assert (
        school_client.post(
            '/api/admin/enrollments',
            headers=h,
            json={'student_user_id': student['id'], 'grade_id': g.json()['id'], 'subject_id': s.json()['id']},
        ).status_code
        == 409
    )
