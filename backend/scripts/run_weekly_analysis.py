"""Manual trigger for weekly analysis.

Usage:
    cd backend
    python scripts/run_weekly_analysis.py
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import async_session
from app.services.report_generator import ReportGenerator


async def main():
    print("Starting weekly analysis...")
    async with async_session() as db:
        generator = ReportGenerator(db)
        result = await generator.generate_weekly_report()
        print(f"\nAnalysis complete!")
        print(f"Report ID: {result['report_id']}")
        print(f"Week: {result['week_start']} - {result['week_end']}")
        print(f"Proposals generated: {result['proposals_generated']}")
        print(f"\nSummary:\n{result['analysis_summary'][:500]}...")


if __name__ == "__main__":
    asyncio.run(main())
