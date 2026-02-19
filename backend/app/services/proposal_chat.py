"""Proposal chat service for wall-bouncing discussions with Claude."""

import json
from typing import Any
from uuid import UUID

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models import ImprovementProposal, ProposalConversation, MessageRole


CHAT_SYSTEM_PROMPT = """あなたはGoogle広告運用のエキスパートアドバイザーです。
ユーザーがAIによって生成された改善提案について相談しています。

## あなたの役割
- 提案の妥当性について議論する
- 代替案を提示する
- リスクや懸念点を説明する
- 質問に対して具体的に回答する
- ユーザーが自信を持って判断できるようサポートする

## 回答のスタイル
- 日本語で回答してください
- 簡潔かつ具体的に回答してください
- データに基づいた根拠を示してください
- 必要に応じて複数の選択肢を提示してください

## 重要
- 提案を無条件に肯定するのではなく、客観的な視点でアドバイスしてください
- ユーザーの質問や懸念に対して誠実に回答してください
- 「この提案で本当にいいのか？」という問いに対しては、メリット・デメリットを整理して回答してください
"""


class ProposalChatService:
    """Service for chatting with Claude about proposals."""

    def __init__(self):
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def chat(
        self,
        db: AsyncSession,
        proposal_id: UUID,
        user_message: str,
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Send a message to Claude about a proposal and get a response.

        Returns:
            tuple: (reply, conversation_history)
        """
        # Load proposal with report data
        proposal = await self._load_proposal(db, proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        # Load existing conversation history
        history = await self._load_conversation_history(db, proposal_id)

        # Build context about the proposal
        proposal_context = self._build_proposal_context(proposal)

        # Build messages for Claude
        messages = self._build_messages(proposal_context, history, user_message)

        # Call Claude API
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=CHAT_SYSTEM_PROMPT,
            messages=messages,
        )

        reply = response.content[0].text

        # Save both user message and assistant reply to DB
        await self._save_message(db, proposal_id, MessageRole.user, user_message)
        await self._save_message(db, proposal_id, MessageRole.assistant, reply)
        await db.commit()

        # Return updated conversation history
        updated_history = await self._load_conversation_history(db, proposal_id)
        history_dicts = [
            {
                "role": msg.role.value,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in updated_history
        ]

        return reply, history_dicts

    async def get_conversation_history(
        self,
        db: AsyncSession,
        proposal_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get the conversation history for a proposal."""
        history = await self._load_conversation_history(db, proposal_id)
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in history
        ]

    async def _load_proposal(
        self, db: AsyncSession, proposal_id: UUID
    ) -> ImprovementProposal | None:
        """Load proposal with related report data."""
        result = await db.execute(
            select(ImprovementProposal)
            .options(selectinload(ImprovementProposal.report))
            .where(ImprovementProposal.id == proposal_id)
        )
        return result.scalar_one_or_none()

    async def _load_conversation_history(
        self, db: AsyncSession, proposal_id: UUID
    ) -> list[ProposalConversation]:
        """Load conversation history ordered by created_at."""
        result = await db.execute(
            select(ProposalConversation)
            .where(ProposalConversation.proposal_id == proposal_id)
            .order_by(ProposalConversation.created_at)
        )
        return list(result.scalars().all())

    async def _save_message(
        self,
        db: AsyncSession,
        proposal_id: UUID,
        role: MessageRole,
        content: str,
    ) -> ProposalConversation:
        """Save a message to the conversation history."""
        message = ProposalConversation(
            proposal_id=proposal_id,
            role=role,
            content=content,
        )
        db.add(message)
        return message

    def _build_proposal_context(self, proposal: ImprovementProposal) -> str:
        """Build context string about the proposal for Claude."""
        parts = [
            "## 議論対象の提案",
            f"**タイトル**: {proposal.title}",
            f"**カテゴリ**: {proposal.category.value}",
            f"**優先度**: {proposal.priority.value}",
            f"**ステータス**: {proposal.status.value}",
        ]

        if proposal.description:
            parts.append(f"**説明**: {proposal.description}")

        if proposal.expected_effect:
            parts.append(f"**期待効果**: {proposal.expected_effect}")

        if proposal.target_campaign:
            parts.append(f"**対象キャンペーン**: {proposal.target_campaign}")

        if proposal.target_ad_group:
            parts.append(f"**対象広告グループ**: {proposal.target_ad_group}")

        if proposal.action_steps:
            parts.append("**アクションステップ**:")
            parts.append(json.dumps(proposal.action_steps, ensure_ascii=False, indent=2))

        # Add report context if available
        if proposal.report:
            report = proposal.report
            parts.append("\n## 関連レポート情報")
            if report.analysis_summary:
                parts.append(f"**分析サマリー**: {report.analysis_summary}")
            if report.kpi_snapshot:
                parts.append("**KPIスナップショット**:")
                parts.append(json.dumps(report.kpi_snapshot, ensure_ascii=False, indent=2))

        return "\n".join(parts)

    def _build_messages(
        self,
        proposal_context: str,
        history: list[ProposalConversation],
        new_message: str,
    ) -> list[dict[str, str]]:
        """Build the messages array for Claude API."""
        messages = []

        # First message includes the proposal context
        if history:
            # Include context in the first user message reconstruction
            first_user_msg = f"{proposal_context}\n\n---\n\n{history[0].content}"
            messages.append({"role": "user", "content": first_user_msg})

            # Add remaining history
            for msg in history[1:]:
                messages.append({"role": msg.role.value, "content": msg.content})

            # Add new message
            messages.append({"role": "user", "content": new_message})
        else:
            # First message in conversation
            full_message = f"{proposal_context}\n\n---\n\nユーザーの質問:\n{new_message}"
            messages.append({"role": "user", "content": full_message})

        return messages
