"""Proposal execution service with safeguards.

Handles the approval → execution → recording flow for
improvement proposals, with safety limits and rollback capability.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.proposal import ImprovementProposal, ProposalStatus
from app.models.execution import ProposalExecution
from app.models.weekly_report import WeeklyReport
from app.services.google_ads_writer import GoogleAdsWriter
from app.services.chatwork import ChatworkService
from app.services.ad_copy_validator import (
    validate_ad_copy,
    validate_action_steps_structure,
    AdCopyValidationError,
)
from app.services.impact_tracker import ImpactTracker

logger = logging.getLogger(__name__)


class SafeguardError(Exception):
    """Raised when a safeguard check fails."""
    pass


class ProposalExecutor:
    """Executes approved proposals via Google Ads API with safeguards."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.writer = GoogleAdsWriter()
        self.chatwork = ChatworkService()
        self.settings = get_settings()
        self.impact_tracker = ImpactTracker(db)

    async def validate_safeguards(
        self,
        proposal: ImprovementProposal,
        edited_values: dict[str, Any] | None = None,
    ) -> list[str]:
        """Validate safeguard rules before execution.

        Returns list of warning messages. Raises SafeguardError for blocking issues.
        """
        warnings = []
        action_steps = proposal.action_steps or []

        # 1. Check max changes per approval
        change_count = len(action_steps)
        if change_count > self.settings.max_changes_per_approval:
            raise SafeguardError(
                f"変更項目数が上限を超えています "
                f"({change_count}/{self.settings.max_changes_per_approval}件)"
            )

        # 2. Check budget change limits
        if proposal.category.value == "budget" and edited_values:
            current_budget = edited_values.get("current_value", 0)
            new_budget = edited_values.get("new_value", 0)
            if current_budget > 0:
                change_pct = abs(
                    (new_budget - current_budget) / current_budget
                ) * 100
                if change_pct > self.settings.max_budget_change_pct:
                    raise SafeguardError(
                        f"予算変更率が上限を超えています "
                        f"({change_pct:.1f}% > ±{self.settings.max_budget_change_pct}%)"
                    )
                if change_pct > self.settings.max_budget_change_pct * 0.8:
                    warnings.append(
                        f"予算変更率が高めです ({change_pct:.1f}%)"
                    )

        # 3. High-risk operation detection
        high_risk_ops = ["pause_campaign", "delete", "remove"]
        for step in action_steps:
            desc = str(step.get("description", "")).lower()
            for risk_op in high_risk_ops:
                if risk_op in desc:
                    warnings.append(
                        f"高リスク操作を含みます: {step.get('description', '')}"
                    )

        return warnings

    async def execute_proposal(
        self,
        proposal_id: UUID,
        executed_by: str = "system",
        edited_values: dict[str, Any] | None = None,
        execution_notes: str = "",
    ) -> dict[str, Any]:
        """Execute an approved proposal.

        Args:
            proposal_id: The proposal to execute
            executed_by: Who executed it (user name or 'system')
            edited_values: Optional edited values overriding the AI proposal
            execution_notes: Optional notes about the execution

        Returns:
            Execution result with details
        """
        # Get proposal with report for KPI data
        result = await self.db.execute(
            select(ImprovementProposal)
            .options(selectinload(ImprovementProposal.report))
            .where(ImprovementProposal.id == proposal_id)
        )
        proposal = result.scalar_one_or_none()

        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        if proposal.status != ProposalStatus.APPROVED:
            raise ValueError(
                f"Proposal status is '{proposal.status.value}', must be 'approved'"
            )

        # Validate safeguards
        warnings = await self.validate_safeguards(proposal, edited_values)

        # Save before snapshot for impact tracking
        await self._save_before_snapshot(proposal)

        # Execute based on category
        try:
            actual_changes = await self._dispatch_execution(
                proposal, edited_values
            )
        except Exception as e:
            logger.error(f"Execution failed for proposal {proposal_id}: {e}")

            # Notify via Chatwork
            await self.chatwork.send_execution_result(
                proposal_title=proposal.title,
                success=False,
                details=str(e),
            )

            return {
                "proposal_id": str(proposal_id),
                "status": "failed",
                "error": str(e),
                "warnings": warnings,
            }

        # Record execution
        execution = ProposalExecution(
            proposal_id=proposal_id,
            executed_at=datetime.now(),
            executed_by=executed_by,
            execution_notes=execution_notes,
            actual_changes=actual_changes,
        )
        self.db.add(execution)

        # Update proposal status
        proposal.status = ProposalStatus.EXECUTED
        await self.db.commit()

        # Notify via Chatwork
        await self.chatwork.send_execution_result(
            proposal_title=proposal.title,
            success=True,
            details=f"変更 {len(actual_changes.get('operations', []))} 件を反映しました",
        )

        return {
            "proposal_id": str(proposal_id),
            "status": "success",
            "actual_changes": actual_changes,
            "warnings": warnings,
            "executed_at": execution.executed_at.isoformat(),
        }

    async def rollback_execution(
        self,
        proposal_id: UUID,
        reason: str = "",
    ) -> dict[str, Any]:
        """Rollback a previously executed proposal.

        Only possible within the rollback window (default 24 hours).
        """
        # Get proposal and execution
        result = await self.db.execute(
            select(ImprovementProposal).where(
                ImprovementProposal.id == proposal_id
            )
        )
        proposal = result.scalar_one_or_none()
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        result = await self.db.execute(
            select(ProposalExecution).where(
                ProposalExecution.proposal_id == proposal_id
            )
        )
        execution = result.scalar_one_or_none()
        if not execution:
            raise ValueError(f"No execution record for proposal {proposal_id}")

        # Check rollback window
        rollback_deadline = execution.executed_at + timedelta(
            hours=self.settings.rollback_window_hours
        )
        if datetime.now() > rollback_deadline:
            raise ValueError(
                f"ロールバック期限を超過しています "
                f"(期限: {rollback_deadline.strftime('%Y-%m-%d %H:%M')})"
            )

        # Perform rollback based on recorded changes
        actual_changes = execution.actual_changes or {}
        rollback_results = []

        try:
            for op in actual_changes.get("operations", []):
                rollback_result = self._rollback_operation(op)
                rollback_results.append(rollback_result)
        except Exception as e:
            logger.error(f"Rollback failed for proposal {proposal_id}: {e}")
            return {
                "proposal_id": str(proposal_id),
                "status": "rollback_failed",
                "error": str(e),
            }

        # Update execution record
        execution.execution_notes = (
            f"{execution.execution_notes or ''}\n"
            f"[ROLLBACK] {datetime.now().isoformat()} - {reason}"
        ).strip()
        execution.actual_changes = {
            **actual_changes,
            "rolled_back": True,
            "rollback_at": datetime.now().isoformat(),
            "rollback_reason": reason,
            "rollback_results": rollback_results,
        }

        # Update proposal status
        proposal.status = ProposalStatus.PENDING

        await self.db.commit()

        # Notify via Chatwork
        await self.chatwork.send_rollback_notification(
            proposal_title=proposal.title,
            reason=reason,
        )

        return {
            "proposal_id": str(proposal_id),
            "status": "rolled_back",
            "rollback_results": rollback_results,
        }

    async def _dispatch_execution(
        self,
        proposal: ImprovementProposal,
        edited_values: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Dispatch execution to the appropriate handler based on category."""
        category = proposal.category.value
        operations = []

        if category == "budget":
            ops = self._execute_budget_change(proposal, edited_values)
            operations.extend(ops)
        elif category == "bidding":
            ops = self._execute_bidding_change(proposal, edited_values)
            operations.extend(ops)
        elif category == "keyword":
            ops = self._execute_keyword_change(proposal, edited_values)
            operations.extend(ops)
        elif category in ("ad_copy", "creative"):
            ops = self._execute_ad_copy_change(proposal, edited_values)
            operations.extend(ops)
        elif category == "targeting":
            ops = self._execute_targeting_change(proposal, edited_values)
            operations.extend(ops)
        elif category == "manual_creative":
            raise ValueError(
                "manual_creativeカテゴリはChatworkタスクとして管理されます。"
                "画像・動画アセットの変更は手動での対応をお願いします。"
            )
        else:
            raise ValueError(
                f"カテゴリ '{category}' の自動反映は未対応です。手動での実行をお願いします。"
            )

        return {
            "category": category,
            "operations": operations,
            "executed_at": datetime.now().isoformat(),
        }

    def _execute_budget_change(
        self,
        proposal: ImprovementProposal,
        edited_values: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Execute budget-related changes."""
        results = []
        campaign_id = self._extract_campaign_id(proposal)
        if not campaign_id:
            raise ValueError("対象キャンペーンIDが特定できません")

        new_budget = None
        if edited_values and "new_value" in edited_values:
            new_budget = edited_values["new_value"]
        else:
            # Try to extract from action_steps
            for step in (proposal.action_steps or []):
                if "budget" in str(step).lower() or "予算" in str(step):
                    new_budget = step.get("value") or step.get("new_value")
                    break

        if new_budget is not None:
            budget_micros = int(float(new_budget) * 1_000_000)
            result = self.writer.update_campaign_budget(
                campaign_id=campaign_id,
                new_budget_micros=budget_micros,
            )
            results.append(result)

        return results

    def _execute_bidding_change(
        self,
        proposal: ImprovementProposal,
        edited_values: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Execute bidding strategy changes."""
        results = []
        campaign_id = self._extract_campaign_id(proposal)
        if not campaign_id:
            raise ValueError("対象キャンペーンIDが特定できません")

        if edited_values:
            if "target_cpa" in edited_values:
                cpa_micros = int(
                    float(edited_values["target_cpa"]) * 1_000_000
                )
                result = self.writer.update_campaign_target_cpa(
                    campaign_id=campaign_id,
                    target_cpa_micros=cpa_micros,
                )
                results.append(result)
            if "target_roas" in edited_values:
                result = self.writer.update_campaign_target_roas(
                    campaign_id=campaign_id,
                    target_roas=float(edited_values["target_roas"]),
                )
                results.append(result)

        return results

    def _execute_keyword_change(
        self,
        proposal: ImprovementProposal,
        edited_values: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Execute keyword changes (add/remove/negative)."""
        results = []
        campaign_id = self._extract_campaign_id(proposal)

        if edited_values:
            # Negative keywords
            neg_keywords = edited_values.get("negative_keywords", [])
            if neg_keywords and campaign_id:
                result = self.writer.add_negative_keywords(
                    campaign_id=campaign_id,
                    keywords=neg_keywords,
                    match_type=edited_values.get("match_type", "EXACT"),
                )
                results.append(result)

            # Add keywords to ad group
            add_keywords = edited_values.get("add_keywords", [])
            ad_group_id = edited_values.get("ad_group_id")
            if add_keywords and ad_group_id:
                result = self.writer.add_keywords(
                    ad_group_id=ad_group_id,
                    keywords=add_keywords,
                )
                results.append(result)

        return results

    def _execute_ad_copy_change(
        self,
        proposal: ImprovementProposal,
        edited_values: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Execute ad copy changes.

        Supports two modes:
        1. edited_values provided: Use user-edited values directly
        2. No edited_values: Auto-extract from structured action_steps
        """
        results = []

        # Determine parameters: prefer edited_values, fall back to action_steps
        if edited_values and edited_values.get("ad_group_id"):
            ad_group_id = edited_values["ad_group_id"]
            headlines = edited_values.get("headlines", [])
            descriptions = edited_values.get("descriptions", [])
            final_url = edited_values.get("final_url", "")
            old_ad_id = edited_values.get("old_ad_id")
        else:
            # Auto-extract from structured action_steps
            action_steps = proposal.action_steps
            if not isinstance(action_steps, dict):
                raise ValueError(
                    "広告文提案のaction_stepsが構造化形式ではありません。"
                    "手動で編集値を指定してください。"
                )

            if action_steps.get("type") != "ad_copy_change":
                raise ValueError(
                    f"action_steps.type が 'ad_copy_change' ではありません: "
                    f"{action_steps.get('type')}"
                )

            ad_group_id = action_steps.get("ad_group_id")
            if not ad_group_id:
                raise ValueError("action_stepsにad_group_idが含まれていません")

            proposed = action_steps.get("proposed_ad", {})
            headlines = proposed.get("headlines", [])
            descriptions = proposed.get("descriptions", [])
            final_url = proposed.get("final_url", "")

            current_ad = action_steps.get("current_ad", {})
            old_ad_id = current_ad.get("ad_id")

        # Validate ad copy before execution
        if not headlines or not descriptions or not final_url:
            raise ValueError(
                "ヘッドライン、説明文、最終ページURLがすべて必要です"
            )

        try:
            warnings = validate_ad_copy(headlines, descriptions, final_url)
            if warnings:
                logger.warning(
                    f"Ad copy validation warnings for proposal "
                    f"{proposal.id}: {warnings}"
                )
        except AdCopyValidationError as e:
            raise ValueError(
                f"広告文のバリデーションに失敗しました: {'; '.join(e.errors)}"
            )

        # Pause old ad if specified
        if old_ad_id:
            result = self.writer.pause_ad(
                ad_group_id=str(ad_group_id),
                ad_id=str(old_ad_id),
            )
            results.append(result)

        # Create new responsive search ad
        result = self.writer.create_responsive_search_ad(
            ad_group_id=str(ad_group_id),
            headlines=headlines,
            descriptions=descriptions,
            final_url=final_url,
        )
        results.append(result)

        return results

    def _execute_targeting_change(
        self,
        proposal: ImprovementProposal,
        edited_values: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        """Execute targeting changes (device bid modifiers, etc.)."""
        results = []
        campaign_id = self._extract_campaign_id(proposal)
        if not campaign_id:
            raise ValueError("対象キャンペーンIDが特定できません")

        if edited_values:
            device_modifiers = edited_values.get("device_modifiers", {})
            for device_type, modifier in device_modifiers.items():
                result = self.writer.update_device_bid_modifier(
                    campaign_id=campaign_id,
                    device_type=device_type.upper(),
                    bid_modifier=float(modifier),
                )
                results.append(result)

        return results

    def _rollback_operation(self, operation: dict[str, Any]) -> dict[str, Any]:
        """Rollback a single operation using recorded previous values."""
        op_type = operation.get("operation", "")

        if op_type == "update_campaign_budget":
            prev_value = operation.get("previous_value")
            if prev_value is not None:
                return self.writer.update_campaign_budget(
                    campaign_id=operation["campaign_id"],
                    new_budget_micros=prev_value,
                )

        elif op_type == "update_target_cpa":
            prev_value = operation.get("previous_value")
            if prev_value is not None:
                return self.writer.update_campaign_target_cpa(
                    campaign_id=operation["campaign_id"],
                    target_cpa_micros=prev_value,
                )

        elif op_type == "update_target_roas":
            prev_value = operation.get("previous_value")
            if prev_value is not None:
                return self.writer.update_campaign_target_roas(
                    campaign_id=operation["campaign_id"],
                    target_roas=prev_value,
                )

        elif op_type == "add_negative_keywords":
            # Cannot easily undo negative keyword additions
            # Would need to remove by resource_name
            logger.warning(
                f"Rollback for negative keywords not fully automated: "
                f"{operation.get('resource_names', [])}"
            )
            return {
                "operation": "rollback_negative_keywords",
                "status": "manual_required",
                "note": "除外キーワードのロールバックは手動対応が必要です",
                "resource_names": operation.get("resource_names", []),
            }

        elif op_type == "create_responsive_search_ad":
            # Pause the newly created ad
            ad_group_id = operation.get("ad_group_id")
            ad_id = operation.get("ad_id")
            if ad_group_id and ad_id:
                return self.writer.pause_ad(
                    ad_group_id=str(ad_group_id),
                    ad_id=str(ad_id),
                )
            logger.warning(
                f"Cannot rollback RSA creation: missing ad_group_id or ad_id"
            )
            return {
                "operation": "rollback_create_rsa",
                "status": "manual_required",
                "note": "新規広告のロールバック（一時停止）は手動対応が必要です",
            }

        elif op_type == "pause_ad":
            # Re-enable the previously paused ad
            ad_group_id = operation.get("ad_group_id")
            ad_id = operation.get("ad_id")
            if ad_group_id and ad_id:
                return self.writer.enable_ad(
                    ad_group_id=str(ad_group_id),
                    ad_id=str(ad_id),
                )
            logger.warning(
                f"Cannot rollback ad pause: missing ad_group_id or ad_id"
            )
            return {
                "operation": "rollback_pause_ad",
                "status": "manual_required",
                "note": "広告の再有効化は手動対応が必要です",
            }

        return {
            "operation": f"rollback_{op_type}",
            "status": "completed",
        }

    @staticmethod
    def _extract_campaign_id(
        proposal: ImprovementProposal,
    ) -> str | None:
        """Extract campaign ID from proposal data."""
        # Try action_steps first
        for step in (proposal.action_steps or []):
            if isinstance(step, dict) and step.get("campaign_id"):
                return str(step["campaign_id"])

        # Try target_campaign (may contain the name, not ID)
        return None

    async def _save_before_snapshot(
        self,
        proposal: ImprovementProposal,
    ) -> None:
        """Save a before snapshot using the latest weekly report KPIs."""
        if not proposal.report:
            logger.warning(
                f"No report linked to proposal {proposal.id}, "
                "cannot save before snapshot"
            )
            return

        report = proposal.report
        kpi_snapshot = report.kpi_snapshot or {}

        # Build KPI data from report snapshot
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

        # Extract campaign_id if available
        campaign_id = self._extract_campaign_id(proposal)

        try:
            await self.impact_tracker.save_before_snapshot(
                proposal_id=proposal.id,
                kpi_data=kpi_data,
                period_start=report.week_start_date,
                period_end=report.week_end_date,
                campaign_id=campaign_id,
            )
            logger.info(f"Saved before snapshot for proposal {proposal.id}")
        except Exception as e:
            logger.error(f"Failed to save before snapshot: {e}")
