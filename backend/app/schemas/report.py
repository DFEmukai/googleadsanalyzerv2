from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, Any
from uuid import UUID


class ReportSummary(BaseModel):
    id: UUID
    week_start_date: date
    week_end_date: date
    created_at: datetime
    kpi_snapshot: Optional[dict[str, Any]] = None
    proposals_count: int = 0

    model_config = {"from_attributes": True}


class ReportDetail(BaseModel):
    id: UUID
    week_start_date: date
    week_end_date: date
    created_at: datetime
    raw_data: Optional[dict[str, Any]] = None
    analysis_summary: Optional[str] = None
    kpi_snapshot: Optional[dict[str, Any]] = None
    proposals: list["ProposalInReport"] = []

    model_config = {"from_attributes": True}


class ProposalInReport(BaseModel):
    id: UUID
    category: str
    priority: str
    title: str
    expected_effect: Optional[str] = None
    status: str
    target_campaign: Optional[str] = None

    model_config = {"from_attributes": True}
