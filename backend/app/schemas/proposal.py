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
