"""Deterministic rubric bands for procedure and comprehension (no generative AI)."""
from __future__ import annotations

PROCEDURE_MAX = 18.0
COMPREHENSION_MAX = 14.0

_KEYWORDS = (
    'alcance', 'ángulo', 'angulo', 'rapidez', 'velocidad', 'componente',
    'horizontal', 'gravedad', 'trayectoria', 'objetivo', 'tolerancia', 'ángulo',
)


def score_procedure(events: list[dict]) -> float:
    """Map telemetry to 0 / 50 / 100 % of Procedimiento (0, 9, 18)."""
    kinds = [e.get('kind') for e in events]
    has_launch = 'launch' in kinds
    has_landed = 'landed' in kinds
    has_control = 'control' in kinds
    has_measure = 'measurement' in kinds
    if not (has_launch and has_landed):
        return 0.0
    if has_control or has_measure:
        return PROCEDURE_MAX
    return PROCEDURE_MAX * 0.5


def score_comprehension(explanations: list[dict]) -> float:
    """Map confirmed explanations to 0 / 50 / 100 % of Comprensión (0, 7, 14)."""
    if not explanations:
        return 0.0
    text = ' '.join(str(item.get('text', '')) for item in explanations).strip().lower()
    if not text:
        return 0.0
    hits = sum(1 for word in _KEYWORDS if word in text)
    if hits >= 2 or len(text) >= 80:
        return COMPREHENSION_MAX
    return COMPREHENSION_MAX * 0.5
