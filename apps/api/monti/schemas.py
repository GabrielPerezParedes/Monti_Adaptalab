from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class LabRequest(StrictModel):
    course: str = Field(default='4.º de secundaria', min_length=1, max_length=60)
    difficulty: Literal['basic', 'medium', 'advanced'] = 'basic'
    seed: int = Field(default=42, ge=0, le=2**31-1)

class JoinRequest(StrictModel):
    alias: str = Field(min_length=1, max_length=40, pattern=r'^[\w áéíóúñÁÉÍÓÚÑ.-]+$')

class LaunchState(StrictModel):
    speed_m_s: float = Field(gt=0, le=30)
    angle_deg: float = Field(ge=0, le=90)
    height_m: float = Field(ge=0, le=15)
    gravity_m_s2: Literal[10.0] = 10.0
    air_resistance: Literal[False] = False

class SimEvent(StrictModel):
    id: UUID
    kind: Literal['control', 'launch', 'landed', 'reset', 'erase', 'measurement', 'pause', 'invalidated']
    run_id: UUID | None = None
    state: LaunchState | None = None
    control: str | None = Field(default=None, max_length=80)
    value: float | bool | str | None = None
    observed_range_m: float | None = None
    observed_time_s: float | None = Field(default=None, ge=0)

    @model_validator(mode='after')
    def check_payload(self):
        if self.kind in {'launch', 'landed', 'invalidated'} and self.run_id is None:
            raise ValueError('This event needs a run_id.')
        if self.kind == 'launch' and self.state is None:
            raise ValueError('A launch needs its initial conditions.')
        if isinstance(self.value, str) and len(self.value) > 120:
            raise ValueError('Control value is too long.')
        return self

class EventBatch(StrictModel):
    events: list[SimEvent] = Field(min_length=1, max_length=100)

class Explanation(StrictModel):
    text: str = Field(min_length=1, max_length=2000)

class Submission(StrictModel):
    run_id: UUID

class TeacherReview(StrictModel):
    procedure: float = Field(ge=0, le=18)
    comprehension: float = Field(ge=0, le=14)
    reason: str = Field(min_length=5, max_length=1000)
