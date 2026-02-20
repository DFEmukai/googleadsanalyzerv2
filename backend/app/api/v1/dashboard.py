from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.db.session import get_db
from app.models.weekly_report import WeeklyReport
from app.models.proposal import ImprovementProposal, ProposalStatus
from app.schemas.dashboard import DashboardSummary, KPIMetric, TrendData, TrendPoint
from app.services.google_ads import GoogleAdsService

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
    elif metric_type in ("cost", "impressions"):
        return "blue"  # Cost and impressions are neutral (informational)
    else:
        return "blue"


def _aggregate_campaign_data(campaigns: list[dict]) -> dict:
    """Aggregate campaign performance data into KPI totals."""
    total_cost = 0.0
    total_conversions = 0.0
    total_impressions = 0
    total_clicks = 0
    total_conversions_value = 0.0

    for c in campaigns:
        total_cost += c.get("cost", 0)
        total_conversions += c.get("conversions", 0)
        total_impressions += c.get("impressions", 0)
        total_clicks += c.get("clicks", 0)
        total_conversions_value += c.get("conversions_value", 0)

    # Calculate aggregated metrics
    cpa = total_cost / total_conversions if total_conversions > 0 else 0
    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    roas = total_conversions_value / total_cost if total_cost > 0 else 0

    # Calculate weighted average impression share
    total_impression_share = 0.0
    impression_share_count = 0
    for c in campaigns:
        imp_share = c.get("impression_share", 0)
        if imp_share and imp_share > 0:
            total_impression_share += imp_share
            impression_share_count += 1
    avg_impression_share = (
        total_impression_share / impression_share_count
        if impression_share_count > 0
        else 0
    )

    return {
        "total_cost": total_cost,
        "total_conversions": total_conversions,
        "total_impressions": total_impressions,
        "cpa": cpa,
        "ctr": ctr,
        "roas": roas,
        "impression_share": avg_impression_share,
    }


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Get the last 7 days' KPI summary with signals.

    Fetches real-time data from Google Ads API for:
    - Cost: 7-day total
    - Conversions: 7-day total
    - CPA: 7-day average (total cost / total conversions)
    - CTR: 7-day average
    - ROAS: 7-day average
    - Impressions: 7-day total
    """
    today = date.today()
    # Last 7 days: yesterday to 7 days ago (excluding today as data may be incomplete)
    end_date = today - timedelta(days=1)
    start_date = today - timedelta(days=7)

    # Previous 7 days for comparison
    prev_end_date = start_date - timedelta(days=1)
    prev_start_date = start_date - timedelta(days=7)

    google_ads_service = GoogleAdsService()

    try:
        # Fetch current period data
        current_campaigns = google_ads_service.get_campaign_performance(
            start_date=start_date, end_date=end_date
        )
        current_kpi = _aggregate_campaign_data(current_campaigns)

        # Fetch previous period data for comparison
        prev_campaigns = google_ads_service.get_campaign_performance(
            start_date=prev_start_date, end_date=prev_end_date
        )
        prev_kpi = _aggregate_campaign_data(prev_campaigns)
    except Exception:
        # Fallback to WeeklyReport if Google Ads API fails
        result = await db.execute(
            select(WeeklyReport).order_by(desc(WeeklyReport.week_start_date)).limit(1)
        )
        latest = result.scalar_one_or_none()

        if not latest or not latest.kpi_snapshot:
            return DashboardSummary()

        result = await db.execute(
            select(WeeklyReport)
            .where(WeeklyReport.week_start_date < latest.week_start_date)
            .order_by(desc(WeeklyReport.week_start_date))
            .limit(1)
        )
        previous = result.scalar_one_or_none()
        prev_kpi = previous.kpi_snapshot if previous and previous.kpi_snapshot else {}
        current_kpi = latest.kpi_snapshot
        start_date = latest.week_start_date
        end_date = latest.week_end_date

    kpis = {}

    metrics_config = [
        ("total_cost", "cost"),
        ("total_conversions", "conversions"),
        ("total_impressions", "impressions"),
        ("cpa", "cpa"),
        ("ctr", "ctr"),
        ("roas", "roas"),
        ("impression_share", "ctr"),
    ]

    for metric_key, metric_type in metrics_config:
        value = current_kpi.get(metric_key, 0)
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
        current_week_start=start_date,
        current_week_end=end_date,
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
