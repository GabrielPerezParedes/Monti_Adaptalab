from math import sqrt
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from monti.main import create_app
from monti.generation import generate, validate_launch
from monti.physics import efficiency, learning_evidence_score, solve
from monti.schemas import LabRequest, LaunchState

TEACHER = {'X-Teacher-Key': 'monti-local-teacher'}

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('MONTI_DEV_TEACHER_KEY', TEACHER['X-Teacher-Key'])
    with TestClient(create_app(f'sqlite:///{tmp_path / "test.sqlite3"}')) as client:
        yield client

def activity(client, difficulty='basic'):
    request = {'seed': 42, 'difficulty': difficulty}
    response = client.post('/api/teacher/labs', headers=TEACHER, json=request)
    assert response.status_code == 201
    lab = response.json()
    assert lab['rubric_version'] == '45-v1'
    assert lab['rubric']['learning_evidence'] == 4
    assert lab['attempt_policy']['version'] == '1.0'
    assert client.post(f'/api/teacher/labs/{lab["id"]}/publish', headers=TEACHER).status_code == 200
    a = client.post(f'/api/labs/{lab["id"]}/join', json={'alias': 'Prueba 01'}).json()
    return lab, a, {'X-Attempt-Token': a['token']}, generate(LabRequest(**request))['private']['witness']

def event(kind, **kwargs):
    return {'id': str(uuid4()), 'kind': kind, **kwargs}

def completed(client, attempt, headers, state, observed=None, extra=None):
    run = str(uuid4())
    expected = solve(LaunchState(**state))
    events = list(extra or [])
    events += [
        event('launch', run_id=run, state=state),
        event('landed', run_id=run, observed_range_m=expected['range_m'] if observed is None else observed),
    ]
    r = client.post(f'/api/attempts/{attempt["id"]}/events', headers=headers, json={'events': events})
    assert r.status_code == 200, r.text
    return run, events

def test_physics_reference_cases_and_units():
    level = solve(LaunchState(speed_m_s=20, angle_deg=45, height_m=0))
    assert level['range_m'] == pytest.approx(40)
    assert level['flight_time_s'] == pytest.approx(2 * sqrt(2))
    assert level['max_height_m'] == pytest.approx(10)
    horizontal = solve(LaunchState(speed_m_s=10, angle_deg=0, height_m=5))
    assert horizontal == pytest.approx({'range_m': 10, 'flight_time_s': 1, 'max_height_m': 5})
    for invalid in [float('nan'), float('inf'), -1, 31]:
        with pytest.raises(ValidationError):
            LaunchState(speed_m_s=invalid, angle_deg=45, height_m=0)
    assert [learning_evidence_score(n) for n in range(6)] == [4, 3.5, 2.5, 1, 0, 0]
    assert [efficiency(n) for n in range(6)] == [4, 3.5, 2.5, 1, 0, 0]

@pytest.mark.parametrize('difficulty', ['basic', 'medium', 'advanced'])
def test_generated_targets_are_reproducible_and_reachable(difficulty):
    for seed in range(100):
        request = LabRequest(seed=seed, difficulty=difficulty)
        a = generate(request)
        assert a == generate(request)
        witness = LaunchState(**a['private']['witness'])
        validate_launch(witness, a['public'])
        assert abs(solve(witness)['range_m'] - a['public']['target_m']) <= a['public']['tolerance_m']
        assert sum(a['public']['rubric'].values()) == 45
        assert a['public']['rubric_version'] == '45-v1'

def test_draft_is_hidden_and_tokens_separate_sessions(client):
    assert client.post('/api/teacher/labs', json={}).status_code == 403
    lab = client.post('/api/teacher/labs', headers=TEACHER, json={}).json()
    public = client.get(f'/api/labs/{lab["id"]}').json()
    assert public['spec'] is None and public['published'] is False
    assert client.post(f'/api/labs/{lab["id"]}/join', json={'alias': 'A'}).status_code == 409
    published_lab, attempt, _, _ = activity(client)
    assert client.get(f'/api/attempts/{attempt["id"]}/report').status_code == 403
    published = client.get(f'/api/labs/{published_lab["id"]}').json()
    assert published['published'] and 'private' not in published['spec']

def test_evaluation_emits_monti_scores_and_report(client):
    lab, a, headers, witness = activity(client)
    public = client.get(f'/api/labs/{lab["id"]}').json()
    assert 'private' not in public['spec'] and 'witness' not in public['spec']
    client.post(f'/api/attempts/{a["id"]}/evaluate', headers=headers)
    control = event('control', control='angle_deg', value=45)
    run, events = completed(client, a, headers, witness, extra=[control])
    base = f'/api/attempts/{a["id"]}'
    client.post(base + '/events', headers=headers, json={'events': events})
    client.post(base + '/explanations', headers=headers, json={
        'text': 'Ajusté el ángulo cerca de 45° porque el alcance horizontal depende de la rapidez y del tiempo de vuelo con g = 10.'
    })
    response = client.post(base + '/submit', headers=headers, json={'run_id': run})
    assert response.status_code == 200
    r = response.json()
    assert r['scores'] == {
        'procedure': 18.0,
        'comprehension': 14.0,
        'physical': 9,
        'learning_evidence': 4.0,
    }
    assert r['total'] == 45
    assert r['status'] == 'scored'
    assert r['rubric_version'] == '45-v1'
    assert client.post(base + '/submit', headers=headers, json={'run_id': run}).json()['penalized_runs'] == 0
    text = client.get(base + '/report.txt', headers=headers).text
    assert 'Alcance:' in text and '45' in text and 'Evidencia de aprendizaje' in text
    assert 'cargar a registros' in text.lower() or 'Cargar' in text or 'registros' in text
    assert client.get(f'/api/teacher/labs/{lab["id"]}/report.txt').status_code == 403
    class_text = client.get(f'/api/teacher/labs/{lab["id"]}/report.txt', headers=TEACHER).text
    assert 'Prueba 01' in class_text and 'Alcance:' in class_text
    assert len(r['evidence']) >= 2

def test_exploration_is_free_and_a_failed_run_is_penalized_only_once(client):
    lab, a, headers, _ = activity(client)
    base = f'/api/attempts/{a["id"]}'
    state = {**lab['initial'], 'angle_deg': 5}
    practice, _ = completed(client, a, headers, state)
    assert client.post(base + '/submit', headers=headers, json={'run_id': practice}).status_code == 409
    client.post(base + '/events', headers=headers, json={'events': [event('reset')]})
    assert client.get(base + '/report', headers=headers).json()['penalized_runs'] == 0
    client.post(base + '/evaluate', headers=headers)
    run, events = completed(client, a, headers, state)
    first = client.post(base + '/submit', headers=headers, json={'run_id': run}).json()
    assert first['passed'] is False and first['scores']['learning_evidence'] == 3.5
    client.post(base + '/submit', headers=headers, json={'run_id': run})
    client.post(base + '/events', headers=headers, json={'events': events + [event('reset'), event('erase')]})
    assert client.get(base + '/report', headers=headers).json()['penalized_runs'] == 1
    other, _ = completed(client, a, headers, state)
    reset = event('reset')
    for _ in range(2):
        assert client.post(base + '/events', headers=headers, json={'events': [reset]}).status_code == 200
    assert client.get(base + '/report', headers=headers).json()['penalized_runs'] == 2
    assert client.post(base + '/submit', headers=headers, json={'run_id': other}).status_code == 409

def test_technical_failure_reset_is_not_penalized(client):
    lab, a, headers, witness = activity(client)
    base = f'/api/attempts/{a["id"]}'
    client.post(base + '/evaluate', headers=headers)
    state = {**lab['initial'], 'angle_deg': 5}
    completed(client, a, headers, state)
    assert client.post(base + '/events', headers=headers, json={
        'events': [event('reset', technical_failure=True)]
    }).status_code == 200
    assert client.get(base + '/report', headers=headers).json()['penalized_runs'] == 0
    other, _ = completed(client, a, headers, witness, extra=[event('control', control='angle_deg', value=45)])
    scored = client.post(base + '/submit', headers=headers, json={'run_id': other}).json()
    assert scored['passed'] is True
    assert scored['scores']['learning_evidence'] == 4
    assert scored['penalized_runs'] == 0

def test_untrusted_events_cannot_change_the_activity_or_claim_a_score(client):
    lab, a, headers, witness = activity(client)
    base = f'/api/attempts/{a["id"]}'
    client.post(base + '/evaluate', headers=headers)
    invalid = event('launch', run_id=str(uuid4()), state={**witness, 'speed_m_s': 26})
    assert client.post(base + '/events', headers=headers, json={'events': [invalid]}).status_code == 422
    run, events = completed(client, a, headers, witness, observed=999)
    assert client.post(base + '/submit', headers=headers, json={'run_id': run}).status_code == 409
    assert client.post(base + '/submit', headers=headers, json={'run_id': run, 'score': 45}).status_code == 422
    modified = {**events[0], 'state': {**witness, 'angle_deg': 5}}
    assert client.post(base + '/events', headers=headers, json={'events': [modified]}).status_code == 409
    other = client.post(f'/api/labs/{lab["id"]}/join', json={'alias': 'Prueba 02'}).json()
    assert client.get(base + '/report', headers={'X-Attempt-Token': other['token']}).status_code == 403
    assert client.post(f'/api/attempts/{other["id"]}/events', headers={'X-Attempt-Token': other['token']},
                       json={'events': [event('landed', run_id=run)]}).status_code == 403

def test_a_rejected_batch_rolls_back_prior_events(client):
    _, a, headers, witness = activity(client)
    base = f'/api/attempts/{a["id"]}'
    first = event('launch', run_id=str(uuid4()), state=witness)
    unknown = event('landed', run_id=str(uuid4()))
    assert client.post(base + '/events', headers=headers, json={'events': [first, unknown]}).status_code == 409
    assert client.get(base + '/report', headers=headers).json()['run_count'] == 0
