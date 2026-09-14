"""Local teaching prototype with optional school authentication."""
from hashlib import sha256
from math import isclose
from secrets import token_urlsafe, compare_digest
from uuid import uuid4
import os
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .database import Attempt, Enrollment, Lab, RecordedEvent, Run, User, connect, now
from .generation import generate, validate_launch
from .physics import efficiency, solve
from .schemas import EventBatch, Explanation, JoinRequest, LabRequest, LaunchState, Submission, TeacherReview
from .auth.deps import (
    bearer_token,
    require_teacher_subject,
    school_auth_enabled,
    teacher_subject_ids,
)
from .auth.router import create_auth_router
from .auth.sessions import resolve_session


def create_app(database_url=None):
    sessions = connect(database_url)
    app = FastAPI(
        title='MONTI · integración local',
        version='1.1.0',
        description='Laboratorio local. Autenticación escolar opcional vía MONTI_FEATURE_SCHOOL_AUTH.',
    )
    app.state.session_factory = sessions
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv('MONTI_CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(','),
        allow_methods=['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization', 'X-Attempt-Token', 'X-Teacher-Key'],
    )
    app.include_router(create_auth_router())

    def db():
        with sessions() as session:
            try:
                yield session
            except IntegrityError as e:
                session.rollback()
                raise HTTPException(409, 'Escritura concurrente: reintenta la misma solicitud.') from e

    def teacher_user(
        request: Request,
        session=Depends(db),
        authorization: str | None = Header(default=None),
        x_teacher_key: str = Header(default=''),
    ) -> User | None:
        if school_auth_enabled():
            token = bearer_token(authorization)
            if not token:
                raise HTTPException(401, 'Debes iniciar sesión.')
            user = resolve_session(session, token)
            if not user or user.role not in {'admin', 'teacher'}:
                raise HTTPException(403, 'Se requiere rol docente o administrador.')
            return user
        expected = os.getenv('MONTI_DEV_TEACHER_KEY', 'monti-local-teacher')
        if not compare_digest(x_teacher_key, expected):
            raise HTTPException(403, 'Se requiere la clave docente de desarrollo.')
        return None

    def get_lab(session, code):
        lab = session.get(Lab, code)
        if not lab:
            raise HTTPException(404, 'Actividad no encontrada.')
        return lab

    def owned(session, attempt_id, token):
        attempt = session.get(Attempt, attempt_id)
        if not attempt or not compare_digest(attempt.token_hash, sha256(token.encode()).hexdigest()):
            raise HTTPException(403, 'Sesión de estudiante no válida.')
        return attempt

    def runs_for(session, attempt):
        return list(session.scalars(select(Run).where(Run.attempt_id == attempt.id)))

    def report(session, attempt):
        runs = runs_for(session, attempt)
        events = list(session.scalars(select(RecordedEvent).where(RecordedEvent.attempt_id == attempt.id).order_by(RecordedEvent.id)))
        final = session.get(Run, attempt.final_run_id) if attempt.final_run_id else None
        review = attempt.reviews[-1] if attempt.reviews else None
        if review and (review['run_id'] != attempt.final_run_id or
                       review['explanation_count'] != len(attempt.explanations) or
                       review['event_count'] != len(events)):
            review = None
        physical = 9 if final and final.passed else (0 if final else None)
        penalties = sum(r.penalized for r in runs)
        scores = {'procedure': review['procedure'] if review else None,
                  'comprehension': review['comprehension'] if review else None,
                  'physical': physical, 'efficiency': efficiency(penalties)}
        total = round(sum(scores.values()), 2) if all(v is not None for v in scores.values()) else None
        result = solve(LaunchState(**final.initial)) if final else None
        summary = f'Realizó {len(runs)} lanzamientos. Se registraron {penalties} fallos o reinicios computables y {len(attempt.explanations)} explicaciones.'
        if final:
            summary += ' El último resultado entregado ' + ('alcanzó el objetivo.' if final.passed else 'quedó fuera de la tolerancia.')
        return {'id': attempt.id, 'alias': attempt.alias, 'lab_id': attempt.lab_id, 'phase': attempt.phase,
                'run_count': len(runs), 'penalized_runs': penalties, 'scores': scores, 'total': total, 'max_score': 45,
                'status': 'reviewed' if total is not None else 'pending', 'result': result,
                'passed': final.passed if final else None, 'summary': summary, 'explanations': attempt.explanations,
                'reviews': attempt.reviews, 'evidence': [e.data for e in events],
                'submitted_state': final.initial if final else None}

    @app.get('/api/health')
    def health():
        enabled = school_auth_enabled()
        return {
            'status': 'ok',
            'mode': 'school-auth' if enabled else 'local-prototype',
            'school_auth': enabled,
            'rag': False,
            'generative_tutor': False,
            'voice': 'browser',
            'generative_voice': False,
        }

    @app.get('/api/teacher/labs')
    def labs(session=Depends(db), actor: User | None = Depends(teacher_user)):
        rows = list(session.scalars(select(Lab).order_by(Lab.created_at.desc())))
        if school_auth_enabled() and actor and actor.role == 'teacher':
            allowed = set(teacher_subject_ids(session, actor))
            rows = [l for l in rows if l.subject_id is None or l.subject_id in allowed]
        return [{'id': l.id, 'published': l.published, 'grade_id': l.grade_id, 'subject_id': l.subject_id, **l.data['public']} for l in rows]

    @app.post('/api/teacher/labs', status_code=201)
    def new_lab(request: LabRequest, session=Depends(db), actor: User | None = Depends(teacher_user)):
        if school_auth_enabled() and actor and actor.role == 'teacher':
            require_teacher_subject(session, actor, request.subject_id)
        lab = Lab(
            id=uuid4().hex[:10],
            data=generate(request),
            grade_id=request.grade_id,
            subject_id=request.subject_id,
        )
        session.add(lab)
        session.commit()
        return {'id': lab.id, 'published': lab.published, 'grade_id': lab.grade_id, 'subject_id': lab.subject_id, **lab.data['public']}

    @app.post('/api/teacher/labs/{code}/publish')
    def publish(code: str, session=Depends(db), actor: User | None = Depends(teacher_user)):
        lab = get_lab(session, code)
        if school_auth_enabled() and actor and actor.role == 'teacher':
            require_teacher_subject(session, actor, lab.subject_id)
        lab.published = True
        session.commit()
        return {'id': lab.id, 'published': True}

    @app.get('/api/labs/{code}')
    def public_lab(code: str, session=Depends(db)):
        lab = get_lab(session, code)
        return {'id': code, 'published': lab.published, 'spec': lab.data['public'] if lab.published else None}

    @app.post('/api/labs/{code}/join', status_code=201)
    def join(
        code: str,
        request: JoinRequest,
        session=Depends(db),
        authorization: str | None = Header(default=None),
    ):
        lab = get_lab(session, code)
        if not lab.published:
            raise HTTPException(409, 'La profesora todavía está preparando la actividad.')
        token = token_urlsafe(32)
        if school_auth_enabled():
            bearer = bearer_token(authorization)
            if not bearer:
                raise HTTPException(401, 'Debes iniciar sesión.')
            user = resolve_session(session, bearer)
            if not user or user.role not in {'student', 'admin'}:
                raise HTTPException(403, 'Se requiere una cuenta de alumno.')
            if not request.enrollment_id:
                raise HTTPException(422, 'Indica la matrícula (enrollment_id).')
            enrollment = session.get(Enrollment, request.enrollment_id)
            if not enrollment or not enrollment.is_active:
                raise HTTPException(403, 'Matrícula no válida.')
            if user.role == 'student' and enrollment.student_user_id != user.id:
                raise HTTPException(403, 'La matrícula no te pertenece.')
            if lab.grade_id and enrollment.grade_id != lab.grade_id:
                raise HTTPException(403, 'La matrícula no corresponde al grado de la actividad.')
            if lab.subject_id and enrollment.subject_id != lab.subject_id:
                raise HTTPException(403, 'La matrícula no corresponde a la asignatura de la actividad.')
            alias = user.display_name[:40]
            attempt = Attempt(
                id=str(uuid4()),
                lab_id=code,
                alias=alias,
                token_hash=sha256(token.encode()).hexdigest(),
                user_id=user.id,
                enrollment_id=enrollment.id,
            )
        else:
            if not request.alias or not request.alias.strip():
                raise HTTPException(422, 'Escribe un alias de prueba.')
            attempt = Attempt(
                id=str(uuid4()),
                lab_id=code,
                alias=request.alias.strip(),
                token_hash=sha256(token.encode()).hexdigest(),
            )
        session.add(attempt)
        session.commit()
        return {'id': attempt.id, 'token': token, 'phase': attempt.phase}

    @app.post('/api/attempts/{attempt_id}/evaluate')
    def start_evaluation(attempt_id: str, session=Depends(db), x_attempt_token: str = Header(default='')):
        attempt = owned(session, attempt_id, x_attempt_token)
        attempt.phase = 'evaluation'
        session.commit()
        return {'phase': attempt.phase}

    @app.post('/api/attempts/{attempt_id}/events')
    def events(attempt_id: str, batch: EventBatch, session=Depends(db), x_attempt_token: str = Header(default='')):
        attempt = owned(session, attempt_id, x_attempt_token)
        spec = get_lab(session, attempt.lab_id).data['public']
        accepted = []
        for event in batch.events:
            payload = event.model_dump(mode='json')
            existing = session.scalar(select(RecordedEvent).where(RecordedEvent.attempt_id == attempt.id, RecordedEvent.event_id == str(event.id)))
            if existing:
                if existing.data != payload:
                    raise HTTPException(409, 'Un ID de evento no puede cambiar su contenido.')
                accepted.append(str(event.id))
                continue
            run = session.get(Run, str(event.run_id)) if event.run_id else None
            if run and run.attempt_id != attempt.id:
                raise HTTPException(403, 'El lanzamiento pertenece a otra sesión.')
            if event.kind == 'launch':
                if run:
                    raise HTTPException(409, 'Lanzamiento ya registrado con otro evento.')
                try:
                    validate_launch(event.state, spec)
                except ValueError as e:
                    raise HTTPException(422, str(e)) from e
                session.add(Run(id=str(event.run_id), attempt_id=attempt.id, initial=event.state.model_dump(), phase=attempt.phase))
            elif event.kind in {'landed', 'invalidated'}:
                if not run:
                    raise HTTPException(409, 'Primero debe registrarse el lanzamiento.')
                if event.kind == 'invalidated':
                    run.invalid = True
                else:
                    run.landed = True
                    expected = solve(LaunchState(**run.initial))
                    if event.observed_range_m is not None and not isclose(event.observed_range_m, expected['range_m'], abs_tol=.05):
                        run.invalid = True
            elif event.kind in {'reset', 'erase'}:
                for active in runs_for(session, attempt):
                    if not active.checked and not active.abandoned:
                        active.abandoned = True
                        if active.phase == 'evaluation':
                            active.penalized = True
            session.add(RecordedEvent(attempt_id=attempt.id, event_id=str(event.id), data=payload))
            session.flush()
            accepted.append(str(event.id))
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(409, 'Eventos concurrentes: reintenta el mismo lote.') from e
        return {'accepted': accepted}

    @app.post('/api/attempts/{attempt_id}/submit')
    def submit(attempt_id: str, submission: Submission, session=Depends(db), x_attempt_token: str = Header(default='')):
        attempt = owned(session, attempt_id, x_attempt_token)
        run = session.get(Run, str(submission.run_id))
        if not run or run.attempt_id != attempt.id:
            raise HTTPException(404, 'Lanzamiento no encontrado.')
        if attempt.phase != 'evaluation' or run.phase != 'evaluation':
            raise HTTPException(409, 'Inicia la evaluación y realiza un lanzamiento nuevo.')
        if not run.landed or run.invalid or run.abandoned:
            raise HTTPException(409, 'Entrega un lanzamiento finalizado, válido y sin reiniciar.')
        spec = get_lab(session, attempt.lab_id).data['public']
        if not run.checked:
            value = solve(LaunchState(**run.initial))['range_m']
            run.passed = abs(value - spec['target_m']) <= spec['tolerance_m'] + 1e-9
            run.checked = True
            run.penalized = not run.passed
            attempt.final_run_id = run.id
            session.commit()
        return report(session, attempt)

    @app.post('/api/attempts/{attempt_id}/explanations')
    def explain(attempt_id: str, explanation: Explanation, session=Depends(db), x_attempt_token: str = Header(default='')):
        attempt = owned(session, attempt_id, x_attempt_token)
        attempt.explanations = [*attempt.explanations, {'text': explanation.text, 'received_at': now().isoformat()}]
        session.commit()
        return {'saved': True}

    @app.get('/api/attempts/{attempt_id}/prompt')
    def prompt(attempt_id: str, session=Depends(db), x_attempt_token: str = Header(default='')):
        attempt = owned(session, attempt_id, x_attempt_token)
        count = len(runs_for(session, attempt))
        prompts = [
            '¿Qué variable vas a cambiar primero y qué efecto esperas sobre el alcance?',
            '¿Cómo se compara la trayectoria observada con tu predicción inicial?',
            '¿Qué cambió entre tus lanzamientos y qué evidencia explica esa diferencia?',
            '¿Qué diferencias esperas entre lanzar a 30° y a 60° con la misma rapidez? Justifica tu predicción.',
        ]
        return {'mode': 'rule-based-guide', 'text': prompts[min(count, 3)], 'source': 'racso-2009-ch8'}

    @app.get('/api/attempts/{attempt_id}/report')
    def student_report(attempt_id: str, session=Depends(db), x_attempt_token: str = Header(default='')):
        return report(session, owned(session, attempt_id, x_attempt_token))

    def report_text(data):
        labels = {'procedure': 'Procedimiento /18', 'comprehension': 'Comprensión /14', 'physical': 'Resultado físico /9', 'efficiency': 'Eficiencia /4'}
        result_lines = []
        if data['result']:
            s, r = data['submitted_state'], data['result']
            result_lines = [f"Condiciones entregadas: rapidez {s['speed_m_s']} m/s; ángulo {s['angle_deg']}°; altura {s['height_m']} m.",
                            f"Alcance: {r['range_m']:.3f} m. Tiempo: {r['flight_time_s']:.3f} s. Altura máxima: {r['max_height_m']:.3f} m."]
        text = '\n'.join(['MONTI · Resumen de actividad', f"Estudiante: {data['alias']}", f"Actividad: {data['lab_id']}",
                          data['summary'], f"Puntaje: {data['total'] if data['total'] is not None else 'Pendiente de revisión'} / 45",
                          *result_lines,
                          *[f'{labels[key]}: {value if value is not None else "Pendiente"}' for key, value in data['scores'].items()],
                          'Última explicación: ' + (data['explanations'][-1]['text'] if data['explanations'] else 'Sin explicación registrada.')])
        return text

    @app.get('/api/attempts/{attempt_id}/report.txt', response_class=PlainTextResponse)
    def export(attempt_id: str, session=Depends(db), x_attempt_token: str = Header(default='')):
        data = report(session, owned(session, attempt_id, x_attempt_token))
        return PlainTextResponse(report_text(data), headers={'Content-Disposition': f'attachment; filename="monti-{attempt_id}.txt"'})

    @app.get('/api/teacher/labs/{code}/report.txt', response_class=PlainTextResponse)
    def class_export(code: str, session=Depends(db), actor: User | None = Depends(teacher_user)):
        lab = get_lab(session, code)
        if school_auth_enabled() and actor and actor.role == 'teacher':
            require_teacher_subject(session, actor, lab.subject_id)
        rows = [report_text(report(session, a)) for a in session.scalars(select(Attempt).where(Attempt.lab_id == code))]
        text = f"MONTI · {lab.data['public']['course']}\n{lab.data['public']['instruction']}\n\n" + '\n\n'.join(rows)
        return PlainTextResponse(text, headers={'Content-Disposition': f'attachment; filename="monti-curso-{lab.id}.txt"'})

    @app.get('/api/teacher/labs/{code}/results')
    def results(code: str, session=Depends(db), actor: User | None = Depends(teacher_user)):
        lab = get_lab(session, code)
        if school_auth_enabled() and actor and actor.role == 'teacher':
            require_teacher_subject(session, actor, lab.subject_id)
        return [report(session, a) for a in session.scalars(select(Attempt).where(Attempt.lab_id == code))]

    @app.post('/api/teacher/attempts/{attempt_id}/review')
    def review(attempt_id: str, value: TeacherReview, session=Depends(db), actor: User | None = Depends(teacher_user)):
        attempt = session.get(Attempt, attempt_id)
        if not attempt or not attempt.final_run_id:
            raise HTTPException(409, 'El estudiante todavía no entregó un resultado.')
        lab = get_lab(session, attempt.lab_id)
        if school_auth_enabled() and actor and actor.role == 'teacher':
            require_teacher_subject(session, actor, lab.subject_id)
        event_count = len(list(session.scalars(select(RecordedEvent.id).where(RecordedEvent.attempt_id == attempt.id))))
        attempt.reviews = [*attempt.reviews, {**value.model_dump(), 'reviewed_at': now().isoformat(),
                                            'run_id': attempt.final_run_id, 'explanation_count': len(attempt.explanations),
                                            'event_count': event_count}]
        session.commit()
        return report(session, attempt)

    return app


app = create_app()
