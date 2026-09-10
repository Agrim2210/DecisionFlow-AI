   
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from app.shared.database import Base


class UserReliabilitySnapshotORM(Base):
    __tablename__ = "user_reliability_snapshots"
    __table_args__ = (
                                                                         
        UniqueConstraint(
            "user_id",
            "org_id",
            name="uq_reliability_user_org_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

                       
    tasks_assigned: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    tasks_completed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    tasks_on_time: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    tasks_overdue: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    tasks_cancelled: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

                    
    reliability_score: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="100.0"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserReliabilitySnapshotORM "
            f"user_id={self.user_id} "
            f"score={self.reliability_score} "
            f"date={self.snapshot_date}>"
        )


class MeetingAnalyticsORM(Base):
    __tablename__ = "meeting_analytics"
    __table_args__ = (
                                          
        UniqueConstraint("meeting_id", name="uq_meeting_analytics_meeting"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

                                                     
    decisions_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    action_items_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    unassigned_tasks: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    risks_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    critical_risks: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    dependencies_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    open_questions_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

                                         
    execution_rate: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.0"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    def __repr__(self) -> str:
        return (
            f"<MeetingAnalyticsORM "
            f"meeting_id={self.meeting_id} "
            f"tasks={self.action_items_count} "
            f"exec_rate={self.execution_rate}>"
        )
