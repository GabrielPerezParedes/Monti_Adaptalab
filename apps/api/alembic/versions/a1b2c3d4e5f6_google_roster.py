"""google workspace user fields + pilot roster

Revision ID: a1b2c3d4e5f6
Revises: e048039af4bc
Create Date: 2026-11-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'e048039af4bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch:
        batch.alter_column('password_hash', existing_type=sa.String(length=255), nullable=True)
        batch.add_column(sa.Column('email', sa.String(length=120), nullable=True))
        batch.add_column(sa.Column('google_sub', sa.String(length=120), nullable=True))
        batch.add_column(sa.Column('auth_provider', sa.String(length=20), server_default='local', nullable=False))
        batch.create_unique_constraint('uq_users_email', ['email'])
        batch.create_unique_constraint('uq_users_google_sub', ['google_sub'])
        batch.create_index('ix_users_email', ['email'])
        batch.create_index('ix_users_google_sub', ['google_sub'])

    op.create_table(
        'pilot_roster',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('display_name', sa.String(length=120), nullable=True),
        sa.Column('grade_id', sa.String(length=36), nullable=True),
        sa.Column('subject_id', sa.String(length=36), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['grade_id'], ['grades.id']),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_pilot_roster_email', 'pilot_roster', ['email'])


def downgrade() -> None:
    op.drop_index('ix_pilot_roster_email', table_name='pilot_roster')
    op.drop_table('pilot_roster')
    with op.batch_alter_table('users') as batch:
        batch.drop_index('ix_users_google_sub')
        batch.drop_index('ix_users_email')
        batch.drop_constraint('uq_users_google_sub', type_='unique')
        batch.drop_constraint('uq_users_email', type_='unique')
        batch.drop_column('auth_provider')
        batch.drop_column('google_sub')
        batch.drop_column('email')
        batch.alter_column('password_hash', existing_type=sa.String(length=255), nullable=False)
