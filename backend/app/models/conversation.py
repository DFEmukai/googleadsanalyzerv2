"""Proposal conversation model for chat history."""

from enum import Enum as PyEnum
from sqlalchemy import Column, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class MessageRole(str, PyEnum):
    user = "user"
    assistant = "assistant"


class ProposalConversation(UUIDMixin, TimestampMixin, Base):
    """Stores chat messages between user and Claude about proposals."""

    __tablename__ = "proposal_conversations"

    proposal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("improvement_proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(
        Enum(MessageRole, name="message_role"),
        nullable=False,
    )
    content = Column(Text, nullable=False)

    # Relationship
    proposal = relationship("ImprovementProposal", back_populates="conversations")
