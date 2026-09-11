"""Independent ideal projectile verifier: SI, upward-positive y, no air drag."""
from math import cos, sin, radians, sqrt
from .schemas import LaunchState

def solve(state: LaunchState) -> dict:
    vx = state.speed_m_s * cos(radians(state.angle_deg))
    vy = state.speed_m_s * sin(radians(state.angle_deg))
    g = state.gravity_m_s2
    t = (vy + sqrt(vy * vy + 2 * g * state.height_m)) / g
    return {
        'range_m': vx * t,
        'flight_time_s': t,
        'max_height_m': state.height_m + max(vy, 0)**2 / (2*g),
    }

def efficiency(penalized_runs: int) -> float:
    if penalized_runs < 0:
        raise ValueError('Attempt count must be nonnegative.')
    return max(0.0, 4 - .25 * penalized_runs * (penalized_runs + 1))
