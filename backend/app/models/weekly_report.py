from sqlalchemy import Column, Date, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin, TimestampMixin


class WeeklyReport(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "weekly_reports"

    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)
    raw_data = Column(JSONB, nullable=True)
    analysis_summary = Column(Text, nullable=True)
    kpi_snapshot = Column(JSONB, nullable=True)

    proposals = relationship("ImprovementProposal", back_populates="report")
    auction_insights = relationship("AuctionInsight", back_populates="report")
