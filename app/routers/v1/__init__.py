from fastapi import APIRouter

from app.routers.v1.auth import router as auth_router
from app.routers.v1.feedback import router as feedback_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(feedback_router)