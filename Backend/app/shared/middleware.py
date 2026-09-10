
from __future__ import annotations

import time
import uuid
from collections.abc import Callable

import jwt
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.shared.config import settings

logger = structlog.get_logger(__name__)

                                           
_PUBLIC_PATHS = frozenset({
    "/",
    "/health",
    "/readyz",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/identity/auth/register",
    "/api/v1/identity/auth/login",
    "/api/v1/identity/auth/refresh",
})

                                                             
_SILENT_PATHS = frozenset({"/health", "/readyz", "/metrics"})


class CorrelationIDMiddleware(BaseHTTPMiddleware):
       

    HEADER = "X-Correlation-ID"

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get(self.HEADER) or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

                                                                             
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        response = await call_next(request)
        response.headers[self.HEADER] = correlation_id
        return response


class TenantContextMiddleware(BaseHTTPMiddleware):
       

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.org_id = None
        request.state.user_id = None
        request.state.role = None
        request.state.plan = None

        if request.url.path not in _PUBLIC_PATHS:
            token = self._extract_token(request)
            if token:
                try:
                                                                               
                    payload = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=[settings.JWT_ALGORITHM],
                        options={"verify_exp": False},
                    )
                    request.state.org_id = payload.get("org_id")
                    request.state.user_id = payload.get("sub")
                    request.state.role = payload.get("role")
                    request.state.plan = payload.get("plan")

                    structlog.contextvars.bind_contextvars(
                        org_id=request.state.org_id,
                        user_id=request.state.user_id,
                        role=request.state.role,
                    )
                except jwt.PyJWTError:
                    pass                                          

        return await call_next(request)

    @staticmethod
    def _extract_token(request: Request) -> str | None:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            return auth[7:].strip() or None
        return None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
       

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in _SILENT_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        log_data = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query) if request.url.query else None,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "org_id": getattr(request.state, "org_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "ip": request.client.host if request.client else None,
        }

        if response.status_code >= 500:
            logger.error("http_request", **log_data)
        elif response.status_code >= 400:
            logger.warning("http_request", **log_data)
        else:
            logger.info("http_request", **log_data)

        return response