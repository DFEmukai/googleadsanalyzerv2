from fastapi import APIRouter

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.reports import router as reports_router
from app.api.v1.proposals import router as proposals_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.chatwork import router as chatwork_router

router = APIRouter(prefix="/api/v1")

router.include_router(dashboard_router)
router.include_router(campaigns_router)
router.include_router(reports_router)
router.include_router(proposals_router)
router.include_router(analysis_router)
router.include_router(chatwork_router)
