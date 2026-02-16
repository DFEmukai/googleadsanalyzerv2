from sqlalchemy import Column, String, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, UUIDMixin


class AuctionInsight(UUIDMixin, Base):
    __tablename__ = "auction_insights"

    report_id = Column(
        UUID(as_uuid=True), ForeignKey("weekly_reports.id"), nullable=False
    )
    competitor_domain = Column(String, nullable=False)
    impression_share = Column(Numeric(5, 4), nullable=True)
    overlap_rate = Column(Numeric(5, 4), nullable=True)
    position_above_rate = Column(Numeric(5, 4), nullable=True)
    top_of_page_rate = Column(Numeric(5, 4), nullable=True)
    outranking_share = Column(Numeric(5, 4), nullable=True)

    report = relationship("WeeklyReport", back_populates="auction_insights")
