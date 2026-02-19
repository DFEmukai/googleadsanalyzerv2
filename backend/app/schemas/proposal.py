from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any
from uuid import UUID


class ProposalResponse(BaseModel):
    id: UUID
    report_id: UUID
    category: str
    priority: str
    title: str
    description: Optional[str] = None
    expected_effect: Optional[str] = None
    action_steps: Optional[list[dict[str, Any]] | dict[str, Any]] = None
    target_campaign: Optional[str] = None
    target_ad_group: Optional[str] = None
    status: str
    created_at: datetime
    # Campaign availability check
    campaign_status: Optional[str] = None  # "active", "paused", "ended", "not_found"
    is_campaign_active: bool = True  # False if campaign is paused/ended/not_found

    model_config = {"from_attributes": True}


class ProposalDetail(ProposalResponse):
    execution: Optional["ExecutionResponse"] = None
    result: Optional["ResultResponse"] = None


class ExecutionResponse(BaseModel):
    id: UUID
    executed_at: datetime
    executed_by: Optional[str] = None
    execution_notes: Optional[str] = None
    actual_changes: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class ResultResponse(BaseModel):
    id: UUID
    measured_at: datetime
    measurement_period: Optional[str] = None
    before_metrics: Optional[dict[str, Any]] = None
    after_metrics: Optional[dict[str, Any]] = None
    effect_summary: Optional[str] = None
    effect_percentage: Optional[float] = None
    ai_evaluation: Optional[str] = None

    model_config = {"from_attributes": True}


class ProposalStatusUpdate(BaseModel):
    status: str


# Chat (Wall-bouncing) schemas
class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    conversation_history: list[ChatMessage]


# Impact Report schemas
class KPISnapshot(BaseModel):
    cost: Optional[float] = None
    conversions: Optional[float] = None
    cpa: Optional[float] = None
    ctr: Optional[float] = None
    roas: Optional[float] = None
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    conversion_value: Optional[float] = None


class KPIChange(BaseModel):
    cost: Optional[float] = None
    conversions: Optional[float] = None
    cpa: Optional[float] = None
    ctr: Optional[float] = None
    roas: Optional[float] = None
    impressions: Optional[float] = None
    clicks: Optional[float] = None
    conversion_value: Optional[float] = None


class ImpactPeriod(BaseModel):
    before: str
    after: Optional[str] = None


class ImpactReport(BaseModel):
    status: str  # "available", "pending", "no_data", "no_before"
    before: Optional[KPISnapshot] = None
    after: Optional[KPISnapshot] = None
    change: Optional[KPIChange] = None
    period: Optional[ImpactPeriod] = None
    message: Optional[str] = None
