"""Improvement proposal API endpoints.

Supports approval workflow with editing capability,
execution via Google Ads API, and rollback.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from uuid import UUID
from pydantic import BaseModel
from typing import Optional, Any

from app.db.session import get_db
from app.models.proposal import (
    ImprovementProposal,
    ProposalCategory,
    Priority,
    ProposalStatus,
)
from app.models.campaign import Campaign, CampaignStatus
from app.schemas.proposal import (
    ProposalResponse,
    ProposalDetail,
    ProposalStatusUpdate,
    ChatRequest,
    ChatResponse,
    ImpactReport,
)
from app.services.proposal_executor import ProposalExecutor, SafeguardError
from app.services.proposal_chat import ProposalChatService
from app.services.impact_tracker import ImpactTracker

router = APIRouter(prefix="/proposals", tags=["proposals"])


class ApproveRequest(BaseModel):
    """Request to approve a proposal with optional edits."""
    schedule_at: Optional[datetime] = None
    edited_values: Optional[dict[str, Any]] = None
    edit_reason: Optional[str] = None
    executed_by: str = "admin"


class ExecuteRequest(BaseModel):
    """Request to execute an approved proposal."""
    edited_values: Optional[dict[str, Any]] = None
    execution_notes: str = ""
    executed_by: str = "admin"


class RejectRequest(BaseModel):
    """Request to reject a proposal."""
    reason: Optional[str] = None


class RollbackRequest(BaseModel):
    """Request to rollback an executed proposal."""
    reason: str = ""


class SafeguardCheckResponse(BaseModel):
    """Response from safeguard validation."""
    can_execute: bool
    warnings: list[str] = []
    error: Optional[str] = None


@router.get("", response_model=list[ProposalResponse])
async def list_proposals(
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    report_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List improvement proposals with optional filters."""
    query = select(ImprovementProposal)

    if status:
        query = query.where(ImprovementProposal.status == ProposalStatus(status))
    if category:
        query = query.where(ImprovementProposal.category == ProposalCategory(category))
    if priority:
        query = query.where(ImprovementProposal.priority == Priority(priority))
    if report_id:
        query = query.where(ImprovementProposal.report_id == report_id)

    query = query.order_by(desc(ImprovementProposal.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    proposals = result.scalars().all()

    # Fetch all campaigns to check their status
    campaign_result = await db.execute(select(Campaign))
    campaigns = campaign_result.scalars().all()
    campaign_status_map = {c.campaign_name: c.status.value for c in campaigns}

    response_list = []
    for p in proposals:
        # Check if target campaign exists and is active
        campaign_status = None
        is_active = True

        if p.target_campaign:
            if p.target_campaign in campaign_status_map:
                campaign_status = campaign_status_map[p.target_campaign]
                is_active = campaign_status == "active"
            else:
                campaign_status = "not_found"
                is_active = False

        # Skip proposals for inactive/non-existent campaigns
        if not is_active:
            continue

        response_list.append(
            ProposalResponse(
                id=p.id,
                report_id=p.report_id,
                category=p.category.value,
                priority=p.priority.value,
                title=p.title,
                description=p.description,
                expected_effect=p.expected_effect,
                action_steps=p.action_steps,
                target_campaign=p.target_campaign,
                target_ad_group=p.target_ad_group,
                status=p.status.value,
                created_at=p.created_at,
                campaign_status=campaign_status,
                is_campaign_active=is_active,
            )
        )

    return response_list


class CleanupResponse(BaseModel):
    """Response from cleanup operation."""
    skipped_count: int
    skipped_proposals: list[dict[str, str]]


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_inactive_proposals(
    dry_run: bool = Query(default=True, description="If true, only report what would be cleaned up"),
    db: AsyncSession = Depends(get_db),
):
    """
    Clean up proposals for inactive/non-existent campaigns.

    Sets status to 'skipped' for proposals where:
    - target_campaign is set AND
    - campaign doesn't exist OR campaign status is not 'active'

    Use dry_run=true to preview what would be cleaned up.
    """
    # Get all pending proposals with target_campaign
    query = select(ImprovementProposal).where(
        ImprovementProposal.status == ProposalStatus.PENDING,
        ImprovementProposal.target_campaign.isnot(None),
    )
    result = await db.execute(query)
    proposals = result.scalars().all()

    # Get all active campaigns
    campaign_result = await db.execute(select(Campaign))
    campaigns = campaign_result.scalars().all()
    active_campaigns = {
        c.campaign_name for c in campaigns if c.status == CampaignStatus.ACTIVE
    }

    # Find proposals to skip
    to_skip = []
    for p in proposals:
        if p.target_campaign and p.target_campaign not in active_campaigns:
            to_skip.append({
                "id": str(p.id),
                "title": p.title,
                "target_campaign": p.target_campaign,
            })

    if not dry_run:
        # Actually update the status
        for p in proposals:
            if p.target_campaign and p.target_campaign not in active_campaigns:
                p.status = ProposalStatus.SKIPPED
        await db.commit()

    return CleanupResponse(
        skipped_count=len(to_skip),
        skipped_proposals=to_skip,
    )


@router.get("/{proposal_id}", response_model=ProposalDetail)
async def get_proposal(proposal_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single proposal with execution and result details."""
    result = await db.execute(
        select(ImprovementProposal)
        .options(
            selectinload(ImprovementProposal.execution),
            selectinload(ImprovementProposal.result),
        )
        .where(ImprovementProposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    return ProposalDetail(
        id=proposal.id,
        report_id=proposal.report_id,
        category=proposal.category.value,
        priority=proposal.priority.value,
        title=proposal.title,
        description=proposal.description,
        expected_effect=proposal.expected_effect,
        action_steps=proposal.action_steps,
        target_campaign=proposal.target_campaign,
        target_ad_group=proposal.target_ad_group,
        status=proposal.status.value,
        created_at=proposal.created_at,
        execution=proposal.execution,
        result=proposal.result,
    )


@router.patch("/{proposal_id}/status")
async def update_proposal_status(
    proposal_id: UUID,
    body: ProposalStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update proposal status (approve, reject, skip)."""
    result = await db.execute(
        select(ImprovementProposal).where(ImprovementProposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    try:
        new_status = ProposalStatus(body.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {body.status}. Must be one of: {[s.value for s in ProposalStatus]}",
        )

    proposal.status = new_status
    await db.commit()

    return {"id": str(proposal.id), "status": new_status.value}


@router.post("/{proposal_id}/approve")
async def approve_proposal(
    proposal_id: UUID,
    body: ApproveRequest,
    db: AsyncSession = Depends(get_db),
):
    """Approve a proposal with optional edits and execute immediately or schedule.

    If schedule_at is provided, the proposal is approved but not executed yet.
    If schedule_at is None, the proposal is approved and executed immediately.
    """
    result = await db.execute(
        select(ImprovementProposal).where(ImprovementProposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()

    if not proposal:
        raise HTTPException(status_code=404, detail="提案が見つかりません")

    if proposal.status != ProposalStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"この提案は '{proposal.status.value}' 状態のため承認できません",
        )

    # Record edit history if values were edited
    if body.edited_values:
        edit_record = {
            "original_action_steps": proposal.action_steps,
            "edited_values": body.edited_values,
            "edit_reason": body.edit_reason,
            "edited_at": datetime.now().isoformat(),
            "edited_by": body.executed_by,
        }
        current_steps = proposal.action_steps or []
        if isinstance(current_steps, list):
            proposal.action_steps = {
                "steps": current_steps,
                "edit_history": [edit_record],
            }
        elif isinstance(current_steps, dict):
            edit_history = current_steps.get("edit_history", [])
            edit_history.append(edit_record)
            current_steps["edit_history"] = edit_history
            proposal.action_steps = current_steps

    # Set status to approved
    proposal.status = ProposalStatus.APPROVED
    await db.commit()

    # If immediate execution (no schedule)
    if body.schedule_at is None:
        executor = ProposalExecutor(db)

        try:
            exec_result = await executor.execute_proposal(
                proposal_id=proposal_id,
                executed_by=body.executed_by,
                edited_values=body.edited_values,
            )
            return {
                "id": str(proposal.id),
                "status": "executed",
                "execution": exec_result,
            }
        except SafeguardError as e:
            proposal.status = ProposalStatus.PENDING
            await db.commit()
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            return {
                "id": str(proposal.id),
                "status": "approved",
                "execution_error": str(e),
                "note": "承認されましたが、自動反映でエラーが発生しました。手動対応が必要です。",
            }
    else:
        return {
            "id": str(proposal.id),
            "status": "approved",
            "scheduled_at": body.schedule_at.isoformat(),
            "note": f"予約反映: {body.schedule_at.strftime('%Y-%m-%d %H:%M')} に実行されます",
        }


@router.post("/{proposal_id}/reject")
async def reject_proposal(
    proposal_id: UUID,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reject a proposal with optional reason."""
    result = await db.execute(
        select(ImprovementProposal).where(ImprovementProposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()

    if not proposal:
        raise HTTPException(status_code=404, detail="提案が見つかりません")

    proposal.status = ProposalStatus.REJECTED

    if body.reason:
        current_steps = proposal.action_steps or {}
        if isinstance(current_steps, list):
            current_steps = {"steps": current_steps}
        current_steps["rejection_reason"] = body.reason
        current_steps["rejected_at"] = datetime.now().isoformat()
        proposal.action_steps = current_steps

    await db.commit()

    return {
        "id": str(proposal.id),
        "status": "rejected",
        "reason": body.reason,
    }


@router.post("/{proposal_id}/execute")
async def execute_proposal(
    proposal_id: UUID,
    body: ExecuteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Execute an approved proposal via Google Ads API."""
    executor = ProposalExecutor(db)

    try:
        result = await executor.execute_proposal(
            proposal_id=proposal_id,
            executed_by=body.executed_by,
            edited_values=body.edited_values,
            execution_notes=body.execution_notes,
        )
        return result
    except SafeguardError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"実行エラー: {str(e)}",
        )


@router.post("/{proposal_id}/rollback")
async def rollback_proposal(
    proposal_id: UUID,
    body: RollbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rollback an executed proposal (within 24h window)."""
    executor = ProposalExecutor(db)

    try:
        result = await executor.rollback_execution(
            proposal_id=proposal_id,
            reason=body.reason,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ロールバックエラー: {str(e)}",
        )


@router.post("/{proposal_id}/safeguard-check")
async def check_safeguards(
    proposal_id: UUID,
    edited_values: Optional[dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    """Check safeguard rules before execution."""
    result = await db.execute(
        select(ImprovementProposal).where(ImprovementProposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()

    if not proposal:
        raise HTTPException(status_code=404, detail="提案が見つかりません")

    executor = ProposalExecutor(db)

    try:
        warnings = await executor.validate_safeguards(proposal, edited_values)
        return SafeguardCheckResponse(
            can_execute=True,
            warnings=warnings,
        )
    except SafeguardError as e:
        return SafeguardCheckResponse(
            can_execute=False,
            error=str(e),
        )


# ============================================================
# Chat (Wall-bouncing) endpoints
# ============================================================

@router.post("/{proposal_id}/chat", response_model=ChatResponse)
async def chat_about_proposal(
    proposal_id: UUID,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Chat with Claude about a proposal before approving it.

    This allows users to discuss the proposal, ask questions,
    explore alternatives, and understand risks before making a decision.
    """
    chat_service = ProposalChatService()

    try:
        reply, history = await chat_service.chat(
            db=db,
            proposal_id=proposal_id,
            user_message=body.message,
        )
        return ChatResponse(reply=reply, conversation_history=history)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"チャットエラー: {str(e)}",
        )


@router.get("/{proposal_id}/chat/history")
async def get_chat_history(
    proposal_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the conversation history for a proposal."""
    chat_service = ProposalChatService()

    try:
        history = await chat_service.get_conversation_history(db, proposal_id)
        return {"conversation_history": history}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"履歴取得エラー: {str(e)}",
        )


# ============================================================
# Impact Report endpoints
# ============================================================

@router.get("/{proposal_id}/impact", response_model=ImpactReport)
async def get_impact_report(
    proposal_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the impact report for an executed proposal.

    Compares before/after KPIs to measure the effect of the proposal.
    Returns percentage changes for cost, conversions, CPA, CTR, ROAS, etc.
    """
    tracker = ImpactTracker(db)

    try:
        report = await tracker.get_impact_report(proposal_id)
        if not report:
            raise HTTPException(status_code=404, detail="提案が見つかりません")

        return ImpactReport(
            status=report.get("status", "no_data"),
            before=report.get("before"),
            after=report.get("after"),
            change=report.get("change"),
            period=report.get("period"),
            message=report.get("message"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"インパクトレポート取得エラー: {str(e)}",
        )
