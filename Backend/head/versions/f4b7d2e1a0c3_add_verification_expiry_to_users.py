   
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4b7d2e1a0c3"
down_revision: Union[str, Sequence[str], None] = "e15a0fd92b71"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verification_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_email_verification_token", "users", ["email_verification_token"])


def downgrade() -> None:
    op.drop_index("ix_users_email_verification_token", table_name="users")
    op.drop_column("users", "email_verification_expires_at")
