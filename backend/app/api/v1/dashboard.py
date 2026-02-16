from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.db.session import get_db
from app.models.weekly_report import WeeklyReport
from app.models.proposal import ImprovementProposal, ProposalStatus
from app.schemas.dashboard import DashboardSummary, KPIMetric, TrendData, TrendPoint

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _compute_signal(
    value: float,
    previous: float | None,
    metric_type: str,
    target: float | None = None,
) -> str:
    """Compute signal color based on metric type and thresholds."""
    if previous is None or previous == 0:
        return "blue"

    change_pct = ((value - previous) / abs(previous)) * 100

    if metric_type == "cpa":
        # Lower is better for CPA
        if target:
            diff_from_target = ((value - target) / target) * 100
            if diff_from_target <= -10:
                return "green"
            elif diff_from_target <= 10:
                return "yellow"
            return "red"
        if change_pct <= -5:
            return "green"
        elif change_pct <= 5:
            return "yellow"
        return "red"
    elif metric_type in ("conversions", "roas"):
        # Higher is better
        if change_pct >= 10:
            return "green"
        elif change_pct >= -10:
            return "yellow"
        return "red"
    elif metric_type == "ctr":
        if change_pct >= 5:
            return "green"
        elif change_pct >= -5:
            return "yellow"
        return "red"
    elif metric_type == "cost":
        return "blue"  # Cost is neutral
    else:
        return "blue"


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Get the current week's KPI summary with signals."""
    # Get latest report
    result = await db.execute(
        select(WeeklyReport).order_by(desc(WeeklyReport.week_start_date)).limit(1)
    )
    latest = result.scalar_one_or_none()

    if not latest or not latest.kpi_snapshot:
        return DashboardSummary()

    # Get previous report for comparison
    result = await db.execute(
        select(WeeklyReport)
        .where(WeeklyReport.week_start_date < latest.week_start_date)
        .order_by(desc(WeeklyReport.week_start_date))
        .limit(1)
    )
    previous = result.scalar_one_or_none()
    prev_kpi = previous.kpi_snapshot if previous and previous.kpi_snapshot else {}

    kpi = latest.kpi_snapshot
    kpis = {}

    metrics_config = [
        ("total_cost", "cost"),
        ("total_conversions", "conversions"),
        ("cpa", "cpa"),
        ("ctr", "ctr"),
        ("roas", "roas"),
        ("impression_share", "ctr"),
    ]

    for metric_key, metric_type in metrics_config:
        value = kpi.get(metric_key, 0)
        prev_value = prev_kpi.get(metric_key)
        change_pct = None
        if prev_value and prev_value != 0:
            change_pct = round(((value - prev_value) / abs(prev_value)) * 100, 1)

        signal = _compute_signal(value, prev_value, metric_type)
        kpis[metric_key] = KPIMetric(
            value=value,
            previous=prev_value,
            change_pct=change_pct,
            signal=signal,
        )

    # Count pending proposals
    result = await db.execute(
        select(func.count(ImprovementProposal.id)).where(
            ImprovementProposal.status == ProposalStatus.PENDING
        )
    )
    pending_count = result.scalar() or 0

    return DashboardSummary(
        current_week_start=latest.week_start_date,
        current_week_end=latest.week_end_date,
        kpis=kpis,
        pending_proposals_count=pending_count,
    )


@router.get("/trends", response_model=TrendData)
async def get_dashboard_trends(
    weeks: int = Query(default=8, ge=1, le=52),
    db: AsyncSession = Depends(get_db),
):
    """Get KPI trends for the specified number of weeks."""
    result = await db.execute(
        select(WeeklyReport)
        .order_by(desc(WeeklyReport.week_start_date))
        .limit(weeks)
    )
    reports = result.scalars().all()

    trends = []
    for report in reversed(reports):
        kpi = report.kpi_snapshot or {}
        trends.append(
            TrendPoint(
                week_start=report.week_start_date,
                total_cost=kpi.get("total_cost"),
                total_conversions=kpi.get("total_conversions"),
                cpa=kpi.get("cpa"),
                ctr=kpi.get("ctr"),
                roas=kpi.get("roas"),
                impression_share=kpi.get("impression_share"),
            )
        )

    return TrendData(trends=trends)
