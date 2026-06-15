from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.error_handling import register_exception_handlers
from src.api.middleware.logging import RequestLoggingMiddleware
from src.api.middleware.metrics import MetricsMiddleware
from src.api.v1.routes import v1_router
from src.core.config import get_settings
from src.core.logging import get_logger, setup_logging
from src.infrastructure.cache.redis_client import redis_client
from src.infrastructure.database.session import close_db, init_db

settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        "Starting Vera Message Engine",
        environment=settings.ENVIRONMENT,
        version="0.1.0",
    )
    await init_db()
    logger.info("Database initialized")
    await redis_client.connect()
    logger.info("Redis connected")
    yield
    await close_db()
    logger.info("Database connections closed")
    await redis_client.disconnect()
    logger.info("Redis disconnected")


app = FastAPI(
    title="Vera Message Engine",
    description="Deterministic message composition engine for merchant growth",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestLoggingMiddleware)

register_exception_handlers(app)

app.include_router(v1_router, prefix="/v1")
