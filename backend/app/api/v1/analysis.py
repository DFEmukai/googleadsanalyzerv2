from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.report_generator import ReportGenerator

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run")
async def run_analysis(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger the weekly analysis pipeline.

    If start_date and end_date are not provided, analyzes the previous week.
    """
    generator = ReportGenerator(db)
    result = await generator.generate_weekly_report(start_date, end_date)
    return result
