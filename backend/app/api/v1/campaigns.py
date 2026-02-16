from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from uuid import UUID

from app.db.session import get_db
from app.models.campaign import Campaign, CampaignStatus
from app.models.weekly_report import WeeklyReport
from app.schemas.campaign import CampaignResponse, CampaignWithMetrics

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


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single campaign by ID."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign
