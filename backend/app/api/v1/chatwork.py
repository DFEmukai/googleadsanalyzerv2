"""Chatwork notification API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.models.weekly_report import WeeklyReport
from app.models.proposal import ImprovementProposal, Priority
from app.services.chatwork import ChatworkService

router = APIRouter(prefix="/chatwork", tags=["chatwork"])


class ChatworkTestMessage(BaseModel):
    message: str = "テスト通知：Google広告AIエージェントからの接続確認です。"


class ChatworkStatusResponse(BaseModel):
    configured: bool
    room_id: Optional[str] = None
    has_assignee: bool = False


@router.get("/status", response_model=ChatworkStatusResponse)
async def get_chatwork_status():
    """Check Chatwork API configuration status."""
    service = ChatworkService()
    settings_obj = service
    return ChatworkStatusResponse(
        configured=service.is_configured(),
        room_id=service.room_id if service.is_configured() else None,
        has_assignee=bool(service.assignee_id),
    )


@router.post("/test")
async def send_test_message(body: ChatworkTestMessage):
    """Send a test message to verify Chatwork integration."""
    service = ChatworkService()
    if not service.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Chatwork APIが設定されていません。環境変数 CHATWORK_API_TOKEN と CHATWORK_ROOM_ID を設定してください。",
        )

    try:
        result = await service.send_message(body.message)
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chatworkメッセージ送信エラー: {str(e)}",
        )


@router.post("/notify/{report_id}")
async def send_report_notification(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Manually send a Chatwork notification for a specific report."""
    service = ChatworkService()
    if not service.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Chatwork APIが設定されていません。",
        )

    # Get the report
    result = await db.execute(
        select(WeeklyReport).where(WeeklyReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="レポートが見つかりません")

    # Get high-priority proposals for this report
    result = await db.execute(
        select(ImprovementProposal)
        .where(
            ImprovementProposal.report_id == report_id,
            ImprovementProposal.priority == Priority.HIGH,
        )
    )
    proposals = result.scalars().all()

    high_priority = [
        {
            "title": p.title,
            "target_campaign": p.target_campaign,
            "expected_effect": p.expected_effect,
        }
        for p in proposals
    ]

    # Get previous KPI for comparison
    prev_result = await db.execute(
        select(WeeklyReport)
        .where(WeeklyReport.week_start_date < report.week_start_date)
        .order_by(desc(WeeklyReport.week_start_date))
        .limit(1)
    )
    prev_report = prev_result.scalar_one_or_none()
    previous_kpi = prev_report.kpi_snapshot if prev_report else None

    try:
        chatwork_result = await service.send_weekly_report(
            report_id=str(report.id),
            week_start=report.week_start_date,
            week_end=report.week_end_date,
            kpi_snapshot=report.kpi_snapshot or {},
            previous_kpi=previous_kpi,
            high_priority_proposals=high_priority,
        )
        return chatwork_result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chatwork通知エラー: {str(e)}",
        )
