from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SimulationStatus(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class SimulationState(BaseModel):
    status: SimulationStatus = SimulationStatus.STOPPED
    current_tick: int = 0
    sim_time: datetime | None = None
    time_scale: int = 60
    population: int = 0
    total_gdp: float = 0.0
    avg_happiness: float = 0.0
    avg_health: float = 0.0
    unemployment_rate: float = 0.0
    active_events: int = 0


class SimulationControl(BaseModel):
    action: str = Field(description="start, stop, pause, resume, or step")
    time_scale: int | None = None
    steps: int | None = Field(default=None, description="Number of ticks for 'step' action")


class ScenarioRequest(BaseModel):
    description: str = Field(description="Natural language scenario to simulate")
    duration_hours: int = Field(default=24, description="Simulation hours to run")


class TickResult(BaseModel):
    tick: int
    sim_time: str
    citizens_processed: int
    events_triggered: int
    transactions: int
    duration_ms: float
