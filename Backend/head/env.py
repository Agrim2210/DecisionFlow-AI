from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from app.shared.database import Base
from alembic import context
from app.domains.identity.infra.orm_models import OrganizationORM,UserORM,RefreshTokenORM
from app.domains.meetings.infra.orm_models import MeetingORM,TranscriptORM
from app.domains.extraction.infra.orm_models import DecisionORM,RiskORM,ActionItemORM,OpenQuestionORM,MemoryChunkORM
from app.domains.analytics.infra.orm_models import MeetingAnalyticsORM, UserReliabilitySnapshotORM
from app.domains.audit.infra.orm_models import AuditLogORM
from app.domains.graph.infra.orm_models import TaskDependencyORM
from app.domains.notifications.infra.orm_models import EscalationORM, EscalationPolicyORM, NotificationORM

                                                   
                                                   
config = context.config

                                               
                                      
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

                                       
                            
                           
                                         
target_metadata = Base.metadata

                                                               
                  
                                                                     
          


from app.shared.config import settings


def run_migrations_offline() -> None:
    url = settings.sync_database_url or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    if settings.sync_database_url:
        configuration["sqlalchemy.url"] = settings.sync_database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
