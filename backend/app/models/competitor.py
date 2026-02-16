from sqlalchemy import Column, String, Text, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class Competitor(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "competitors"

    domain = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class CompetitorSnapshot(UUIDMixin, Base):
    __tablename__ = "competitor_snapshots"

    competitor_id = Column(
        UUID(as_uuid=True), ForeignKey("competitors.id"), nullable=False
    )
    captured_at = Column(DateTime, nullable=False)
    ad_copies = Column(JSONB, nullable=True)
    keywords = Column(JSONB, nullable=True)
    estimated_spend = Column(Numeric(12, 2), nullable=True)
    source = Column(Text, nullable=True)

    competitor = relationship("Competitor")
