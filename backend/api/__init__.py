"""
REST API endpoints
Provides polling-based endpoints for frontend
"""

from fastapi import APIRouter

from . import routes

router = APIRouter()

# Include all routes
router.include_router(routes.router, tags=["trading"])

__all__ = ["router"]
