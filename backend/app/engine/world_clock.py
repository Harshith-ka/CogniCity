"""
World Clock: Manages simulation time progression.
Each real-time tick advances simulation time by (time_scale) minutes.
"""

from datetime import datetime, timedelta


class WorldClock:
    def __init__(
        self,
        start_time: datetime | None = None,
        time_scale: int = 60,
    ):
        self.sim_time = start_time or datetime(2025, 1, 1, 6, 0, 0)
        self.time_scale = time_scale
        self.tick_count = 0
        self.day_count = 0
        self._day_start = self.sim_time.day

    def tick(self) -> datetime:
        self.sim_time += timedelta(minutes=self.time_scale)
        self.tick_count += 1

        if self.sim_time.day != self._day_start:
            self.day_count += 1
            self._day_start = self.sim_time.day

        return self.sim_time

    @property
    def hour(self) -> int:
        return self.sim_time.hour

    @property
    def minute(self) -> int:
        return self.sim_time.minute

    @property
    def day(self) -> int:
        return self.day_count

    @property
    def is_daytime(self) -> bool:
        return 6 <= self.hour < 22

    @property
    def is_work_hours(self) -> bool:
        return 9 <= self.hour < 17 and self.sim_time.weekday() < 5

    def time_str(self) -> str:
        return self.sim_time.strftime("%Y-%m-%d %H:%M")
