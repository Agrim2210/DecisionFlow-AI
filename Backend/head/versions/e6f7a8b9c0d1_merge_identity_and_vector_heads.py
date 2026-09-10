   
from typing import Sequence, Union


revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, Sequence[str], None] = (
    "a1b2c3d4e5f6",
    "d4e5f6a7b8c9",
    "f4b7d2e1a0c3",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
