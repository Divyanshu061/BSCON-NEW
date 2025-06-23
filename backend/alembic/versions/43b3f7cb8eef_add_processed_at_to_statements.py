"""Add processed_at to statements

Revision ID: 43b3f7cb8eef
Revises: 091d8d77243a
Create Date: 2025-06-23 17:12:19.632240

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '43b3f7cb8eef'
down_revision = '091d8d77243a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'statements',
        sa.Column(
            'processed_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp when this statement was marked processed'
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('statements', 'processed_at')
