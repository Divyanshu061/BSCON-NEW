"""Add default value to credits_remaining

Revision ID: 091d8d77243a
Revises: eb7c690ec2db
Create Date: 2025-06-22 19:07:39.995022
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '091d8d77243a'
down_revision: Union[str, None] = 'eb7c690ec2db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'users',
        'credits_remaining',
        existing_type=sa.Integer(),
        nullable=False,
        server_default=sa.text('5'),
    )


def downgrade() -> None:
    op.alter_column(
        'users',
        'credits_remaining',
        existing_type=sa.Integer(),
        nullable=False,
        server_default=None,
    )
