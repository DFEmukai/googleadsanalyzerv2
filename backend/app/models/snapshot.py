"""Proposal snapshot model for impact tracking."""

from enum import Enum as PyEnum
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class SnapshotType(str, PyEnum):
    before = "before"
    after = "after"


class ProposalSnapshot(UUIDMixin, TimestampMixin, Base):
    """Stores KPI snapshots for impact measurement."""

    __tablename__ = "proposal_snapshots"

    proposal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("improvement_proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_type = Column(
        Enum(SnapshotType, name="snapshot_type_enum"),
        nullable=False,
    )
    campaign_id = Column(String, nullable=True)  # Target campaign ID if applicable

    # KPI metrics
    cost = Column(Numeric(12, 2), nullable=True)
    conversions = Column(Numeric(10, 2), nullable=True)
    cpa = Column(Numeric(10, 2), nullable=True)
    ctr = Column(Numeric(8, 4), nullable=True)  # Stored as decimal (e.g., 0.0523)
    roas = Column(Numeric(10, 2), nullable=True)
    impressions = Column(Numeric(12, 0), nullable=True)
    clicks = Column(Numeric(12, 0), nullable=True)
    conversion_value = Column(Numeric(12, 2), nullable=True)

    # Period info
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Relationship
    proposal = relationship("ImprovementProposal", back_populates="snapshots")
