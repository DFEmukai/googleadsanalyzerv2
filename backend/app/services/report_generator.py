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
from app.models.proposal import ImprovementProposal, ProposalCategory, Priority
from app.models.auction_insight import AuctionInsight
from app.services.data_fetcher import DataFetcher
from app.services.claude_analyzer import ClaudeAnalyzer
from app.services.chatwork import ChatworkService

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.data_fetcher = DataFetcher(db)
        self.analyzer = ClaudeAnalyzer()
        self.chatwork = ChatworkService()

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
            proposal = ImprovementProposal(
                report_id=report.id,
                category=self._map_category(proposal_data.get("category", "keyword")),
                priority=self._map_priority(proposal_data.get("priority", "medium")),
                title=proposal_data.get("title", ""),
                description=proposal_data.get("description", ""),
                expected_effect=proposal_data.get("expected_effect", ""),
                action_steps=proposal_data.get("action_steps", []),
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

        # Step 7: Send Chatwork notification
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
