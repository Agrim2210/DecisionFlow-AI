   
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from app.shared.database import Base


class TaskDependencyORM(Base):
    __tablename__ = "task_dependencies"
    __table_args__ = (
                                                                       
        UniqueConstraint("upstream_id", "downstream_id", name="uq_task_dependency_edge"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    upstream_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("action_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    downstream_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("action_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dependency_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="finish_to_start"
    )
    detected_by: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="ai"
    )
    confidence_score: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False, server_default="1.0"
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    def __repr__(self) -> str:
        return (
            f"<TaskDependencyORM "
            f"upstream={self.upstream_id} → downstream={self.downstream_id} "
            f"type={self.dependency_type}>"
        )
