   
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

                                        
revision: str = 'db808409948b'
down_revision: Union[str, Sequence[str], None] = 'ac71dfe4f9e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
                         
                                                                 
    op.create_table('audit_logs',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('actor_id', sa.UUID(), nullable=False),
    sa.Column('actor_type', sa.String(length=50), nullable=False),
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('aggregate_type', sa.String(length=100), nullable=False),
    sa.Column('aggregate_id', sa.UUID(), nullable=False),
    sa.Column('before_state', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('after_state', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('ip_address', sa.String(length=50), nullable=True),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_actor_id'), 'audit_logs', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_aggregate_id'), 'audit_logs', ['aggregate_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_aggregate_type'), 'audit_logs', ['aggregate_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_event_type'), 'audit_logs', ['event_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_occurred_at'), 'audit_logs', ['occurred_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_org_id'), 'audit_logs', ['org_id'], unique=False)
    op.create_table('escalation_policies',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('is_default', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('trigger_after_hours', sa.Integer(), server_default='24', nullable=False),
    sa.Column('levels', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_escalation_policies_org_id'), 'escalation_policies', ['org_id'], unique=False)
    op.create_table('notifications',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('recipient_id', sa.UUID(), nullable=False),
    sa.Column('event_type', sa.String(length=100), nullable=False),
    sa.Column('channel', sa.String(length=50), nullable=False),
    sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
    sa.Column('subject', sa.String(length=500), server_default='', nullable=False),
    sa.Column('body', sa.Text(), server_default='', nullable=False),
    sa.Column('related_item_id', sa.UUID(), nullable=True),
    sa.Column('related_item_type', sa.String(length=50), nullable=True),
    sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('failed_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_event_type'), 'notifications', ['event_type'], unique=False)
    op.create_index(op.f('ix_notifications_org_id'), 'notifications', ['org_id'], unique=False)
    op.create_index(op.f('ix_notifications_recipient_id'), 'notifications', ['recipient_id'], unique=False)
    op.create_table('user_reliability_snapshots',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('tasks_assigned', sa.Integer(), server_default='0', nullable=False),
    sa.Column('tasks_completed', sa.Integer(), server_default='0', nullable=False),
    sa.Column('tasks_on_time', sa.Integer(), server_default='0', nullable=False),
    sa.Column('tasks_overdue', sa.Integer(), server_default='0', nullable=False),
    sa.Column('tasks_cancelled', sa.Integer(), server_default='0', nullable=False),
    sa.Column('reliability_score', sa.Float(), server_default='100.0', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'org_id', name='uq_reliability_user_org_date')
    )
    op.create_index(op.f('ix_user_reliability_snapshots_org_id'), 'user_reliability_snapshots', ['org_id'], unique=False)
    op.create_index(op.f('ix_user_reliability_snapshots_snapshot_date'), 'user_reliability_snapshots', ['snapshot_date'], unique=False)
    op.create_index(op.f('ix_user_reliability_snapshots_user_id'), 'user_reliability_snapshots', ['user_id'], unique=False)
    op.create_table('meeting_analytics',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('meeting_id', sa.UUID(), nullable=False),
    sa.Column('decisions_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('action_items_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('unassigned_tasks', sa.Integer(), server_default='0', nullable=False),
    sa.Column('risks_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('critical_risks', sa.Integer(), server_default='0', nullable=False),
    sa.Column('dependencies_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('open_questions_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('execution_rate', sa.Float(), server_default='0.0', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('meeting_id', name='uq_meeting_analytics_meeting')
    )
    op.create_index(op.f('ix_meeting_analytics_meeting_id'), 'meeting_analytics', ['meeting_id'], unique=True)
    op.create_index(op.f('ix_meeting_analytics_org_id'), 'meeting_analytics', ['org_id'], unique=False)
    op.create_table('escalations',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('action_item_id', sa.UUID(), nullable=False),
    sa.Column('policy_id', sa.UUID(), nullable=True),
    sa.Column('current_level', sa.Integer(), server_default='1', nullable=False),
    sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
    sa.Column('history', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
    sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['action_item_id'], ['action_items.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['policy_id'], ['escalation_policies.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_escalations_action_item_id'), 'escalations', ['action_item_id'], unique=False)
    op.create_index(op.f('ix_escalations_org_id'), 'escalations', ['org_id'], unique=False)
    op.create_index(op.f('ix_escalations_status'), 'escalations', ['status'], unique=False)
    op.create_table('task_dependencies',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('upstream_id', sa.UUID(), nullable=False),
    sa.Column('downstream_id', sa.UUID(), nullable=False),
    sa.Column('dependency_type', sa.String(length=50), server_default='finish_to_start', nullable=False),
    sa.Column('detected_by', sa.String(length=50), server_default='ai', nullable=False),
    sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), server_default='1.0', nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['downstream_id'], ['action_items.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['upstream_id'], ['action_items.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('upstream_id', 'downstream_id', name='uq_task_dependency_edge')
    )
    op.create_index(op.f('ix_task_dependencies_downstream_id'), 'task_dependencies', ['downstream_id'], unique=False)
    op.create_index(op.f('ix_task_dependencies_org_id'), 'task_dependencies', ['org_id'], unique=False)
    op.create_index(op.f('ix_task_dependencies_upstream_id'), 'task_dependencies', ['upstream_id'], unique=False)
                                  


def downgrade() -> None:
                           
                                                                 
    op.drop_index(op.f('ix_task_dependencies_upstream_id'), table_name='task_dependencies')
    op.drop_index(op.f('ix_task_dependencies_org_id'), table_name='task_dependencies')
    op.drop_index(op.f('ix_task_dependencies_downstream_id'), table_name='task_dependencies')
    op.drop_table('task_dependencies')
    op.drop_index(op.f('ix_escalations_status'), table_name='escalations')
    op.drop_index(op.f('ix_escalations_org_id'), table_name='escalations')
    op.drop_index(op.f('ix_escalations_action_item_id'), table_name='escalations')
    op.drop_table('escalations')
    op.drop_index(op.f('ix_meeting_analytics_org_id'), table_name='meeting_analytics')
    op.drop_index(op.f('ix_meeting_analytics_meeting_id'), table_name='meeting_analytics')
    op.drop_table('meeting_analytics')
    op.drop_index(op.f('ix_user_reliability_snapshots_user_id'), table_name='user_reliability_snapshots')
    op.drop_index(op.f('ix_user_reliability_snapshots_snapshot_date'), table_name='user_reliability_snapshots')
    op.drop_index(op.f('ix_user_reliability_snapshots_org_id'), table_name='user_reliability_snapshots')
    op.drop_table('user_reliability_snapshots')
    op.drop_index(op.f('ix_notifications_recipient_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_org_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_event_type'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_escalation_policies_org_id'), table_name='escalation_policies')
    op.drop_table('escalation_policies')
    op.drop_index(op.f('ix_audit_logs_org_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_occurred_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_event_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_aggregate_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_aggregate_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
                                  
