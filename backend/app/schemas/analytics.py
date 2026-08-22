from pydantic import BaseModel


class CityMetrics(BaseModel):
    population: int = 0
    employed: int = 0
    unemployed: int = 0
    unemployment_rate: float = 0.0

    avg_happiness: float = 0.0
    avg_health: float = 0.0
    avg_stress: float = 0.0

    total_gdp: float = 0.0
    avg_income: float = 0.0
    total_transactions: int = 0
    inflation_rate: float = 0.0

    active_businesses: int = 0
    total_businesses: int = 0

    active_events: int = 0
    crime_rate: float = 0.0
    pollution_index: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "population": 1000,
                "employed": 850,
                "unemployed": 150,
                "unemployment_rate": 0.15,
                "avg_happiness": 0.72,
                "avg_health": 0.88,
                "avg_stress": 0.35,
                "total_gdp": 5000000.0,
                "avg_income": 3500.0,
            }
        }


class PopulationBreakdown(BaseModel):
    by_age: dict[str, int] = {}
    by_gender: dict[str, int] = {}
    by_education: dict[str, int] = {}
    by_occupation: dict[str, int] = {}
    by_district: dict[str, int] = {}
