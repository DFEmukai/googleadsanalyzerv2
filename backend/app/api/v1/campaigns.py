from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID
from datetime import date, timedelta

from app.db.session import get_db
from app.models.campaign import Campaign, CampaignStatus
from app.models.weekly_report import WeeklyReport
from app.models.proposal import Proposal
from app.schemas.campaign import (
    CampaignResponse,
    CampaignWithMetrics,
    CampaignDashboard,
    CampaignInfo,
    CampaignSummary,
    CampaignTrendPoint,
    CampaignPeriod,
    RelatedProposal,
)
from app.services.google_ads import GoogleAdsService

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("", response_model=list[CampaignWithMetrics])
async def list_campaigns(
    status: str | None = Query(default=None),
    sort_by: str = Query(default="campaign_name"),
    db: AsyncSession = Depends(get_db),
):
    """List all campaigns with their latest metrics."""
    query = select(Campaign)
    if status:
        query = query.where(Campaign.status == CampaignStatus(status))
    query = query.order_by(Campaign.campaign_name)

    result = await db.execute(query)
    campaigns = result.scalars().all()

    # Get latest report for metrics
    report_result = await db.execute(
        select(WeeklyReport).order_by(desc(WeeklyReport.week_start_date)).limit(1)
    )
    latest_report = report_result.scalar_one_or_none()

    campaign_metrics = {}
    if latest_report and latest_report.raw_data:
        for perf in latest_report.raw_data.get("campaign_performance", []):
            campaign_metrics[perf["campaign_id"]] = perf

    result_list = []
    for campaign in campaigns:
        metrics = campaign_metrics.get(campaign.campaign_id, {})
        result_list.append(
            CampaignWithMetrics(
                id=campaign.id,
                campaign_id=campaign.campaign_id,
                campaign_name=campaign.campaign_name,
                campaign_type=campaign.campaign_type.value,
                status=campaign.status.value,
                first_seen_at=campaign.first_seen_at,
                last_seen_at=campaign.last_seen_at,
                ended_at=campaign.ended_at,
                created_at=campaign.created_at,
                cost=metrics.get("cost"),
                conversions=metrics.get("conversions"),
                cpa=metrics.get("cpa"),
                ctr=metrics.get("ctr"),
                clicks=metrics.get("clicks"),
                impressions=metrics.get("impressions"),
                roas=metrics.get("roas"),
            )
        )

    # Sort
    if sort_by == "cost" and result_list:
        result_list.sort(key=lambda x: x.cost or 0, reverse=True)
    elif sort_by == "conversions" and result_list:
        result_list.sort(key=lambda x: x.conversions or 0, reverse=True)
    elif sort_by == "cpa" and result_list:
        result_list.sort(key=lambda x: x.cpa or 0)

    return result_list


# NOTE: Dashboard endpoint must be defined BEFORE the generic /{campaign_id} endpoint
# to ensure FastAPI matches "/dashboard" as a path segment, not as a campaign_id
@router.get("/{campaign_id}/dashboard", response_model=CampaignDashboard)
async def get_campaign_dashboard(
    campaign_id: UUID,
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard data for a specific campaign."""
    # Get campaign from database
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Calculate date range
    end_date = date.today() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=days - 1)

    # Fetch daily performance data from Google Ads
    google_ads = GoogleAdsService()
    try:
        daily_data = google_ads.get_campaign_daily_performance(
            campaign.campaign_id, start_date, end_date
        )
    except Exception:
        # If Google Ads API fails, try to use cached data from latest report
        daily_data = []

    # Calculate summary from daily data
    if daily_data:
        total_cost = sum(d["cost"] for d in daily_data)
        total_conversions = sum(d["conversions"] for d in daily_data)
        total_clicks = sum(d["clicks"] for d in daily_data)
        total_impressions = sum(d["impressions"] for d in daily_data)

        summary = CampaignSummary(
            cost=total_cost,
            conversions=total_conversions,
            cpa=total_cost / total_conversions if total_conversions > 0 else 0,
            ctr=total_clicks / total_impressions if total_impressions > 0 else 0,
            roas=(
                sum(d.get("conversions_value", 0) for d in daily_data) / total_cost
                if total_cost > 0
                else 0
            ),
            clicks=total_clicks,
            impressions=total_impressions,
            impression_share=(
                sum(d.get("impression_share", 0) for d in daily_data) / len(daily_data)
                if daily_data
                else None
            ),
        )
        trends = [
            CampaignTrendPoint(
                date=d["date"],
                cost=d["cost"],
                conversions=d["conversions"],
                cpa=d["cpa"],
                ctr=d["ctr"],
                roas=d["roas"],
                clicks=d["clicks"],
                impressions=d["impressions"],
            )
            for d in daily_data
        ]
    else:
        # Fallback to latest report data
        report_result = await db.execute(
            select(WeeklyReport).order_by(desc(WeeklyReport.week_start_date)).limit(1)
        )
        latest_report = report_result.scalar_one_or_none()

        campaign_perf = {}
        if latest_report and latest_report.raw_data:
            for perf in latest_report.raw_data.get("campaign_performance", []):
                if perf.get("campaign_id") == campaign.campaign_id:
                    campaign_perf = perf
                    break

        summary = CampaignSummary(
            cost=campaign_perf.get("cost", 0),
            conversions=campaign_perf.get("conversions", 0),
            cpa=campaign_perf.get("cpa", 0),
            ctr=campaign_perf.get("ctr", 0),
            roas=campaign_perf.get("roas", 0),
            clicks=campaign_perf.get("clicks", 0),
            impressions=campaign_perf.get("impressions", 0),
            impression_share=campaign_perf.get("impression_share"),
        )
        trends = []

    # Get related proposals
    proposals_result = await db.execute(
        select(Proposal)
        .where(Proposal.target_campaign == campaign.campaign_name)
        .order_by(desc(Proposal.created_at))
        .limit(10)
    )
    proposals = proposals_result.scalars().all()

    return CampaignDashboard(
        campaign=CampaignInfo(
            id=str(campaign.id),
            campaign_id=campaign.campaign_id,
            name=campaign.campaign_name,
            status=campaign.status.value,
            type=campaign.campaign_type.value,
        ),
        summary=summary,
        trends=trends,
        period=CampaignPeriod(
            start=str(start_date),
            end=str(end_date),
        ),
        proposals=[
            RelatedProposal(
                id=str(p.id),
                category=p.category.value,
                priority=p.priority.value,
                title=p.title,
                status=p.status.value,
                expected_effect=p.expected_effect,
            )
            for p in proposals
        ],
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single campaign by ID."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign
