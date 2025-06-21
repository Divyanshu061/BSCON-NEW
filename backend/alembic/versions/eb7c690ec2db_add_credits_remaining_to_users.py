"""Add credits_remaining to users

Revision ID: eb7c690ec2db
Revises: cf9609010244
Create Date: 2025-06-21 16:59:35.202063
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision: str = 'eb7c690ec2db'
down_revision: Union[str, None] = 'cf9609010244'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add non-nullable credits_remaining with default value 0."""
    # Step 1: Add the column as nullable to avoid errors with existing rows
    op.add_column('users', sa.Column('credits_remaining', sa.Integer(), nullable=True))

    # Step 2: Set a default value for all existing rows
    op.execute('UPDATE users SET credits_remaining = 0')

    # Step 3: Alter the column to make it non-nullable
    op.alter_column('users', 'credits_remaining', nullable=False)


def downgrade() -> None:
    """Downgrade schema: Remove credits_remaining column."""
    op.drop_column('users', 'credits_remaining')
