from tests.conftest import auth_header, login_admin


def test_student_enrollment_isolation(school_client):
    admin = login_admin(school_client)
    h = auth_header(admin)
    grade = school_client.post('/api/admin/grades', headers=h, json={'name': '4.º de secundaria', 'sort_order': 4}).json()
    other_grade = school_client.post('/api/admin/grades', headers=h, json={'name': '3.º de secundaria', 'sort_order': 3}).json()
    subject = school_client.post('/api/admin/subjects', headers=h, json={'name': 'Física'}).json()
    student = school_client.post(
        '/api/admin/users',
        headers=h,
        json={'login': 'alumno@test.local', 'display_name': 'Ana', 'role': 'student', 'password': 'password-student'},
    ).json()
    other = school_client.post(
        '/api/admin/users',
        headers=h,
        json={'login': 'otro@test.local', 'display_name': 'Luis', 'role': 'student', 'password': 'password-student'},
    ).json()
    enrollment = school_client.post(
        '/api/admin/enrollments',
        headers=h,
        json={'student_user_id': student['id'], 'grade_id': grade['id'], 'subject_id': subject['id']},
    ).json()
    other_enrollment = school_client.post(
        '/api/admin/enrollments',
        headers=h,
        json={'student_user_id': other['id'], 'grade_id': other_grade['id'], 'subject_id': subject['id']},
    ).json()

    teacher = school_client.post(
        '/api/admin/users',
        headers=h,
        json={'login': 'docente@test.local', 'display_name': 'Doc', 'role': 'teacher', 'password': 'password-teacher'},
    ).json()
    school_client.post(
        '/api/admin/teacher-assignments',
        headers=h,
        json={'teacher_user_id': teacher['id'], 'subject_id': subject['id']},
    )
    teacher_login = school_client.post('/api/auth/login', json={'login': 'docente@test.local', 'password': 'password-teacher'})
    th = auth_header(teacher_login.json()['token'])
    lab = school_client.post(
        '/api/teacher/labs',
        headers=th,
        json={'course': '4.º', 'difficulty': 'basic', 'seed': 1, 'grade_id': grade['id'], 'subject_id': subject['id']},
    ).json()
    school_client.post(f"/api/teacher/labs/{lab['id']}/publish", headers=th)

    student_login = school_client.post('/api/auth/login', json={'login': 'alumno@test.local', 'password': 'password-student'})
    sh = auth_header(student_login.json()['token'])
    ok = school_client.post(
        f"/api/labs/{lab['id']}/join",
        headers=sh,
        json={'enrollment_id': enrollment['id']},
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()['token']

    bad = school_client.post(
        f"/api/labs/{lab['id']}/join",
        headers=sh,
        json={'enrollment_id': other_enrollment['id']},
    )
    assert bad.status_code == 403

    assert school_client.get('/api/admin/users', headers=sh).status_code == 403
    assert school_client.get('/api/teacher/labs', headers=sh).status_code == 403
