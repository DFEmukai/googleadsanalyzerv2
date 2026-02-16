from sqlalchemy import Column, String, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TimestampMixin
import enum


class ProposalCategory(str, enum.Enum):
    KEYWORD = "keyword"
    AD_COPY = "ad_copy"              # kept for backward compatibility
    CREATIVE = "creative"             # ad copy text (auto-executable)
    TARGETING = "targeting"
    BUDGET = "budget"
    BIDDING = "bidding"
    COMPETITIVE_RESPONSE = "competitive_response"
    MANUAL_CREATIVE = "manual_creative"  # image/video assets (Chatwork task)


class Priority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProposalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    SKIPPED = "skipped"


class ImprovementProposal(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "improvement_proposals"

    report_id = Column(
        UUID(as_uuid=True), ForeignKey("weekly_reports.id"), nullable=False
    )
    category = Column(
        SAEnum(
            ProposalCategory,
            name="proposal_category_enum",
            create_constraint=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    priority = Column(
        SAEnum(
            Priority,
            name="priority_enum",
            create_constraint=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    expected_effect = Column(Text, nullable=True)
    action_steps = Column(JSONB, nullable=True)
    target_campaign = Column(String, nullable=True)
    target_ad_group = Column(String, nullable=True)
    status = Column(
        SAEnum(
            ProposalStatus,
            name="proposal_status_enum",
            create_constraint=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=ProposalStatus.PENDING,
    )

    report = relationship("WeeklyReport", back_populates="proposals")
    execution = relationship(
        "ProposalExecution", back_populates="proposal", uselist=False
    )
    result = relationship("ProposalResult", back_populates="proposal", uselist=False)
