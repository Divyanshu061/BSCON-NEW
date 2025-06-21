"""Make created_at default to now()

Revision ID: cf9609010244
Revises: 5687c2b675ce
Create Date: 2025-06-12 17:24:20.671149

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cf9609010244'
down_revision: Union[str, None] = '5687c2b675ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add server default for created_at"""
    op.alter_column(
        'users',
        'created_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text('now()'),
        existing_nullable=False
    )
    op.alter_column(
        'statements',
        'uploaded_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text('now()'),
        existing_nullable=False
    )


def downgrade() -> None:
    """Downgrade schema: remove server default for created_at"""
    op.alter_column(
        'statements',
        'uploaded_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False
    )
    op.alter_column(
        'users',
        'created_at',
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False
    )
