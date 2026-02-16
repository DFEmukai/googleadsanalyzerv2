from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.db.session import get_db
from app.models.weekly_report import WeeklyReport
from app.models.proposal import ImprovementProposal
from app.schemas.report import ReportSummary, ReportDetail, ProposalInReport

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportSummary])
async def list_reports(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List weekly reports with summary."""
    result = await db.execute(
        select(WeeklyReport)
        .order_by(desc(WeeklyReport.week_start_date))
        .limit(limit)
        .offset(offset)
    )
    reports = result.scalars().all()

    summaries = []
    for report in reports:
        # Count proposals
        count_result = await db.execute(
            select(func.count(ImprovementProposal.id)).where(
                ImprovementProposal.report_id == report.id
            )
        )
        proposals_count = count_result.scalar() or 0

        summaries.append(
            ReportSummary(
                id=report.id,
                week_start_date=report.week_start_date,
                week_end_date=report.week_end_date,
                created_at=report.created_at,
                kpi_snapshot=report.kpi_snapshot,
                proposals_count=proposals_count,
            )
        )

    return summaries


@router.get("/latest", response_model=ReportDetail)
async def get_latest_report(db: AsyncSession = Depends(get_db)):
    """Get the most recent weekly report with proposals."""
    result = await db.execute(
        select(WeeklyReport)
        .options(selectinload(WeeklyReport.proposals))
        .order_by(desc(WeeklyReport.week_start_date))
        .limit(1)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="No reports found")

    return _build_report_detail(report)


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(report_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific report by ID."""
    result = await db.execute(
        select(WeeklyReport)
        .options(selectinload(WeeklyReport.proposals))
        .where(WeeklyReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return _build_report_detail(report)


def _build_report_detail(report: WeeklyReport) -> ReportDetail:
    proposals = [
        ProposalInReport(
            id=p.id,
            category=p.category.value,
            priority=p.priority.value,
            title=p.title,
            expected_effect=p.expected_effect,
            status=p.status.value,
            target_campaign=p.target_campaign,
        )
        for p in report.proposals
    ]

    return ReportDetail(
        id=report.id,
        week_start_date=report.week_start_date,
        week_end_date=report.week_end_date,
        created_at=report.created_at,
        raw_data=report.raw_data,
        analysis_summary=report.analysis_summary,
        kpi_snapshot=report.kpi_snapshot,
        proposals=proposals,
    )
