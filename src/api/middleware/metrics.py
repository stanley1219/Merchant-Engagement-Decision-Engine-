import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Active HTTP requests",
    ["method", "endpoint"],
)

TICK_PROCESSING_TIME = Histogram(
    "tick_processing_duration_seconds",
    "Tick processing duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
)

MESSAGES_GENERATED = Counter(
    "messages_generated_total",
    "Total messages generated",
    ["category", "signal_type"],
)

SUPPRESSION_HITS = Counter(
    "suppression_hits_total",
    "Total suppression key hits",
    ["trigger_type"],
)

LLM_CALLS = Counter(
    "llm_calls_total",
    "Total LLM calls",
    ["model", "status"],
)

LLM_LATENCY = Histogram(
    "llm_call_duration_seconds",
    "LLM call latency in seconds",
    ["model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method
        path = request.url.path

        ACTIVE_REQUESTS.labels(method=method, endpoint=path).inc()
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            status = response.status_code
            return response
        except Exception:
            status = 500
            raise
        finally:
            process_time = time.perf_counter() - start_time
            REQUEST_COUNT.labels(method=method, endpoint=path, status=status).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=path).observe(process_time)
            ACTIVE_REQUESTS.labels(method=method, endpoint=path).dec()