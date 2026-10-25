from typing import Literal

from pydantic import BaseModel


class TaskConfig(BaseModel):
    """Replenishment task parameters; feasibility output decides the final values."""

    granularity: Literal['commodity', 'sub_commodity'] = 'commodity'
    history_days: int = 98
    horizon_days: int = 7
    min_purchases: int = 2
    min_history_trips: int = 6
    staple_trip_share: float = 0.6
    max_instances_per_hh: int = 4
