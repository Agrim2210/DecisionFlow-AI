   
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9f0a1b2d3e4"
down_revision: Union[str, Sequence[str], None] = "e15a0fd92b71"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("pending_users", "org_name", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("pending_users", "org_slug", existing_type=sa.String(length=100), nullable=True)
    op.add_column("pending_users", sa.Column("invited_org_id", sa.UUID(), nullable=True))
    op.add_column("pending_users", sa.Column("invited_role", sa.String(length=50), nullable=True))
    op.add_column("pending_users", sa.Column("invited_by_user_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_pending_users_invited_org_id", "pending_users", "organizations",
        ["invited_org_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_pending_users_invited_by_user_id", "pending_users", "users",
        ["invited_by_user_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_pending_users_invited_org_id", "pending_users", ["invited_org_id"])


def downgrade() -> None:
    op.drop_index("ix_pending_users_invited_org_id", table_name="pending_users")
    op.drop_constraint("fk_pending_users_invited_by_user_id", "pending_users", type_="foreignkey")
    op.drop_constraint("fk_pending_users_invited_org_id", "pending_users", type_="foreignkey")
    op.drop_column("pending_users", "invited_by_user_id")
    op.drop_column("pending_users", "invited_role")
    op.drop_column("pending_users", "invited_org_id")
    op.alter_column("pending_users", "org_slug", existing_type=sa.String(length=100), nullable=False)
    op.alter_column("pending_users", "org_name", existing_type=sa.String(length=255), nullable=False)
