"""Health check endpoints"""

from fastapi import APIRouter, HTTPException
from app.services.intelowl_service import intel_service
import logging

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)

@router.get("/")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "ThreatFlow Middleware"}

@router.get("/intelowl")
async def intelowl_health():
    """Check IntelOwl connectivity"""
    try:
        analyzers = await intel_service.get_available_analyzers()
        return {
            "status": "connected",
            "analyzers_available": len(analyzers)
        }
    except Exception as e:
        logger.error(f"IntelOwl health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"IntelOwl unreachable: {str(e)}")