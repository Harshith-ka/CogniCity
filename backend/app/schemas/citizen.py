import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from backend.app.models.citizen import Gender, EducationLevel, TransportPreference


class CitizenBase(BaseModel):
    name: str
    age: int = Field(ge=0, le=120)
    gender: Gender
    education: EducationLevel
    occupation: str = "unemployed"
    salary: float = 0.0
    balance: float = 1000.0
    personality_traits: dict = Field(default_factory=dict)
    goals: list[str] = Field(default_factory=list)
    happiness: float = Field(default=0.7, ge=0.0, le=1.0)
    stress: float = Field(default=0.3, ge=0.0, le=1.0)
    health: float = Field(default=0.9, ge=0.0, le=1.0)
    energy: float = Field(default=1.0, ge=0.0, le=1.0)
    hunger: float = Field(default=0.0, ge=0.0, le=1.0)
    social_need: float = Field(default=0.5, ge=0.0, le=1.0)
    political_opinion: float = Field(default=0.5, ge=0.0, le=1.0)
    transport_preference: TransportPreference = TransportPreference.WALKING


class CitizenCreate(CitizenBase):
    pass


class CitizenUpdate(BaseModel):
    name: str | None = None
    occupation: str | None = None
    salary: float | None = None
    balance: float | None = None
    happiness: float | None = None
    stress: float | None = None
    health: float | None = None
    energy: float | None = None
    hunger: float | None = None
    current_activity: str | None = None


class CitizenResponse(CitizenBase):
    id: uuid.UUID
    current_activity: str
    is_alive: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CitizenSummary(BaseModel):
    id: uuid.UUID
    name: str
    age: int
    gender: Gender
    occupation: str
    happiness: float
    stress: float
    health: float
    energy: float
    balance: float
    personality_traits: dict = Field(default_factory=dict)
    current_activity: str
    x: float | None = None
    y: float | None = None
    district_name: str | None = None

    model_config = {"from_attributes": True}
