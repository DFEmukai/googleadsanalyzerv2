"""Impact tracking service for proposal effect measurement."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ImprovementProposal, ProposalSnapshot, ProposalExecution
from app.models.snapshot import SnapshotType


class ImpactTracker:
    """Service for tracking and calculating proposal impact."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_before_snapshot(
        self,
        proposal_id: UUID,
        kpi_data: dict[str, Any],
        period_start: date,
        period_end: date,
        campaign_id: str | None = None,
    ) -> ProposalSnapshot:
        """Save a 'before' KPI snapshot when a proposal is executed."""
        snapshot = ProposalSnapshot(
            proposal_id=proposal_id,
            snapshot_type=SnapshotType.before,
            campaign_id=campaign_id,
            cost=kpi_data.get("cost"),
            conversions=kpi_data.get("conversions"),
            cpa=kpi_data.get("cpa"),
            ctr=kpi_data.get("ctr"),
            roas=kpi_data.get("roas"),
            impressions=kpi_data.get("impressions"),
            clicks=kpi_data.get("clicks"),
            conversion_value=kpi_data.get("conversion_value"),
            period_start=period_start,
            period_end=period_end,
        )
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def save_after_snapshot(
        self,
        proposal_id: UUID,
        kpi_data: dict[str, Any],
        period_start: date,
        period_end: date,
        campaign_id: str | None = None,
    ) -> ProposalSnapshot:
        """Save an 'after' KPI snapshot for impact measurement."""
        # Check if after snapshot already exists
        result = await self.db.execute(
            select(ProposalSnapshot).where(
                ProposalSnapshot.proposal_id == proposal_id,
                ProposalSnapshot.snapshot_type == SnapshotType.after,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing snapshot
            existing.cost = kpi_data.get("cost")
            existing.conversions = kpi_data.get("conversions")
            existing.cpa = kpi_data.get("cpa")
            existing.ctr = kpi_data.get("ctr")
            existing.roas = kpi_data.get("roas")
            existing.impressions = kpi_data.get("impressions")
            existing.clicks = kpi_data.get("clicks")
            existing.conversion_value = kpi_data.get("conversion_value")
            existing.period_start = period_start
            existing.period_end = period_end
            await self.db.flush()
            return existing

        snapshot = ProposalSnapshot(
            proposal_id=proposal_id,
            snapshot_type=SnapshotType.after,
            campaign_id=campaign_id,
            cost=kpi_data.get("cost"),
            conversions=kpi_data.get("conversions"),
            cpa=kpi_data.get("cpa"),
            ctr=kpi_data.get("ctr"),
            roas=kpi_data.get("roas"),
            impressions=kpi_data.get("impressions"),
            clicks=kpi_data.get("clicks"),
            conversion_value=kpi_data.get("conversion_value"),
            period_start=period_start,
            period_end=period_end,
        )
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def get_impact_report(self, proposal_id: UUID) -> dict[str, Any] | None:
        """Get the impact report for an executed proposal."""
        # Load proposal with snapshots
        result = await self.db.execute(
            select(ImprovementProposal)
            .options(
                selectinload(ImprovementProposal.snapshots),
                selectinload(ImprovementProposal.execution),
            )
            .where(ImprovementProposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()

        if not proposal:
            return None

        if not proposal.snapshots:
            return {"status": "no_data", "message": "スナップショットがありません"}

        before_snapshot = None
        after_snapshot = None

        for snapshot in proposal.snapshots:
            if snapshot.snapshot_type == SnapshotType.before:
                before_snapshot = snapshot
            elif snapshot.snapshot_type == SnapshotType.after:
                after_snapshot = snapshot

        if not before_snapshot:
            return {"status": "no_before", "message": "実行前のデータがありません"}

        # Build before data
        before_data = self._snapshot_to_dict(before_snapshot)

        # Build response
        response: dict[str, Any] = {
            "status": "available" if after_snapshot else "pending",
            "before": before_data,
            "period": {
                "before": f"{before_snapshot.period_start}~{before_snapshot.period_end}",
            },
        }

        if after_snapshot:
            after_data = self._snapshot_to_dict(after_snapshot)
            change_data = self._calculate_change(before_data, after_data)

            response["after"] = after_data
            response["change"] = change_data
            response["period"]["after"] = (
                f"{after_snapshot.period_start}~{after_snapshot.period_end}"
            )
        else:
            # Calculate when after data will be available
            if proposal.execution:
                executed_at = proposal.execution.executed_at
                available_after = executed_at + timedelta(days=7)
                response["message"] = f"効果測定は {available_after.strftime('%Y-%m-%d')} 以降に利用可能になります"

        return response

    async def get_proposals_needing_after_snapshot(
        self,
        min_days_since_execution: int = 7,
    ) -> list[ImprovementProposal]:
        """Get executed proposals that need after snapshots collected."""
        from datetime import datetime

        cutoff_date = datetime.now() - timedelta(days=min_days_since_execution)

        # Find executed proposals with before snapshot but no after snapshot
        result = await self.db.execute(
            select(ImprovementProposal)
            .join(ProposalExecution)
            .options(
                selectinload(ImprovementProposal.snapshots),
                selectinload(ImprovementProposal.execution),
            )
            .where(
                ImprovementProposal.status == "executed",
                ProposalExecution.executed_at <= cutoff_date,
            )
        )
        proposals = result.scalars().all()

        # Filter to those with before but no after snapshot
        needs_after = []
        for proposal in proposals:
            has_before = False
            has_after = False
            for snapshot in proposal.snapshots:
                if snapshot.snapshot_type == SnapshotType.before:
                    has_before = True
                elif snapshot.snapshot_type == SnapshotType.after:
                    has_after = True

            if has_before and not has_after:
                needs_after.append(proposal)

        return needs_after

    def _snapshot_to_dict(self, snapshot: ProposalSnapshot) -> dict[str, Any]:
        """Convert a snapshot to a dictionary."""
        return {
            "cost": float(snapshot.cost) if snapshot.cost else None,
            "conversions": float(snapshot.conversions) if snapshot.conversions else None,
            "cpa": float(snapshot.cpa) if snapshot.cpa else None,
            "ctr": float(snapshot.ctr) if snapshot.ctr else None,
            "roas": float(snapshot.roas) if snapshot.roas else None,
            "impressions": int(snapshot.impressions) if snapshot.impressions else None,
            "clicks": int(snapshot.clicks) if snapshot.clicks else None,
            "conversion_value": (
                float(snapshot.conversion_value) if snapshot.conversion_value else None
            ),
        }

    def _calculate_change(
        self,
        before: dict[str, Any],
        after: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate percentage change between before and after."""
        change = {}

        for key in ["cost", "conversions", "cpa", "ctr", "roas", "impressions", "clicks", "conversion_value"]:
            before_val = before.get(key)
            after_val = after.get(key)

            if before_val is not None and after_val is not None and before_val != 0:
                pct_change = ((after_val - before_val) / before_val) * 100
                change[key] = round(pct_change, 1)
            else:
                change[key] = None

        return change
