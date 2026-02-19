"""Google Ads API client wrapper.

Handles all GAQL queries and data fetching from Google Ads API.
"""

from datetime import date
from typing import Any

from app.config import get_settings


class GoogleAdsService:
    def __init__(self):
        settings = get_settings()
        self.customer_id = settings.google_ads_customer_id
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google.ads.googleads.client import GoogleAdsClient

            settings = get_settings()
            config = {
                "developer_token": settings.google_ads_developer_token,
                "client_id": settings.google_ads_client_id,
                "client_secret": settings.google_ads_client_secret,
                "refresh_token": settings.google_ads_refresh_token,
                "use_proto_plus": True,
            }
            if settings.google_ads_login_customer_id:
                config["login_customer_id"] = settings.google_ads_login_customer_id
            self._client = GoogleAdsClient.load_from_dict(config)
        return self._client

    def _query(self, query: str) -> list[dict[str, Any]]:
        client = self._get_client()
        service = client.get_service("GoogleAdsService")
        response = service.search(customer_id=self.customer_id, query=query)

        results = []
        for row in response:
            results.append(row)
        return results

    def get_campaigns(self) -> list[dict[str, Any]]:
        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.advertising_channel_type,
                campaign.status,
                campaign.bidding_strategy_type
            FROM campaign
            WHERE campaign.status != 'REMOVED'
            ORDER BY campaign.name
        """
        rows = self._query(query)
        campaigns = []
        for row in rows:
            channel = str(row.campaign.advertising_channel_type).split(".")[-1].lower()
            campaign_type = self._map_channel_type(channel)
            campaigns.append(
                {
                    "campaign_id": str(row.campaign.id),
                    "campaign_name": row.campaign.name,
                    "campaign_type": campaign_type,
                    "status": str(row.campaign.status).split(".")[-1].lower(),
                    "bidding_strategy_type": str(
                        row.campaign.bidding_strategy_type
                    ).split(".")[-1],
                }
            )
        return campaigns

    def get_campaign_performance(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.advertising_channel_type,
                campaign.status,
                metrics.cost_micros,
                metrics.conversions,
                metrics.clicks,
                metrics.impressions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.conversions_value,
                metrics.search_impression_share,
                campaign_budget.amount_micros
            FROM campaign
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
        """
        rows = self._query(query)
        results = []
        for row in rows:
            cost = row.metrics.cost_micros / 1_000_000
            conversions = row.metrics.conversions
            cpa = cost / conversions if conversions > 0 else 0
            conv_value = row.metrics.conversions_value
            roas = conv_value / cost if cost > 0 else 0

            results.append(
                {
                    "campaign_id": str(row.campaign.id),
                    "campaign_name": row.campaign.name,
                    "status": str(row.campaign.status).split(".")[-1].lower(),
                    "cost": cost,
                    "conversions": conversions,
                    "clicks": row.metrics.clicks,
                    "impressions": row.metrics.impressions,
                    "ctr": row.metrics.ctr,
                    "cpa": cpa,
                    "roas": roas,
                    "average_cpc": row.metrics.average_cpc / 1_000_000,
                    "conversions_value": conv_value,
                    "impression_share": row.metrics.search_impression_share or 0,
                    "budget_micros": row.campaign_budget.amount_micros,
                }
            )
        return results

    def get_keyword_performance(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                ad_group.name,
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                metrics.cost_micros,
                metrics.conversions,
                metrics.clicks,
                metrics.impressions,
                metrics.ctr,
                metrics.average_cpc
            FROM keyword_view
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
            ORDER BY metrics.cost_micros DESC
            LIMIT 200
        """
        rows = self._query(query)
        results = []
        for row in rows:
            cost = row.metrics.cost_micros / 1_000_000
            conversions = row.metrics.conversions
            results.append(
                {
                    "campaign_id": str(row.campaign.id),
                    "campaign_name": row.campaign.name,
                    "ad_group_name": row.ad_group.name,
                    "keyword": row.ad_group_criterion.keyword.text,
                    "match_type": str(
                        row.ad_group_criterion.keyword.match_type
                    ).split(".")[-1],
                    "cost": cost,
                    "conversions": conversions,
                    "clicks": row.metrics.clicks,
                    "impressions": row.metrics.impressions,
                    "ctr": row.metrics.ctr,
                    "cpa": cost / conversions if conversions > 0 else 0,
                }
            )
        return results

    def get_ad_group_performance(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                ad_group.id,
                ad_group.name,
                ad_group.status,
                metrics.cost_micros,
                metrics.conversions,
                metrics.clicks,
                metrics.impressions,
                metrics.ctr,
                metrics.conversions_value
            FROM ad_group
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
            ORDER BY metrics.cost_micros DESC
        """
        rows = self._query(query)
        results = []
        for row in rows:
            cost = row.metrics.cost_micros / 1_000_000
            conversions = row.metrics.conversions
            results.append(
                {
                    "campaign_id": str(row.campaign.id),
                    "campaign_name": row.campaign.name,
                    "ad_group_id": str(row.ad_group.id),
                    "ad_group_name": row.ad_group.name,
                    "status": str(row.ad_group.status).split(".")[-1].lower(),
                    "cost": cost,
                    "conversions": conversions,
                    "clicks": row.metrics.clicks,
                    "impressions": row.metrics.impressions,
                    "ctr": row.metrics.ctr,
                    "cpa": cost / conversions if conversions > 0 else 0,
                    "roas": (
                        row.metrics.conversions_value / cost if cost > 0 else 0
                    ),
                }
            )
        return results

    def get_search_terms(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                ad_group.name,
                search_term_view.search_term,
                metrics.cost_micros,
                metrics.conversions,
                metrics.clicks,
                metrics.impressions
            FROM search_term_view
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
            ORDER BY metrics.impressions DESC
            LIMIT 200
        """
        rows = self._query(query)
        results = []
        for row in rows:
            cost = row.metrics.cost_micros / 1_000_000
            conversions = row.metrics.conversions
            results.append(
                {
                    "campaign_name": row.campaign.name,
                    "ad_group_name": row.ad_group.name,
                    "search_term": row.search_term_view.search_term,
                    "cost": cost,
                    "conversions": conversions,
                    "clicks": row.metrics.clicks,
                    "impressions": row.metrics.impressions,
                    "cpa": cost / conversions if conversions > 0 else 0,
                }
            )
        return results

    def get_device_performance(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                segments.device,
                metrics.cost_micros,
                metrics.conversions,
                metrics.clicks,
                metrics.impressions,
                metrics.ctr
            FROM campaign
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
        """
        rows = self._query(query)
        results = []
        for row in rows:
            cost = row.metrics.cost_micros / 1_000_000
            conversions = row.metrics.conversions
            results.append(
                {
                    "campaign_name": row.campaign.name,
                    "device": str(row.segments.device).split(".")[-1],
                    "cost": cost,
                    "conversions": conversions,
                    "clicks": row.metrics.clicks,
                    "impressions": row.metrics.impressions,
                    "ctr": row.metrics.ctr,
                    "cpa": cost / conversions if conversions > 0 else 0,
                }
            )
        return results

    def get_geo_performance(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT
                campaign.name,
                campaign.status,
                geographic_view.country_criterion_id,
                geographic_view.location_type,
                metrics.cost_micros,
                metrics.conversions,
                metrics.clicks,
                metrics.impressions
            FROM geographic_view
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
            ORDER BY metrics.cost_micros DESC
            LIMIT 100
        """
        rows = self._query(query)
        results = []
        for row in rows:
            cost = row.metrics.cost_micros / 1_000_000
            conversions = row.metrics.conversions
            results.append(
                {
                    "campaign_name": row.campaign.name,
                    "country_id": str(row.geographic_view.country_criterion_id),
                    "location_type": str(row.geographic_view.location_type).split(
                        "."
                    )[-1],
                    "cost": cost,
                    "conversions": conversions,
                    "clicks": row.metrics.clicks,
                    "impressions": row.metrics.impressions,
                    "cpa": cost / conversions if conversions > 0 else 0,
                }
            )
        return results

    def get_auction_insights(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT
                campaign.name,
                campaign.status,
                auction_insight.display_domain,
                metrics.auction_insight_search_impression_share,
                metrics.auction_insight_search_overlap_rate,
                metrics.auction_insight_search_position_above_rate,
                metrics.auction_insight_search_top_impression_percentage,
                metrics.auction_insight_search_outranking_share
            FROM auction_insight
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
        """
        try:
            rows = self._query(query)
        except Exception:
            return []

        results = []
        for row in rows:
            results.append(
                {
                    "campaign_name": row.campaign.name,
                    "competitor_domain": row.auction_insight.display_domain,
                    "impression_share": row.metrics.auction_insight_search_impression_share,
                    "overlap_rate": row.metrics.auction_insight_search_overlap_rate,
                    "position_above_rate": row.metrics.auction_insight_search_position_above_rate,
                    "top_of_page_rate": row.metrics.auction_insight_search_top_impression_percentage,
                    "outranking_share": row.metrics.auction_insight_search_outranking_share,
                }
            )
        return results

    def get_hourly_performance(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        query = f"""
            SELECT
                campaign.name,
                campaign.status,
                segments.hour,
                segments.day_of_week,
                metrics.cost_micros,
                metrics.conversions,
                metrics.clicks,
                metrics.impressions
            FROM campaign
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
        """
        rows = self._query(query)
        results = []
        for row in rows:
            cost = row.metrics.cost_micros / 1_000_000
            conversions = row.metrics.conversions
            results.append(
                {
                    "campaign_name": row.campaign.name,
                    "hour": row.segments.hour,
                    "day_of_week": str(row.segments.day_of_week).split(".")[-1],
                    "cost": cost,
                    "conversions": conversions,
                    "clicks": row.metrics.clicks,
                    "impressions": row.metrics.impressions,
                }
            )
        return results

    def get_ad_copy_performance(
        self, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Fetch responsive search ad copy text and performance metrics."""
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                ad_group.id,
                ad_group.name,
                ad_group_ad.ad.id,
                ad_group_ad.status,
                ad_group_ad.ad.type,
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.responsive_search_ad.descriptions,
                ad_group_ad.ad.final_urls,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.conversions,
                metrics.cost_micros
            FROM ad_group_ad
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.status = 'ENABLED'
                AND ad_group_ad.status != 'REMOVED'
                AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
            ORDER BY metrics.impressions DESC
            LIMIT 100
        """
        try:
            rows = self._query(query)
        except Exception:
            return []

        results = []
        for row in rows:
            cost = row.metrics.cost_micros / 1_000_000
            conversions = row.metrics.conversions

            # Extract headline/description text from AdTextAsset objects
            headlines = []
            for asset in row.ad_group_ad.ad.responsive_search_ad.headlines:
                headlines.append(asset.text)

            descriptions = []
            for asset in row.ad_group_ad.ad.responsive_search_ad.descriptions:
                descriptions.append(asset.text)

            final_urls = list(row.ad_group_ad.ad.final_urls)

            results.append(
                {
                    "campaign_id": str(row.campaign.id),
                    "campaign_name": row.campaign.name,
                    "ad_group_id": str(row.ad_group.id),
                    "ad_group_name": row.ad_group.name,
                    "ad_id": str(row.ad_group_ad.ad.id),
                    "status": str(row.ad_group_ad.status).split(".")[-1].lower(),
                    "headlines": headlines,
                    "descriptions": descriptions,
                    "final_urls": final_urls,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "ctr": row.metrics.ctr,
                    "conversions": conversions,
                    "cost": cost,
                    "cpa": cost / conversions if conversions > 0 else 0,
                }
            )
        return results

    def get_campaign_daily_performance(
        self, campaign_id: str, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        """Fetch daily performance data for a specific campaign."""
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                segments.date,
                metrics.cost_micros,
                metrics.conversions,
                metrics.clicks,
                metrics.impressions,
                metrics.ctr,
                metrics.average_cpc,
                metrics.conversions_value,
                metrics.search_impression_share
            FROM campaign
            WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
                AND campaign.id = {campaign_id}
            ORDER BY segments.date
        """
        rows = self._query(query)
        results = []
        for row in rows:
            cost = row.metrics.cost_micros / 1_000_000
            conversions = row.metrics.conversions
            cpa = cost / conversions if conversions > 0 else 0
            conv_value = row.metrics.conversions_value
            roas = conv_value / cost if cost > 0 else 0

            results.append(
                {
                    "date": str(row.segments.date),
                    "cost": cost,
                    "conversions": conversions,
                    "clicks": row.metrics.clicks,
                    "impressions": row.metrics.impressions,
                    "ctr": row.metrics.ctr,
                    "cpa": cpa,
                    "roas": roas,
                    "average_cpc": row.metrics.average_cpc / 1_000_000,
                    "conversions_value": conv_value,
                    "impression_share": row.metrics.search_impression_share or 0,
                }
            )
        return results

    @staticmethod
    def _map_channel_type(channel: str) -> str:
        mapping = {
            "search": "search",
            "display": "display",
            "performance_max": "pmax",
            "video": "video",
            "shopping": "search",
            "multi_channel": "pmax",
        }
        return mapping.get(channel, "search")
