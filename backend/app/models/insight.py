from sqlalchemy import Column, Text, Numeric, Boolean, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base, UUIDMixin, TimestampMixin
import enum


class InsightType(str, enum.Enum):
    EFFECTIVE_PATTERN = "effective_pattern"
    INEFFECTIVE_PATTERN = "ineffective_pattern"
    SEASONAL_TREND = "seasonal_trend"
    CAMPAIGN_CHARACTERISTIC = "campaign_characteristic"


class LearningInsight(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "learning_insights"

    insight_type = Column(
        SAEnum(
            InsightType,
            name="insight_type_enum",
            create_constraint=True,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
    )
    category = Column(Text, nullable=True)
    description = Column(Text, nullable=False)
    evidence = Column(JSONB, nullable=True)
    confidence = Column(Numeric(3, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
