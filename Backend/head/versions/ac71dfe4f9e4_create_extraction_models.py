   
import pgvector.sqlalchemy 
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

                                        
revision: str = 'ac71dfe4f9e4'
down_revision: Union[str, Sequence[str], None] = 'fd9a7afa108b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
                         
                                                                 
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table('decisions',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('meeting_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('decision_type', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
    sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), server_default='1.0', nullable=False),
    sa.Column('ai_raw_output', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('made_by', postgresql.ARRAY(sa.UUID()), server_default='{}', nullable=False),
    sa.Column('effective_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=1536), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_decisions_meeting_id'), 'decisions', ['meeting_id'], unique=False)
    op.create_index(op.f('ix_decisions_org_id'), 'decisions', ['org_id'], unique=False)
    op.create_table('memory_chunks',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('meeting_id', sa.UUID(), nullable=False),
    sa.Column('source_type', sa.String(length=50), nullable=False),
    sa.Column('source_id', sa.UUID(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=1536), nullable=False),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memory_chunks_meeting_id'), 'memory_chunks', ['meeting_id'], unique=False)
    op.create_index(op.f('ix_memory_chunks_org_id'), 'memory_chunks', ['org_id'], unique=False)
    op.create_table('open_questions',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('meeting_id', sa.UUID(), nullable=False),
    sa.Column('question', sa.Text(), nullable=False),
    sa.Column('context', sa.Text(), server_default='', nullable=False),
    sa.Column('status', sa.String(length=50), server_default='open', nullable=False),
    sa.Column('answer', sa.Text(), nullable=True),
    sa.Column('answered_by', sa.UUID(), nullable=True),
    sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['answered_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_open_questions_meeting_id'), 'open_questions', ['meeting_id'], unique=False)
    op.create_index(op.f('ix_open_questions_org_id'), 'open_questions', ['org_id'], unique=False)
    op.create_table('risks',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('meeting_id', sa.UUID(), nullable=False),
    sa.Column('related_item_id', sa.UUID(), nullable=False),
    sa.Column('related_item_type', sa.String(length=50), nullable=False),
    sa.Column('risk_type', sa.String(length=100), nullable=False),
    sa.Column('severity', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('recommendation', sa.Text(), server_default='', nullable=False),
    sa.Column('status', sa.String(length=50), server_default='open', nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risks_meeting_id'), 'risks', ['meeting_id'], unique=False)
    op.create_index(op.f('ix_risks_org_id'), 'risks', ['org_id'], unique=False)
    op.create_index(op.f('ix_risks_severity'), 'risks', ['severity'], unique=False)
    op.create_table('action_items',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('meeting_id', sa.UUID(), nullable=False),
    sa.Column('decision_id', sa.UUID(), nullable=True),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), server_default='', nullable=False),
    sa.Column('owner_id', sa.UUID(), nullable=True),
    sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
    sa.Column('priority', sa.String(length=50), server_default='medium', nullable=False),
    sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), server_default='1.0', nullable=False),
    sa.Column('ai_raw_output', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=1536), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['decision_id'], ['decisions.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_action_items_due_date'), 'action_items', ['due_date'], unique=False)
    op.create_index(op.f('ix_action_items_meeting_id'), 'action_items', ['meeting_id'], unique=False)
    op.create_index(op.f('ix_action_items_org_id'), 'action_items', ['org_id'], unique=False)
    op.create_index(op.f('ix_action_items_owner_id'), 'action_items', ['owner_id'], unique=False)
    op.create_index(op.f('ix_action_items_status'), 'action_items', ['status'], unique=False)
                                  


def downgrade() -> None:
                           
                                                                 
    op.drop_index(op.f('ix_action_items_status'), table_name='action_items')
    op.drop_index(op.f('ix_action_items_owner_id'), table_name='action_items')
    op.drop_index(op.f('ix_action_items_org_id'), table_name='action_items')
    op.drop_index(op.f('ix_action_items_meeting_id'), table_name='action_items')
    op.drop_index(op.f('ix_action_items_due_date'), table_name='action_items')
    op.drop_table('action_items')
    op.drop_index(op.f('ix_risks_severity'), table_name='risks')
    op.drop_index(op.f('ix_risks_org_id'), table_name='risks')
    op.drop_index(op.f('ix_risks_meeting_id'), table_name='risks')
    op.drop_table('risks')
    op.drop_index(op.f('ix_open_questions_org_id'), table_name='open_questions')
    op.drop_index(op.f('ix_open_questions_meeting_id'), table_name='open_questions')
    op.drop_table('open_questions')
    op.drop_index(op.f('ix_memory_chunks_org_id'), table_name='memory_chunks')
    op.drop_index(op.f('ix_memory_chunks_meeting_id'), table_name='memory_chunks')
    op.drop_table('memory_chunks')
    op.drop_index(op.f('ix_decisions_org_id'), table_name='decisions')
    op.drop_index(op.f('ix_decisions_meeting_id'), table_name='decisions')
    op.drop_table('decisions')
                                  
