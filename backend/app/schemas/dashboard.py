from pydantic import BaseModel
from datetime import date
from typing import Optional


class KPIMetric(BaseModel):
    value: float
    previous: Optional[float] = None
    change_pct: Optional[float] = None
    signal: str = "blue"  # green, yellow, red, blue
    target: Optional[float] = None


class DashboardSummary(BaseModel):
    current_week_start: Optional[date] = None
    current_week_end: Optional[date] = None
    kpis: dict[str, KPIMetric] = {}
    pending_proposals_count: int = 0
    alerts: list[str] = []


class TrendPoint(BaseModel):
    week_start: date
    total_cost: Optional[float] = None
    total_conversions: Optional[float] = None
    cpa: Optional[float] = None
    ctr: Optional[float] = None
    roas: Optional[float] = None
    impression_share: Optional[float] = None


class TrendData(BaseModel):
    trends: list[TrendPoint] = []
