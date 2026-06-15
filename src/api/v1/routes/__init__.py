from fastapi import APIRouter

from src.api.v1.routes.context import router as context_router
from src.api.v1.routes.health import router as health_router
from src.api.v1.routes.metadata import router as metadata_router
from src.api.v1.routes.reply import router as reply_router
from src.api.v1.routes.tick import router as tick_router

v1_router = APIRouter()

v1_router.include_router(health_router, tags=["health"])
v1_router.include_router(metadata_router, tags=["metadata"])
v1_router.include_router(context_router, tags=["context"])
v1_router.include_router(tick_router, tags=["tick"])
v1_router.include_router(reply_router, tags=["reply"])
