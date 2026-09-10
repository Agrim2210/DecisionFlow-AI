   
from typing import Sequence, Union

from alembic import op


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c9f0a1b2d3e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_chunks_embedding_hnsw "
        "ON memory_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_chunks_org_source "
        "ON memory_chunks (org_id, source_type)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_memory_chunks_org_source")
    op.execute("DROP INDEX IF EXISTS ix_memory_chunks_embedding_hnsw")
