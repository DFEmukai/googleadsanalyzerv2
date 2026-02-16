from sqlalchemy import Column, String, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, UUIDMixin, TimestampMixin
import enum


class CampaignType(str, enum.Enum):
    SEARCH = "search"
    DISPLAY = "display"
    PMAX = "pmax"
    VIDEO = "video"


class CampaignStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class Campaign(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"

    campaign_id = Column(String, nullable=False, unique=True, index=True)
    campaign_name = Column(String, nullable=False)
    campaign_type = Column(
        SAEnum(
            CampaignType,
            name="campaign_type_enum",
            create_constraint=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    status = Column(
        SAEnum(
            CampaignStatus,
            name="campaign_status_enum",
            create_constraint=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=CampaignStatus.ACTIVE,
    )
    first_seen_at = Column(DateTime, nullable=False)
    last_seen_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
