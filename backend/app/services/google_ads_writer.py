"""Google Ads API write operations.

Handles mutate operations for approved improvement proposals:
- Budget changes
- Bid strategy changes
- Keyword additions/removals
- Ad copy changes
- Targeting adjustments
"""

import logging
from datetime import datetime
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)


class GoogleAdsWriter:
    """Handles Google Ads API write (mutate) operations."""

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

    def update_campaign_budget(
        self, campaign_id: str, new_budget_micros: int
    ) -> dict[str, Any]:
        """Update a campaign's daily budget.

        Args:
            campaign_id: The Google Ads campaign ID
            new_budget_micros: New daily budget in micros (1 JPY = 1,000,000 micros)

        Returns:
            Dict with operation result and previous value
        """
        client = self._get_client()
        ga_service = client.get_service("GoogleAdsService")
        campaign_budget_service = client.get_service("CampaignBudgetService")

        # First, get current budget resource name
        query = f"""
            SELECT
                campaign.id,
                campaign.campaign_budget,
                campaign_budget.amount_micros
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """
        response = ga_service.search(
            customer_id=self.customer_id, query=query
        )

        current_budget_micros = None
        budget_resource_name = None
        for row in response:
            current_budget_micros = row.campaign_budget.amount_micros
            budget_resource_name = row.campaign.campaign_budget

        if not budget_resource_name:
            raise ValueError(f"Campaign {campaign_id} not found or has no budget")

        # Mutate the budget
        operation = client.get_type("CampaignBudgetOperation")
        campaign_budget = operation.update
        campaign_budget.resource_name = budget_resource_name
        campaign_budget.amount_micros = new_budget_micros

        field_mask = client.get_type("FieldMask")
        field_mask.paths.append("amount_micros")
        operation.update_mask.CopyFrom(field_mask)

        response = campaign_budget_service.mutate_campaign_budgets(
            customer_id=self.customer_id,
            operations=[operation],
        )

        logger.info(
            f"Budget updated for campaign {campaign_id}: "
            f"{current_budget_micros} -> {new_budget_micros}"
        )

        return {
            "operation": "update_campaign_budget",
            "campaign_id": campaign_id,
            "previous_value": current_budget_micros,
            "new_value": new_budget_micros,
            "resource_name": response.results[0].resource_name,
        }

    def update_campaign_target_cpa(
        self, campaign_id: str, target_cpa_micros: int
    ) -> dict[str, Any]:
        """Update a campaign's target CPA.

        Args:
            campaign_id: The Google Ads campaign ID
            target_cpa_micros: New target CPA in micros
        """
        client = self._get_client()
        ga_service = client.get_service("GoogleAdsService")
        campaign_service = client.get_service("CampaignService")

        # Get current target CPA
        query = f"""
            SELECT
                campaign.id,
                campaign.bidding_strategy_type,
                campaign.target_cpa.target_cpa_micros
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """
        response = ga_service.search(
            customer_id=self.customer_id, query=query
        )

        current_target_cpa = None
        resource_name = None
        for row in response:
            current_target_cpa = row.campaign.target_cpa.target_cpa_micros
            resource_name = row.campaign.resource_name

        if not resource_name:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Mutate
        operation = client.get_type("CampaignOperation")
        campaign = operation.update
        campaign.resource_name = resource_name
        campaign.target_cpa.target_cpa_micros = target_cpa_micros

        field_mask = client.get_type("FieldMask")
        field_mask.paths.append("target_cpa.target_cpa_micros")
        operation.update_mask.CopyFrom(field_mask)

        response = campaign_service.mutate_campaigns(
            customer_id=self.customer_id,
            operations=[operation],
        )

        logger.info(
            f"Target CPA updated for campaign {campaign_id}: "
            f"{current_target_cpa} -> {target_cpa_micros}"
        )

        return {
            "operation": "update_target_cpa",
            "campaign_id": campaign_id,
            "previous_value": current_target_cpa,
            "new_value": target_cpa_micros,
            "resource_name": response.results[0].resource_name,
        }

    def update_campaign_target_roas(
        self, campaign_id: str, target_roas: float
    ) -> dict[str, Any]:
        """Update a campaign's target ROAS.

        Args:
            campaign_id: The Google Ads campaign ID
            target_roas: New target ROAS (e.g., 3.5 = 350%)
        """
        client = self._get_client()
        ga_service = client.get_service("GoogleAdsService")
        campaign_service = client.get_service("CampaignService")

        query = f"""
            SELECT
                campaign.id,
                campaign.target_roas.target_roas
            FROM campaign
            WHERE campaign.id = {campaign_id}
        """
        response = ga_service.search(
            customer_id=self.customer_id, query=query
        )

        current_target_roas = None
        resource_name = None
        for row in response:
            current_target_roas = row.campaign.target_roas.target_roas
            resource_name = row.campaign.resource_name

        if not resource_name:
            raise ValueError(f"Campaign {campaign_id} not found")

        operation = client.get_type("CampaignOperation")
        campaign = operation.update
        campaign.resource_name = resource_name
        campaign.target_roas.target_roas = target_roas

        field_mask = client.get_type("FieldMask")
        field_mask.paths.append("target_roas.target_roas")
        operation.update_mask.CopyFrom(field_mask)

        response = campaign_service.mutate_campaigns(
            customer_id=self.customer_id,
            operations=[operation],
        )

        return {
            "operation": "update_target_roas",
            "campaign_id": campaign_id,
            "previous_value": current_target_roas,
            "new_value": target_roas,
            "resource_name": response.results[0].resource_name,
        }

    def add_negative_keywords(
        self, campaign_id: str, keywords: list[str], match_type: str = "EXACT"
    ) -> dict[str, Any]:
        """Add negative keywords to a campaign.

        Args:
            campaign_id: The Google Ads campaign ID
            keywords: List of keyword texts to add as negatives
            match_type: EXACT, PHRASE, or BROAD
        """
        client = self._get_client()
        campaign_criterion_service = client.get_service(
            "CampaignCriterionService"
        )

        operations = []
        for keyword_text in keywords:
            operation = client.get_type("CampaignCriterionOperation")
            criterion = operation.create
            criterion.campaign = client.get_service(
                "GoogleAdsService"
            ).campaign_path(self.customer_id, campaign_id)
            criterion.negative = True
            criterion.keyword.text = keyword_text
            criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[
                match_type
            ].value
            operations.append(operation)

        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=self.customer_id,
            operations=operations,
        )

        logger.info(
            f"Added {len(keywords)} negative keywords to campaign {campaign_id}"
        )

        return {
            "operation": "add_negative_keywords",
            "campaign_id": campaign_id,
            "keywords_added": keywords,
            "match_type": match_type,
            "count": len(response.results),
            "resource_names": [r.resource_name for r in response.results],
        }

    def add_keywords(
        self,
        ad_group_id: str,
        keywords: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Add keywords to an ad group.

        Args:
            ad_group_id: The ad group ID
            keywords: List of dicts with 'text', 'match_type', and optionally 'cpc_bid_micros'
        """
        client = self._get_client()
        ad_group_criterion_service = client.get_service(
            "AdGroupCriterionService"
        )

        operations = []
        for kw in keywords:
            operation = client.get_type("AdGroupCriterionOperation")
            criterion = operation.create
            criterion.ad_group = client.get_service(
                "GoogleAdsService"
            ).ad_group_path(self.customer_id, ad_group_id)
            criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
            criterion.keyword.text = kw["text"]
            criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[
                kw.get("match_type", "BROAD")
            ].value
            if kw.get("cpc_bid_micros"):
                criterion.cpc_bid_micros = kw["cpc_bid_micros"]
            operations.append(operation)

        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=self.customer_id,
            operations=operations,
        )

        return {
            "operation": "add_keywords",
            "ad_group_id": ad_group_id,
            "keywords_added": [kw["text"] for kw in keywords],
            "count": len(response.results),
            "resource_names": [r.resource_name for r in response.results],
        }

    def pause_keyword(
        self, ad_group_id: str, criterion_id: str
    ) -> dict[str, Any]:
        """Pause a keyword in an ad group."""
        client = self._get_client()
        ad_group_criterion_service = client.get_service(
            "AdGroupCriterionService"
        )

        resource_name = client.get_service(
            "GoogleAdsService"
        ).ad_group_criterion_path(self.customer_id, ad_group_id, criterion_id)

        operation = client.get_type("AdGroupCriterionOperation")
        criterion = operation.update
        criterion.resource_name = resource_name
        criterion.status = client.enums.AdGroupCriterionStatusEnum.PAUSED

        field_mask = client.get_type("FieldMask")
        field_mask.paths.append("status")
        operation.update_mask.CopyFrom(field_mask)

        response = ad_group_criterion_service.mutate_ad_group_criteria(
            customer_id=self.customer_id,
            operations=[operation],
        )

        return {
            "operation": "pause_keyword",
            "ad_group_id": ad_group_id,
            "criterion_id": criterion_id,
            "resource_name": response.results[0].resource_name,
        }

    def update_device_bid_modifier(
        self,
        campaign_id: str,
        device_type: str,
        bid_modifier: float,
    ) -> dict[str, Any]:
        """Update device bid modifier for a campaign.

        Args:
            campaign_id: Campaign ID
            device_type: MOBILE, DESKTOP, or TABLET
            bid_modifier: Bid modifier (e.g., 1.2 = +20%, 0.8 = -20%)
        """
        client = self._get_client()
        campaign_criterion_service = client.get_service(
            "CampaignCriterionService"
        )

        device_enum = client.enums.DeviceEnum[device_type].value

        # Check if criterion already exists
        ga_service = client.get_service("GoogleAdsService")
        query = f"""
            SELECT
                campaign_criterion.resource_name,
                campaign_criterion.device.type
            FROM campaign_criterion
            WHERE campaign.id = {campaign_id}
                AND campaign_criterion.type = 'DEVICE'
                AND campaign_criterion.device.type = '{device_type}'
        """

        response = ga_service.search(
            customer_id=self.customer_id, query=query
        )

        existing_resource = None
        for row in response:
            existing_resource = row.campaign_criterion.resource_name

        if existing_resource:
            # Update existing
            operation = client.get_type("CampaignCriterionOperation")
            criterion = operation.update
            criterion.resource_name = existing_resource
            criterion.bid_modifier = bid_modifier

            field_mask = client.get_type("FieldMask")
            field_mask.paths.append("bid_modifier")
            operation.update_mask.CopyFrom(field_mask)
        else:
            # Create new
            operation = client.get_type("CampaignCriterionOperation")
            criterion = operation.create
            criterion.campaign = ga_service.campaign_path(
                self.customer_id, campaign_id
            )
            criterion.device.type_ = device_enum
            criterion.bid_modifier = bid_modifier

        response = campaign_criterion_service.mutate_campaign_criteria(
            customer_id=self.customer_id,
            operations=[operation],
        )

        return {
            "operation": "update_device_bid_modifier",
            "campaign_id": campaign_id,
            "device_type": device_type,
            "bid_modifier": bid_modifier,
            "resource_name": response.results[0].resource_name,
        }

    def create_responsive_search_ad(
        self,
        ad_group_id: str,
        headlines: list[str],
        descriptions: list[str],
        final_url: str,
    ) -> dict[str, Any]:
        """Create a responsive search ad.

        Args:
            ad_group_id: The ad group ID
            headlines: List of headline texts (3-15)
            descriptions: List of description texts (2-4)
            final_url: The landing page URL
        """
        client = self._get_client()
        ad_group_ad_service = client.get_service("AdGroupAdService")

        operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = operation.create
        ad_group_ad.ad_group = client.get_service(
            "GoogleAdsService"
        ).ad_group_path(self.customer_id, ad_group_id)
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED  # Start paused for review

        ad = ad_group_ad.ad
        ad.final_urls.append(final_url)

        for headline_text in headlines:
            headline = client.get_type("AdTextAsset")
            headline.text = headline_text
            ad.responsive_search_ad.headlines.append(headline)

        for desc_text in descriptions:
            description = client.get_type("AdTextAsset")
            description.text = desc_text
            ad.responsive_search_ad.descriptions.append(description)

        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=self.customer_id,
            operations=[operation],
        )

        return {
            "operation": "create_responsive_search_ad",
            "ad_group_id": ad_group_id,
            "headlines": headlines,
            "descriptions": descriptions,
            "final_url": final_url,
            "resource_name": response.results[0].resource_name,
        }

    def pause_ad(self, ad_group_id: str, ad_id: str) -> dict[str, Any]:
        """Pause an ad."""
        client = self._get_client()
        ad_group_ad_service = client.get_service("AdGroupAdService")

        resource_name = client.get_service(
            "GoogleAdsService"
        ).ad_group_ad_path(self.customer_id, ad_group_id, ad_id)

        operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = operation.update
        ad_group_ad.resource_name = resource_name
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED

        field_mask = client.get_type("FieldMask")
        field_mask.paths.append("status")
        operation.update_mask.CopyFrom(field_mask)

        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=self.customer_id,
            operations=[operation],
        )

        return {
            "operation": "pause_ad",
            "ad_group_id": ad_group_id,
            "ad_id": ad_id,
            "resource_name": response.results[0].resource_name,
        }

    def enable_ad(self, ad_group_id: str, ad_id: str) -> dict[str, Any]:
        """Enable a paused ad."""
        client = self._get_client()
        ad_group_ad_service = client.get_service("AdGroupAdService")

        resource_name = client.get_service(
            "GoogleAdsService"
        ).ad_group_ad_path(self.customer_id, ad_group_id, ad_id)

        operation = client.get_type("AdGroupAdOperation")
        ad_group_ad = operation.update
        ad_group_ad.resource_name = resource_name
        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED

        field_mask = client.get_type("FieldMask")
        field_mask.paths.append("status")
        operation.update_mask.CopyFrom(field_mask)

        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=self.customer_id,
            operations=[operation],
        )

        return {
            "operation": "enable_ad",
            "ad_group_id": ad_group_id,
            "ad_id": ad_id,
            "resource_name": response.results[0].resource_name,
        }
