   
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sqlalchemy
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.shared.config import settings


                                                                    
class Base(DeclarativeBase):
       
    pass


_orm_models_loaded = False


def load_orm_models() -> None:
       
    global _orm_models_loaded
    if _orm_models_loaded:
        return

                                                                            
                                                                             
    from app.domains.analytics.infra import orm_models as analytics_models
    from app.domains.audit.infra import orm_models as audit_models
    from app.domains.extraction.infra import orm_models as extraction_models
    from app.domains.graph.infra import orm_models as graph_models
    from app.domains.identity.infra import orm_models as identity_models
    from app.domains.meetings.infra import orm_models as meetings_models
    from app.domains.notifications.infra import orm_models as notification_models

                                                                        
    _ = (
        analytics_models, audit_models, extraction_models, graph_models,
        identity_models, meetings_models, notification_models,
    )
    _orm_models_loaded = True


                                                                    
def _build_engine(test_mode: bool = False) -> AsyncEngine:
    kwargs: dict = {
        "echo": settings.DEBUG and settings.is_development,
        "future": True,
    }
    if test_mode:
                                                                           
        kwargs["poolclass"] = NullPool
    else:
        kwargs.update({
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
            "pool_recycle": settings.DATABASE_POOL_RECYCLE,
            "pool_pre_ping": True,
        })
    return create_async_engine(settings.async_database_url, **kwargs)


                                                  
engine: AsyncEngine = _build_engine()

                                                                            
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


                                                                    
async def get_db() -> AsyncGenerator[AsyncSession, None]:
       
    load_orm_models()
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


                                                                    
async def set_tenant_context(session: AsyncSession, org_id: uuid.UUID) -> None:
       
    await session.execute(
        sqlalchemy.text("SELECT set_config('app.org_id', :org_id, true)"),
        {"org_id": str(org_id)},
    )


                                                                   
@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
       
    load_orm_models()
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_engine() -> None:
                                                         
    await engine.dispose()
