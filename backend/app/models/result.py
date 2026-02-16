from sqlalchemy import Column, String, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin


class ProposalResult(UUIDMixin, Base):
    __tablename__ = "proposal_results"

    proposal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("improvement_proposals.id"),
        nullable=False,
        unique=True,
    )
    measured_at = Column(DateTime, nullable=False)
    measurement_period = Column(String, nullable=True)
    before_metrics = Column(JSONB, nullable=True)
    after_metrics = Column(JSONB, nullable=True)
    effect_summary = Column(Text, nullable=True)
    effect_percentage = Column(Numeric(10, 2), nullable=True)
    ai_evaluation = Column(Text, nullable=True)

    proposal = relationship("ImprovementProposal", back_populates="result")
