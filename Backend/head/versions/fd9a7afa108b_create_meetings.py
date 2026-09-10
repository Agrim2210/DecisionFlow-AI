   
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


                                        
revision: str = 'fd9a7afa108b'
down_revision: Union[str, Sequence[str], None] = '375f7c227dc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
                         
                                                                 
    op.create_table('meetings',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('source', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('meeting_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('duration_seconds', sa.Integer(), nullable=True),
    sa.Column('participant_ids', postgresql.ARRAY(sa.UUID()), server_default='{}', nullable=False),
    sa.Column('processing_meta', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_meetings_created_by'), 'meetings', ['created_by'], unique=False)
    op.create_index(op.f('ix_meetings_org_id'), 'meetings', ['org_id'], unique=False)
    op.create_index(op.f('ix_meetings_status'), 'meetings', ['status'], unique=False)
    op.create_table('transcripts',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('meeting_id', sa.UUID(), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('raw_s3_key', sa.Text(), nullable=False),
    sa.Column('normalized_s3_key', sa.Text(), nullable=True),
    sa.Column('raw_text', sa.Text(), nullable=True),
    sa.Column('content_hash', sa.String(length=64), nullable=True),
    sa.Column('word_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('speaker_map', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transcripts_content_hash'), 'transcripts', ['content_hash'], unique=False)
    op.create_index(op.f('ix_transcripts_meeting_id'), 'transcripts', ['meeting_id'], unique=True)
    op.create_index(op.f('ix_transcripts_org_id'), 'transcripts', ['org_id'], unique=False)
                                  


def downgrade() -> None:
                           
                                                                 
    op.drop_index(op.f('ix_transcripts_org_id'), table_name='transcripts')
    op.drop_index(op.f('ix_transcripts_meeting_id'), table_name='transcripts')
    op.drop_index(op.f('ix_transcripts_content_hash'), table_name='transcripts')
    op.drop_table('transcripts')
    op.drop_index(op.f('ix_meetings_status'), table_name='meetings')
    op.drop_index(op.f('ix_meetings_org_id'), table_name='meetings')
    op.drop_index(op.f('ix_meetings_created_by'), table_name='meetings')
    op.drop_table('meetings')
                                  
