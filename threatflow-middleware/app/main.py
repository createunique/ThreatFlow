"""ThreatFlow Middleware FastAPI Application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import health, execute
import logging

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Middleware API for ThreatFlow - IntelOwl Orchestration Layer",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(execute.router)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"IntelOwl URL: {settings.INTELOWL_URL}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down ThreatFlow Middleware")