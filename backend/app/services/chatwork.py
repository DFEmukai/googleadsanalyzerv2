"""Chatwork API integration service.

Sends weekly report notifications and creates tasks for
high-priority improvement proposals.
"""

import httpx
from datetime import date, datetime, timedelta
from typing import Any

from app.config import get_settings


class ChatworkService:
    BASE_URL = "https://api.chatwork.com/v2"

    def __init__(self):
        settings = get_settings()
        self.api_token = settings.chatwork_api_token
        self.room_id = settings.chatwork_room_id
        self.assignee_id = settings.chatwork_assignee_id
        self.mention_id = settings.chatwork_mention_id
        self.dashboard_url = settings.dashboard_url

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-ChatWorkToken": self.api_token}

    def is_configured(self) -> bool:
        """Check if Chatwork API is properly configured."""
        return bool(self.api_token and self.room_id)

    async def send_message(self, message: str) -> dict[str, Any] | None:
        """Send a message to the configured Chatwork room."""
        if not self.is_configured():
            return None

        url = f"{self.BASE_URL}/rooms/{self.room_id}/messages"
        payload = {"body": message, "self_unread": 0}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=self._headers, data=payload
            )
            response.raise_for_status()
            return response.json()

    async def create_task(
        self,
        title: str,
        assignee_ids: list[str] | None = None,
        limit_date: date | None = None,
        limit_type: str = "date",
    ) -> dict[str, Any] | None:
        """Create a task in the configured Chatwork room.

        Args:
            title: Task title/body
            assignee_ids: List of account IDs to assign. Defaults to configured assignee.
            limit_date: Task deadline date. Defaults to today.
            limit_type: 'none', 'date', or 'time'
        """
        if not self.is_configured():
            return None

        if assignee_ids is None:
            if not self.assignee_id:
                return None
            assignee_ids = [self.assignee_id]

        if limit_date is None:
            limit_date = date.today()

        url = f"{self.BASE_URL}/rooms/{self.room_id}/tasks"
        # Chatwork API expects unix timestamp for limit
        limit_timestamp = int(
            datetime.combine(limit_date, datetime.max.time()).timestamp()
        )
        payload = {
            "body": title,
            "to_ids": ",".join(assignee_ids),
            "limit": limit_timestamp,
            "limit_type": limit_type,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, headers=self._headers, data=payload
            )
            response.raise_for_status()
            return response.json()

    def build_weekly_report_message(
        self,
        report_id: str,
        week_start: date,
        week_end: date,
        kpi_snapshot: dict[str, Any],
        previous_kpi: dict[str, Any] | None,
        high_priority_proposals: list[dict[str, Any]],
        manual_creative_proposals: list[dict[str, Any]] | None = None,
    ) -> str:
        """Build the weekly report notification message for Chatwork."""
        # Mention
        mention = ""
        if self.mention_id:
            mention = f"[To:{self.mention_id}]\n\n"

        # Header
        start_str = week_start.strftime("%Y/%m/%d")
        end_str = week_end.strftime("%Y/%m/%d")
        header = (
            f"{mention}"
            f"[hr]\n"
            f"[info][title]週次Google広告レポート[/title]"
            f"期間：{start_str}〜{end_str}[/info]\n"
        )

        # KPI highlights
        cost = kpi_snapshot.get("total_cost", 0)
        conversions = kpi_snapshot.get("total_conversions", 0)
        cpa = kpi_snapshot.get("cpa", 0)
        ctr = kpi_snapshot.get("ctr", 0)
        roas = kpi_snapshot.get("roas", 0)

        kpi_section = "[info][title]今週のハイライト[/title]"
        kpi_section += f"・費用：¥{cost:,.0f}"
        if previous_kpi and previous_kpi.get("total_cost"):
            cost_change = self._calc_change_pct(cost, previous_kpi["total_cost"])
            kpi_section += f"（前週比 {self._format_change(cost_change)}）"
        kpi_section += "\n"

        kpi_section += f"・CV数：{conversions:.1f}件"
        if previous_kpi and previous_kpi.get("total_conversions"):
            conv_change = self._calc_change_pct(
                conversions, previous_kpi["total_conversions"]
            )
            kpi_section += f"（前週比 {self._format_change(conv_change)}）"
        kpi_section += "\n"

        kpi_section += f"・CPA：¥{cpa:,.0f}"
        if previous_kpi and previous_kpi.get("cpa"):
            cpa_change = self._calc_change_pct(cpa, previous_kpi["cpa"])
            kpi_section += f"（前週比 {self._format_change(cpa_change)}）"
        kpi_section += "\n"

        kpi_section += f"・CTR：{ctr:.2f}%"
        if previous_kpi and previous_kpi.get("ctr"):
            ctr_change = self._calc_change_pct(ctr, previous_kpi["ctr"])
            kpi_section += f"（前週比 {self._format_change(ctr_change)}）"
        kpi_section += "\n"

        kpi_section += f"・ROAS：{roas:.2f}"
        if previous_kpi and previous_kpi.get("roas"):
            roas_change = self._calc_change_pct(roas, previous_kpi["roas"])
            kpi_section += f"（前週比 {self._format_change(roas_change)}）"
        kpi_section += "[/info]\n"

        # High priority proposals
        proposal_section = ""
        if high_priority_proposals:
            proposal_section = "[info][title]緊急度：高の改善提案[/title]"
            for i, proposal in enumerate(high_priority_proposals, 1):
                title = proposal.get("title", "")
                target = proposal.get("target_campaign", "")
                target_str = f"（{target}）" if target else ""
                proposal_section += f"{i}. {title}{target_str}\n"
            proposal_section += "[/info]\n"

        # Task notification for manual_creative proposals
        task_section = ""
        mc_proposals = manual_creative_proposals or []
        if mc_proposals:
            task_section = (
                "[info][title]Chatworkタスク登録[/title]"
                f"画像・動画クリエイティブ改善提案 {len(mc_proposals)}件 をタスク登録しました。\n"
                "手動での対応をお願いします。[/info]\n"
            )

        # Dashboard notification for other proposals
        dashboard_section = ""
        if high_priority_proposals:
            dashboard_section = (
                "[info][title]ダッシュボード確認[/title]"
                "上記の改善提案はダッシュボードで承認・却下を行ってください。[/info]\n"
            )

        # Dashboard link
        report_url = f"{self.dashboard_url}/reports/{report_id}"
        footer = f"詳細レポート：{report_url}\n"

        return header + kpi_section + proposal_section + task_section + dashboard_section + footer

    async def send_weekly_report(
        self,
        report_id: str,
        week_start: date,
        week_end: date,
        kpi_snapshot: dict[str, Any],
        previous_kpi: dict[str, Any] | None,
        high_priority_proposals: list[dict[str, Any]],
        manual_creative_proposals: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send weekly report and create tasks for manual_creative proposals.

        Only manual_creative proposals get Chatwork tasks.
        Other proposals are managed via the dashboard.

        Returns a summary of what was sent.
        """
        results: dict[str, Any] = {
            "message_sent": False,
            "tasks_created": 0,
            "errors": [],
        }

        if not self.is_configured():
            results["errors"].append("Chatwork APIが設定されていません")
            return results

        # Send the report message
        try:
            message = self.build_weekly_report_message(
                report_id=report_id,
                week_start=week_start,
                week_end=week_end,
                kpi_snapshot=kpi_snapshot,
                previous_kpi=previous_kpi,
                high_priority_proposals=high_priority_proposals,
                manual_creative_proposals=manual_creative_proposals,
            )
            await self.send_message(message)
            results["message_sent"] = True
        except Exception as e:
            results["errors"].append(f"メッセージ送信エラー: {str(e)}")

        # Create tasks only for manual_creative proposals (image/video)
        for proposal in (manual_creative_proposals or []):
            try:
                task_title = (
                    f"【Google広告・クリエイティブ】{proposal.get('title', '')}"
                )
                target = proposal.get("target_campaign", "")
                if target:
                    task_title += f"\n対象：{target}"

                description = proposal.get("description", "")
                if description:
                    task_title += f"\n内容：{description}"

                expected_effect = proposal.get("expected_effect", "")
                if expected_effect:
                    task_title += f"\n期待効果：{expected_effect}"

                # Set deadline to 7 days from now
                deadline = date.today() + timedelta(days=7)
                await self.create_task(title=task_title, limit_date=deadline)
                results["tasks_created"] += 1
            except Exception as e:
                results["errors"].append(
                    f"タスク作成エラー ({proposal.get('title', '')}): {str(e)}"
                )

        return results

    async def send_execution_result(
        self,
        proposal_title: str,
        success: bool,
        details: str = "",
    ) -> dict[str, Any] | None:
        """Send notification about proposal execution result."""
        if not self.is_configured():
            return None

        status_emoji = "(OK)" if success else "(devil)"
        status_text = "成功" if success else "失敗"

        message = (
            f"[info][title]Google広告 変更反映{status_text}[/title]"
            f"提案：{proposal_title}\n"
            f"ステータス：{status_emoji} {status_text}\n"
        )
        if details:
            message += f"詳細：{details}\n"
        message += "[/info]"

        try:
            return await self.send_message(message)
        except Exception:
            return None

    async def send_rollback_notification(
        self,
        proposal_title: str,
        reason: str = "",
    ) -> dict[str, Any] | None:
        """Send notification about a rollback action."""
        if not self.is_configured():
            return None

        message = (
            f"[info][title]Google広告 変更ロールバック実行[/title]"
            f"提案：{proposal_title}\n"
        )
        if reason:
            message += f"理由：{reason}\n"
        message += "変更前の状態に戻しました。[/info]"

        try:
            return await self.send_message(message)
        except Exception:
            return None

    @staticmethod
    def _calc_change_pct(current: float, previous: float) -> float:
        if previous == 0:
            return 0
        return ((current - previous) / previous) * 100

    @staticmethod
    def _format_change(pct: float) -> str:
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:.1f}%"
