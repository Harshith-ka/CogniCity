"""
Weather & Environment Engine: Dynamic weather simulation.
Weather affects citizen mood, health, traffic speed, and crime rates.
Seasons cycle based on sim day count. Conditions change every few ticks
with smooth transitions and occasional extreme events.
"""

from __future__ import annotations

import math
import random
from datetime import datetime

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.weather import WeatherState

log = structlog.get_logger()

SEASON_CONFIG = {
    "spring": {"temp_range": (10, 25), "rain_chance": 0.25, "storm_chance": 0.05, "snow_chance": 0.0},
    "summer": {"temp_range": (22, 38), "rain_chance": 0.10, "storm_chance": 0.08, "snow_chance": 0.0},
    "autumn": {"temp_range": (5, 20), "rain_chance": 0.30, "storm_chance": 0.06, "snow_chance": 0.02},
    "winter": {"temp_range": (-5, 12), "rain_chance": 0.20, "storm_chance": 0.03, "snow_chance": 0.15},
}

CONDITION_EFFECTS = {
    "clear":    {"happiness": 0.02, "health": 0.01,  "traffic": 1.0, "crime": 1.0},
    "cloudy":   {"happiness": 0.0,  "health": 0.0,   "traffic": 1.0, "crime": 1.0},
    "rain":     {"happiness": -0.02, "health": -0.01, "traffic": 1.3, "crime": 0.7},
    "storm":    {"happiness": -0.05, "health": -0.03, "traffic": 1.8, "crime": 0.4},
    "snow":     {"happiness": 0.01,  "health": -0.02, "traffic": 2.0, "crime": 0.5},
    "fog":      {"happiness": -0.01, "health": 0.0,   "traffic": 1.5, "crime": 0.8},
    "heatwave": {"happiness": -0.04, "health": -0.04, "traffic": 1.1, "crime": 1.3},
    "cold_snap":{"happiness": -0.03, "health": -0.05, "traffic": 1.4, "crime": 0.6},
}


class WeatherEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._ticks_since_change = 0
        self._change_interval = random.randint(4, 12)

    def _get_season(self, day: int) -> str:
        cycle = day % 120
        if cycle < 30:
            return "spring"
        elif cycle < 60:
            return "summer"
        elif cycle < 90:
            return "autumn"
        return "winter"

    def _generate_condition(self, season: str, hour: int) -> dict:
        cfg = SEASON_CONFIG[season]
        t_min, t_max = cfg["temp_range"]

        diurnal = math.sin((hour - 6) * math.pi / 12) * 0.3
        temperature = random.uniform(t_min, t_max) + diurnal * (t_max - t_min)

        roll = random.random()
        if roll < cfg["snow_chance"]:
            condition = "snow"
        elif roll < cfg["snow_chance"] + cfg["storm_chance"]:
            condition = "storm"
        elif roll < cfg["snow_chance"] + cfg["storm_chance"] + cfg["rain_chance"]:
            condition = "rain"
        elif random.random() < 0.08:
            condition = "fog" if hour < 9 or hour > 20 else "cloudy"
        elif temperature > 35:
            condition = "heatwave"
        elif temperature < -2:
            condition = "cold_snap"
        elif random.random() < 0.4:
            condition = "cloudy"
        else:
            condition = "clear"

        humidity = {"rain": 0.85, "storm": 0.9, "snow": 0.7, "fog": 0.95,
                    "heatwave": 0.2, "cold_snap": 0.3, "cloudy": 0.6, "clear": 0.4}
        wind = {"storm": random.uniform(50, 100), "clear": random.uniform(0, 15),
                "rain": random.uniform(15, 40), "snow": random.uniform(10, 35)}
        vis = {"fog": random.uniform(0.2, 2), "storm": random.uniform(1, 5),
               "rain": random.uniform(3, 8), "snow": random.uniform(2, 6)}

        aqi = 30 if condition in ("rain", "storm", "snow") else random.randint(30, 120)
        uv = max(0, 8 * diurnal + random.uniform(-1, 1)) if condition == "clear" else random.uniform(0, 3)
        precip = {"rain": random.uniform(2, 20), "storm": random.uniform(15, 60),
                  "snow": random.uniform(5, 30)}.get(condition, 0)

        effects = CONDITION_EFFECTS[condition]

        return {
            "condition": condition,
            "temperature_c": round(temperature, 1),
            "humidity": humidity.get(condition, 0.5),
            "wind_speed_kmh": round(wind.get(condition, random.uniform(5, 25)), 1),
            "visibility_km": round(vis.get(condition, 10.0), 1),
            "air_quality_index": aqi,
            "uv_index": round(max(0, uv), 1),
            "precipitation_mm": round(precip, 1),
            "season": season,
            "happiness_modifier": effects["happiness"],
            "health_modifier": effects["health"],
            "traffic_modifier": effects["traffic"],
            "crime_modifier": effects["crime"],
        }

    async def get_current_weather(self) -> WeatherState | None:
        result = await self.db.execute(
            select(WeatherState).where(WeatherState.is_current == True).limit(1)  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def process_tick(self, sim_time: datetime, day: int, hour: int) -> dict:
        self._ticks_since_change += 1

        if self._ticks_since_change < self._change_interval:
            current = await self.get_current_weather()
            if current:
                return self._weather_to_dict(current)

        self._ticks_since_change = 0
        self._change_interval = random.randint(4, 12)

        season = self._get_season(day)
        data = self._generate_condition(season, hour)

        await self.db.execute(
            update(WeatherState).where(WeatherState.is_current == True).values(is_current=False)  # noqa: E712
        )

        weather = WeatherState(
            sim_timestamp=sim_time,
            is_current=True,
            **data,
        )
        self.db.add(weather)
        await self.db.flush()

        log.debug("weather_updated", condition=data["condition"], temp=data["temperature_c"], season=season)
        return self._weather_to_dict(weather)

    def _weather_to_dict(self, w: WeatherState) -> dict:
        return {
            "condition": w.condition,
            "temperature_c": w.temperature_c,
            "humidity": w.humidity,
            "wind_speed_kmh": w.wind_speed_kmh,
            "visibility_km": w.visibility_km,
            "air_quality_index": w.air_quality_index,
            "uv_index": w.uv_index,
            "precipitation_mm": w.precipitation_mm,
            "season": w.season,
            "happiness_modifier": w.happiness_modifier,
            "health_modifier": w.health_modifier,
            "traffic_modifier": w.traffic_modifier,
            "crime_modifier": w.crime_modifier,
        }
