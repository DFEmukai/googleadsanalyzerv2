import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1.router import router as v1_router
from app.db.session import engine
from app.services.scheduler import setup_scheduler, start_scheduler, stop_scheduler, get_next_run_time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: configure and start scheduler
    setup_scheduler(day_of_week="mon", hour=7, minute=0)
    start_scheduler()
    logger.info("Application started with scheduler")
    yield
    # Shutdown
    stop_scheduler()
    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Google Ads AI Agent",
    description="Google Ads analysis and improvement proposal system",
    version="0.2.0",
    lifespan=lifespan,
)

settings = get_settings()

# CORS: Allow configured frontend_url + Render domains + dev ports
cors_origins = list(dict.fromkeys(filter(None, [
    settings.frontend_url,
    "https://frontend-qja7.onrender.com",
    "https://googleads-frontend.onrender.com",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3003",
])))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/api/v1/health")
async def health_check():
    next_run = get_next_run_time()
    return {
        "status": "ok",
        "version": "0.2.0",
        "next_scheduled_analysis": next_run,
    }
