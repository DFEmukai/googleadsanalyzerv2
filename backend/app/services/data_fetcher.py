"""Weekly data fetching orchestrator.

Fetches all required data from Google Ads API and assembles it
into a structured format for analysis.
"""

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.campaign import Campaign, CampaignType, CampaignStatus
from app.services.google_ads import GoogleAdsService


class DataFetcher:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.google_ads = GoogleAdsService()

    @staticmethod
    def get_previous_week_range() -> tuple[date, date]:
        """Get Monday-Sunday of the previous week."""
        today = date.today()
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        return last_monday, last_sunday

    async def fetch_weekly_data(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> dict[str, Any]:
        """Fetch all data for the specified week."""
        if start_date is None or end_date is None:
            start_date, end_date = self.get_previous_week_range()

        # Fetch all data
        campaigns = self.google_ads.get_campaigns()
        campaign_perf = self.google_ads.get_campaign_performance(start_date, end_date)
        keyword_perf = self.google_ads.get_keyword_performance(start_date, end_date)
        ad_group_perf = self.google_ads.get_ad_group_performance(start_date, end_date)
        search_terms = self.google_ads.get_search_terms(start_date, end_date)
        device_perf = self.google_ads.get_device_performance(start_date, end_date)
        geo_perf = self.google_ads.get_geo_performance(start_date, end_date)
        hourly_perf = self.google_ads.get_hourly_performance(start_date, end_date)
        auction_insights = self.google_ads.get_auction_insights(start_date, end_date)
        ad_copy_perf = self.google_ads.get_ad_copy_performance(start_date, end_date)

        # Sync campaigns to database
        await self._sync_campaigns(campaigns)

        # Calculate KPI snapshot
        kpi_snapshot = self._calculate_kpis(campaign_perf)

        raw_data = {
            "campaigns": campaigns,
            "campaign_performance": campaign_perf,
            "keyword_performance": keyword_perf,
            "ad_group_performance": ad_group_perf,
            "search_terms": search_terms,
            "device_performance": device_perf,
            "geo_performance": geo_perf,
            "hourly_performance": hourly_perf,
            "auction_insights": auction_insights,
            "ad_copy_performance": ad_copy_perf,
        }

        return {
            "start_date": start_date,
            "end_date": end_date,
            "raw_data": raw_data,
            "kpi_snapshot": kpi_snapshot,
        }

    async def _sync_campaigns(self, campaigns: list[dict[str, Any]]) -> None:
        """Sync campaign data with the database. Detect new/ended campaigns."""
        now = datetime.now()
        seen_ids = set()

        for campaign_data in campaigns:
            cid = campaign_data["campaign_id"]
            seen_ids.add(cid)

            # Google Ads APIから返される値は大文字の場合があるため、小文字に変換
            raw_type = campaign_data["campaign_type"].lower()
            raw_status = campaign_data["status"].lower()

            result = await self.db.execute(
                select(Campaign).where(Campaign.campaign_id == cid)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.campaign_name = campaign_data["campaign_name"]
                existing.last_seen_at = now
                if raw_status == "paused":
                    existing.status = CampaignStatus.PAUSED
                elif raw_status == "enabled":
                    existing.status = CampaignStatus.ACTIVE
            else:
                # campaign_typeをENUM値にマッピング
                type_mapping = {
                    "search": CampaignType.SEARCH,
                    "display": CampaignType.DISPLAY,
                    "pmax": CampaignType.PMAX,
                    "performance_max": CampaignType.PMAX,
                    "video": CampaignType.VIDEO,
                    "shopping": CampaignType.SEARCH,
                    "multi_channel": CampaignType.PMAX,
                }
                campaign_type = type_mapping.get(raw_type, CampaignType.SEARCH)

                new_campaign = Campaign(
                    campaign_id=cid,
                    campaign_name=campaign_data["campaign_name"],
                    campaign_type=campaign_type,
                    status=CampaignStatus.ACTIVE,
                    first_seen_at=now,
                    last_seen_at=now,
                )
                self.db.add(new_campaign)

        # Mark campaigns not seen as ended
        result = await self.db.execute(
            select(Campaign).where(Campaign.status != CampaignStatus.ENDED)
        )
        all_active = result.scalars().all()
        for campaign in all_active:
            if campaign.campaign_id not in seen_ids:
                campaign.status = CampaignStatus.ENDED
                campaign.ended_at = now

        await self.db.commit()

    @staticmethod
    def _calculate_kpis(campaign_perf: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate aggregate KPIs from campaign performance data."""
        total_cost = sum(c["cost"] for c in campaign_perf)
        total_conversions = sum(c["conversions"] for c in campaign_perf)
        total_clicks = sum(c["clicks"] for c in campaign_perf)
        total_impressions = sum(c["impressions"] for c in campaign_perf)
        total_conv_value = sum(c.get("conversions_value", 0) for c in campaign_perf)

        cpa = total_cost / total_conversions if total_conversions > 0 else 0
        ctr = total_clicks / total_impressions if total_impressions > 0 else 0
        roas = total_conv_value / total_cost if total_cost > 0 else 0

        # Average impression share (only for campaigns that have it)
        impression_shares = [
            c["impression_share"]
            for c in campaign_perf
            if c.get("impression_share", 0) > 0
        ]
        avg_impression_share = (
            sum(impression_shares) / len(impression_shares) if impression_shares else 0
        )

        return {
            "total_cost": round(total_cost, 0),
            "total_conversions": round(total_conversions, 1),
            "cpa": round(cpa, 0),
            "ctr": round(ctr * 100, 2),
            "roas": round(roas, 2),
            "impression_share": round(avg_impression_share, 4),
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "total_conversions_value": round(total_conv_value, 0),
        }
