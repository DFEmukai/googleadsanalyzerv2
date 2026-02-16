from pydantic import BaseModel
from datetime import datetime
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
