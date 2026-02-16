from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin


class ProposalExecution(UUIDMixin, Base):
    __tablename__ = "proposal_executions"

    proposal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("improvement_proposals.id"),
        nullable=False,
        unique=True,
    )
    executed_at = Column(DateTime, nullable=False)
    executed_by = Column(String, nullable=True)
    execution_notes = Column(Text, nullable=True)
    actual_changes = Column(JSONB, nullable=True)

    proposal = relationship("ImprovementProposal", back_populates="execution")
