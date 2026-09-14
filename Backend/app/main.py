   
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.shared.config import settings
from app.shared.exceptions import AppError
from app.shared.middleware import (
    CorrelationIDMiddleware,
    RequestLoggingMiddleware,
    TenantContextMiddleware,
)

logger = structlog.get_logger(__name__)


                                                                    
@asynccontextmanager
async def lifespan(app: FastAPI):
       
                                                                    
    logger.info(
        "app_starting",
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        env=settings.APP_ENV,
        debug=settings.DEBUG,
    )

                                                    
    if not settings.is_development or True:                
        try:
            from app.shared.database import engine
            import sqlalchemy
            async with engine.connect() as conn:
                await conn.execute(sqlalchemy.text("SELECT 1"))
            logger.info("db_connection_ok")
        except Exception as exc:
            logger.error("db_connection_failed", error=str(exc))
            raise

    yield                  

                                                                    
    from app.shared.database import dispose_engine
    await dispose_engine()
    logger.info("app_shutdown_complete")


                                                                    
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "**DecisionFlow AI** — Decision Operating System for Modern Organizations.\n\n"
            "Transforms meeting transcripts into tracked, owned, and escalated workflows.\n\n"
            "## Authentication\n"
            "Use `POST /api/v1/identity/auth/login` to get a Bearer token.\n"
            "Pass it as `Authorization: Bearer <token>` on all protected endpoints.\n\n"
            "## Panels\n"
            "- **Admin panel**: routes under `/api/v1/identity/users`, "
            "`/api/v1/meetings` (all-org view)\n"
            "- **Worker panel**: routes ending in `/mine` or `/me/*`\n"
        ),
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

                                                                     
                               
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_origin_regex=settings.CORS_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Correlation-ID", "Accept", "Origin"],
        expose_headers=["X-Correlation-ID"],
    )
                                                             
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIDMiddleware)                           

                                                                    
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
           
        correlation_id = getattr(request.state, "correlation_id", None)

        if exc.status_code >= 500:
            logger.error(
                "app_error_500",
                code=exc.error_code,
                message=exc.message,
                path=str(request.url),
                correlation_id=correlation_id,
            )
        elif exc.status_code >= 400:
            logger.warning(
                "app_error_4xx",
                code=exc.error_code,
                status=exc.status_code,
                path=str(request.url),
            )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                },
                "data": None,
            },
            headers={"X-Correlation-ID": correlation_id} if correlation_id else {},
        )

    @app.exception_handler(Exception)
    async def handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
                                                                     
        logger.exception(
            "unhandled_exception",
            path=str(request.url),
            exc_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again.",
                },
                "data": None,
            },
        )

                                                                    
    _register_routers(app)

                                                                    
    @app.get("/health", tags=["System"], include_in_schema=True)
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
            "smtp_configured": settings.smtp_configured,
            "smtp_host": settings.SMTP_HOST or "(not set)",
            "api_public_url": settings.API_PUBLIC_URL,
            "frontend_url": settings.FRONTEND_URL,
        }

    @app.get("/", tags=["System"], include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": settings.APP_NAME,
            "docs": "/docs",
            "health": "/health",
        }

    return app


def _register_routers(app: FastAPI) -> None:
       
    V1 = "/api/v1"

                                                                    
    from app.domains.identity.api.auth_router import router as auth_router
    from app.domains.identity.api.users_router import router as users_router
    from app.domains.identity.api.orgs_router import router as orgs_router

    app.include_router(auth_router,  prefix=f"{V1}/identity")
    app.include_router(users_router, prefix=f"{V1}/identity")
    app.include_router(orgs_router,  prefix=f"{V1}/identity")

                                                                    
    from app.domains.meetings.api.meetings_router import router as meetings_router

    app.include_router(meetings_router, prefix=f"{V1}")

    from app.domains.extraction.api.decisions_router import router as decisions_router
    from app.domains.extraction.api.tasks_router import router as tasks_router
    from app.domains.extraction.api.risks_router import router as risks_router
    from app.domains.extraction.api.questions_router import router as questions_router
    from app.domains.graph.api.graph_router import router as graph_router
    from app.domains.notifications.api.notifications_router import router as notif_router
    from app.domains.notifications.api.policies_router import router as policies_router
    from app.domains.notifications.api.escalations_router import router as escalations_router
    from app.domains.search.api.search_router import router as search_router
    from app.domains.analytics.api.admin_router import router as analytics_admin_router
    from app.domains.analytics.api.worker_router import router as analytics_worker_router
    from app.domains.audit.api.audit_router import router as audit_router

    app.include_router(decisions_router, prefix=V1)
    app.include_router(tasks_router, prefix=V1)
    app.include_router(risks_router, prefix=V1)
    app.include_router(questions_router, prefix=V1)
    app.include_router(graph_router, prefix=V1)
    app.include_router(notif_router, prefix=V1)
    app.include_router(policies_router, prefix=V1)
    app.include_router(escalations_router, prefix=V1)
    app.include_router(search_router, prefix=V1)
    app.include_router(analytics_admin_router, prefix=V1)
    app.include_router(analytics_worker_router, prefix=V1)
    app.include_router(audit_router, prefix=V1)

    logger.info("routers_registered", router_count=len(app.routes))


                                                                    
app = create_app()
