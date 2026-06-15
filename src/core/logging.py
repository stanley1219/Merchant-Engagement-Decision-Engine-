import logging
import sys
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from src.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]

    if settings.is_production:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s",
            rename_fields={"level": "severity"},
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        
        structlog.configure(
            processors=shared_processors + [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=shared_processors + [
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy"]:
        logging.getLogger(logger_name).handlers = []
        logging.getLogger(logger_name).propagate = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


class LoggerMixin:
    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        return get_logger(self.__class__.__module__)