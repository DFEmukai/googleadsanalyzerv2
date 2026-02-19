from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional
from uuid import UUID


class CampaignResponse(BaseModel):
    id: UUID
    campaign_id: str
    campaign_name: str
    campaign_type: str
    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    ended_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignWithMetrics(CampaignResponse):
    cost: Optional[float] = None
    conversions: Optional[float] = None
    cpa: Optional[float] = None
    ctr: Optional[float] = None
    clicks: Optional[int] = None
    impressions: Optional[int] = None
    roas: Optional[float] = None


class CampaignInfo(BaseModel):
    id: str
    campaign_id: str
    name: str
    status: str
    type: str


class CampaignSummary(BaseModel):
    cost: float
    conversions: float
    cpa: float
    ctr: float
    roas: float
    clicks: int
    impressions: int
    impression_share: Optional[float] = None


class CampaignTrendPoint(BaseModel):
    date: str
    cost: float
    conversions: float
    cpa: float
    ctr: float
    roas: float
    clicks: int
    impressions: int


class CampaignPeriod(BaseModel):
    start: str
    end: str


class RelatedProposal(BaseModel):
    id: str
    category: str
    priority: str
    title: str
    status: str
    expected_effect: Optional[str] = None


class CampaignDashboard(BaseModel):
    campaign: CampaignInfo
    summary: CampaignSummary
    trends: list[CampaignTrendPoint]
    period: CampaignPeriod
    proposals: list[RelatedProposal]
