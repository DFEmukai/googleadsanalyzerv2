"""Report generation orchestrator.

Coordinates data fetching, analysis, and database storage
for the weekly analysis cycle. Integrates Chatwork notifications.
"""

import logging
from datetime import date
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.weekly_report import WeeklyReport
from app.models.proposal import ImprovementProposal, ProposalCategory, Priority, ProposalStatus
from app.models.auction_insight import AuctionInsight
from app.models.campaign import Campaign, CampaignStatus
from app.services.data_fetcher import DataFetcher
from app.services.claude_analyzer import ClaudeAnalyzer
from app.services.chatwork import ChatworkService
from app.services.impact_tracker import ImpactTracker

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.data_fetcher = DataFetcher(db)
        self.analyzer = ClaudeAnalyzer()
        self.chatwork = ChatworkService()
        self.impact_tracker = ImpactTracker(db)

    async def generate_weekly_report(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        send_chatwork: bool = True,
    ) -> dict[str, Any]:
        """Generate a complete weekly report with analysis and proposals."""
        # Step 1: Fetch data
        data = await self.data_fetcher.fetch_weekly_data(start_date, end_date)

        # Step 2: Get previous week's KPI for comparison
        previous_kpi = await self._get_previous_kpi(data["start_date"])

        # Step 3: Analyze with Claude
        analysis = self.analyzer.analyze(
            raw_data=data["raw_data"],
            kpi_snapshot=data["kpi_snapshot"],
            previous_kpi=previous_kpi,
        )

        # Step 4: Save report
        report = WeeklyReport(
            week_start_date=data["start_date"],
            week_end_date=data["end_date"],
            raw_data=data["raw_data"],
            analysis_summary=analysis.get("analysis_summary", ""),
            kpi_snapshot=data["kpi_snapshot"],
        )
        self.db.add(report)
        await self.db.flush()

        # Step 5: Save proposals
        proposals_created = []
        for proposal_data in analysis.get("proposals", []):
            # Include target_campaign_id in action_steps if provided
            action_steps = proposal_data.get("action_steps", [])
            target_campaign_id = proposal_data.get("target_campaign_id")
            if target_campaign_id:
                if isinstance(action_steps, dict):
                    action_steps["target_campaign_id"] = target_campaign_id
                elif isinstance(action_steps, list):
                    # Wrap list in dict to include campaign_id
                    action_steps = {
                        "steps": action_steps,
                        "target_campaign_id": target_campaign_id,
                    }

            proposal = ImprovementProposal(
                report_id=report.id,
                category=self._map_category(proposal_data.get("category", "keyword")),
                priority=self._map_priority(proposal_data.get("priority", "medium")),
                title=proposal_data.get("title", ""),
                description=proposal_data.get("description", ""),
                expected_effect=proposal_data.get("expected_effect", ""),
                action_steps=action_steps,
                target_campaign=proposal_data.get("target_campaign"),
                target_ad_group=proposal_data.get("target_ad_group"),
            )
            self.db.add(proposal)
            proposals_created.append(proposal_data)

        # Step 6: Save auction insights
        for insight_data in data["raw_data"].get("auction_insights", []):
            if insight_data.get("competitor_domain"):
                auction = AuctionInsight(
                    report_id=report.id,
                    competitor_domain=insight_data["competitor_domain"],
                    impression_share=insight_data.get("impression_share"),
                    overlap_rate=insight_data.get("overlap_rate"),
                    position_above_rate=insight_data.get("position_above_rate"),
                    top_of_page_rate=insight_data.get("top_of_page_rate"),
                    outranking_share=insight_data.get("outranking_share"),
                )
                self.db.add(auction)

        await self.db.commit()

        # Step 7: Collect after data for executed proposals
        impact_results = await self._collect_after_snapshots(
            data["kpi_snapshot"],
            data["start_date"],
            data["end_date"],
        )

        # Step 8: Clean up old proposals for inactive campaigns
        cleanup_result = await self.cleanup_inactive_proposals()
        logger.info(f"Cleanup: skipped {cleanup_result['skipped_count']} proposals for inactive campaigns")

        # Step 9: Send Chatwork notification
        chatwork_result = None
        if send_chatwork and self.chatwork.is_configured():
            try:
                high_priority = [
                    p for p in proposals_created
                    if p.get("priority", "").lower() == "high"
                ]
                # Separate manual_creative proposals for Chatwork task creation
                manual_creative_proposals = [
                    p for p in proposals_created
                    if p.get("category") == "manual_creative"
                ]
                chatwork_result = await self.chatwork.send_weekly_report(
                    report_id=str(report.id),
                    week_start=data["start_date"],
                    week_end=data["end_date"],
                    kpi_snapshot=data["kpi_snapshot"],
                    previous_kpi=previous_kpi,
                    high_priority_proposals=high_priority,
                    manual_creative_proposals=manual_creative_proposals,
                )
            except Exception as e:
                logger.error(f"Chatwork notification failed: {e}")
                chatwork_result = {"message_sent": False, "errors": [str(e)]}

        return {
            "report_id": str(report.id),
            "week_start": str(data["start_date"]),
            "week_end": str(data["end_date"]),
            "analysis_summary": analysis.get("analysis_summary", ""),
            "proposals_generated": len(proposals_created),
            "status": "completed",
            "chatwork": chatwork_result,
            "impact_tracking": impact_results,
            "cleanup": cleanup_result,
        }

    async def _get_previous_kpi(self, current_week_start: date) -> dict[str, Any] | None:
        """Get the KPI snapshot from the previous week's report."""
        result = await self.db.execute(
            select(WeeklyReport)
            .where(WeeklyReport.week_start_date < current_week_start)
            .order_by(desc(WeeklyReport.week_start_date))
            .limit(1)
        )
        previous_report = result.scalar_one_or_none()
        if previous_report and previous_report.kpi_snapshot:
            return previous_report.kpi_snapshot
        return None

    @staticmethod
    def _map_category(category: str) -> ProposalCategory:
        mapping = {
            "keyword": ProposalCategory.KEYWORD,
            "ad_copy": ProposalCategory.AD_COPY,
            "creative": ProposalCategory.CREATIVE,
            "targeting": ProposalCategory.TARGETING,
            "budget": ProposalCategory.BUDGET,
            "bidding": ProposalCategory.BIDDING,
            "competitive_response": ProposalCategory.COMPETITIVE_RESPONSE,
            "manual_creative": ProposalCategory.MANUAL_CREATIVE,
        }
        return mapping.get(category, ProposalCategory.KEYWORD)

    @staticmethod
    def _map_priority(priority: str) -> Priority:
        mapping = {
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW,
        }
        return mapping.get(priority, Priority.MEDIUM)

    async def _collect_after_snapshots(
        self,
        kpi_snapshot: dict[str, Any],
        period_start: date,
        period_end: date,
    ) -> dict[str, Any]:
        """Collect after snapshots for proposals executed more than 7 days ago."""
        proposals = await self.impact_tracker.get_proposals_needing_after_snapshot(
            min_days_since_execution=7
        )

        if not proposals:
            return {"collected": 0, "proposals": []}

        # Build KPI data from current snapshot
        kpi_data = {
            "cost": kpi_snapshot.get("total_cost"),
            "conversions": kpi_snapshot.get("total_conversions"),
            "cpa": kpi_snapshot.get("cpa"),
            "ctr": kpi_snapshot.get("ctr"),
            "roas": kpi_snapshot.get("roas"),
            "impressions": kpi_snapshot.get("impressions"),
            "clicks": kpi_snapshot.get("clicks"),
            "conversion_value": kpi_snapshot.get("conversion_value"),
        }

        collected = []
        for proposal in proposals:
            try:
                # Extract campaign_id if possible
                campaign_id = None
                for step in (proposal.action_steps or []):
                    if isinstance(step, dict) and step.get("campaign_id"):
                        campaign_id = str(step["campaign_id"])
                        break

                await self.impact_tracker.save_after_snapshot(
                    proposal_id=proposal.id,
                    kpi_data=kpi_data,
                    period_start=period_start,
                    period_end=period_end,
                    campaign_id=campaign_id,
                )
                collected.append({
                    "proposal_id": str(proposal.id),
                    "title": proposal.title,
                })
                logger.info(f"Collected after snapshot for proposal {proposal.id}")
            except Exception as e:
                logger.error(f"Failed to collect after snapshot for {proposal.id}: {e}")

        await self.db.commit()

        return {"collected": len(collected), "proposals": collected}

    async def cleanup_inactive_proposals(self) -> dict[str, Any]:
        """Clean up pending proposals for inactive/non-existent campaigns.

        Sets status to 'skipped' for proposals where:
        - status is 'pending'
        - target_campaign is set
        - campaign doesn't exist OR campaign status is not 'active'
        """
        # Get all pending proposals with target_campaign
        query = select(ImprovementProposal).where(
            ImprovementProposal.status == ProposalStatus.PENDING,
            ImprovementProposal.target_campaign.isnot(None),
        )
        result = await self.db.execute(query)
        proposals = result.scalars().all()

        # Get all active campaigns
        campaign_result = await self.db.execute(select(Campaign))
        campaigns = campaign_result.scalars().all()
        active_campaigns = {
            c.campaign_name for c in campaigns if c.status == CampaignStatus.ACTIVE
        }

        # Mark proposals as skipped
        skipped = []
        for p in proposals:
            if p.target_campaign and p.target_campaign not in active_campaigns:
                p.status = ProposalStatus.SKIPPED
                skipped.append({
                    "id": str(p.id),
                    "title": p.title,
                    "target_campaign": p.target_campaign,
                })
                logger.info(f"Skipped proposal {p.id} for inactive campaign: {p.target_campaign}")

        if skipped:
            await self.db.commit()

        return {"skipped_count": len(skipped), "proposals": skipped}
