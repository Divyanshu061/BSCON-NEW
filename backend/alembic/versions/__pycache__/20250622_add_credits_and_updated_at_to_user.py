# File: alembic/versions/20250622_add_credits_and_updated_at_to_user.py
"""
Add credits and updated_at columns to users table

Revision ID: 20250622_add_credits_updated_at_to_user
Revises: eb7c690ec2db
Create Date: 2025-06-22 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250622_add_credits_updated_at_to_user'
down_revision = 'eb7c690ec2db'
branch_labels = None
dependencies = None


def upgrade():
    # Add credits column with default 5
    op.add_column(
        'users',
        sa.Column('credits', sa.Integer(), nullable=False, server_default='5')
    )
    # Add updated_at column with default now()
    op.add_column(
        'users',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()')
        )
    )
    # Remove old credits_remaining column
    op.drop_column('users', 'credits_remaining')


def downgrade():
    # Re-add credits_remaining column
    op.add_column(
        'users',
        sa.Column('credits_remaining', sa.Integer(), nullable=False, server_default='5')
    )
    # Remove new columns
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'credits')
