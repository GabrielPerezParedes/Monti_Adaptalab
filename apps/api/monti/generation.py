"""Reproducible, constrained prototype generator. This is not an LLM/RAG."""
import random
from .physics import solve
from .schemas import LabRequest, LaunchState

RUBRIC = {'procedure': 18, 'comprehension': 14, 'physical': 9, 'efficiency': 4}
SOURCES = [{'id': 'racso-2009-ch8', 'title': 'Problemas de física y cómo resolverlos',
            'director': 'Félix Aucallanchi Velásquez', 'printed_pages': '61–63',
            'pdf_pages': '62–64', 'note': 'Cap. 8: componentes, alcance y gravedad por defecto de 10 m/s².'}]

def generate(request: LabRequest) -> dict:
    rng = random.Random(request.seed)
    height = rng.choice([3, 5, 8]) if request.difficulty == 'advanced' else 0
    speed = rng.choice([14, 16, 18, 20])
    angle = rng.choice([30, 40, 45, 50, 60])
    witness = LaunchState(speed_m_s=speed, angle_deg=angle, height_m=height)
    reference = solve(witness)
    target = round(reference['range_m'], 2)
    public = {
        'schema_version': '0.1', 'rubric_version': '45-v1-draft',
        'generator': 'parametric-prototype', 'seed': request.seed,
        'course': request.course, 'topic': 'Movimiento parabólico', 'difficulty': request.difficulty,
        'title': 'Un lanzamiento, una explicación',
        'instruction': f'Alcanza la marca situada a {target:.2f} m. Compara tus pruebas y explica por qué tu ajuste funciona.',
        'target_m': target, 'tolerance_m': .5,
        'initial': {'speed_m_s': speed, 'angle_deg': 20, 'height_m': height,
                    'gravity_m_s2': 10, 'air_resistance': False},
        'controls': {'angle_deg': {'min': 5, 'max': 85, 'step': 1, 'editable': True},
                     'speed_m_s': {'min': 5, 'max': 25, 'step': 1, 'editable': request.difficulty != 'basic'},
                     'height_m': {'min': height, 'max': height, 'editable': False}},
        'scene': {'projectile': 'ball', 'target_m': target, 'platform_height_m': height},
        'rubric': RUBRIC, 'max_score': 45, 'sources': SOURCES,
        'attempt_policy': {'version': 'draft-1', 'exploration_free': True, 'deduplicate_reset': True},
    }
    return {'public': public, 'private': {'witness': witness.model_dump(), 'reference': reference}}

def validate_launch(state: LaunchState, spec: dict) -> None:
    for key in ['speed_m_s', 'angle_deg', 'height_m']:
        control = spec['controls'][key]
        value = getattr(state, key)
        if not control['min'] <= value <= control['max']:
            raise ValueError(f'{key}: fuera del intervalo de la actividad.')
        if not control['editable'] and abs(value - spec['initial'][key]) > 1e-7:
            raise ValueError(f'{key}: esta variable está fijada por la actividad.')
