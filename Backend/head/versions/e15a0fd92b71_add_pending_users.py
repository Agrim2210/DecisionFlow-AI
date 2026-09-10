   
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e15a0fd92b71"
down_revision: Union[str, Sequence[str], None] = "db808409948b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("org_name", sa.String(length=255), nullable=False),
        sa.Column("org_slug", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("verification_token_hash", sa.String(length=64), nullable=False),
        sa.Column("verification_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_pending_users_email"),
        sa.UniqueConstraint("org_slug", name="uq_pending_users_org_slug"),
        sa.UniqueConstraint("verification_token_hash", name="uq_pending_users_verification_token_hash"),
    )
    op.create_index("ix_pending_users_email", "pending_users", ["email"])
    op.create_index("ix_pending_users_org_slug", "pending_users", ["org_slug"])
    op.create_index("ix_pending_users_verification_token_hash", "pending_users", ["verification_token_hash"])
    op.create_index("ix_pending_users_verification_expires_at", "pending_users", ["verification_expires_at"])


def downgrade() -> None:
    op.drop_index("ix_pending_users_verification_expires_at", table_name="pending_users")
    op.drop_index("ix_pending_users_verification_token_hash", table_name="pending_users")
    op.drop_index("ix_pending_users_org_slug", table_name="pending_users")
    op.drop_index("ix_pending_users_email", table_name="pending_users")
    op.drop_table("pending_users")
