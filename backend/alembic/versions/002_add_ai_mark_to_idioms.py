"""Add ai_mark field to idioms table

Revision ID: 002
Revises: 001
Create Date: 2025-11-15 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ai_mark column to idioms table."""
    op.add_column('idioms', sa.Column('ai_mark', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove ai_mark column from idioms table."""
    op.drop_column('idioms', 'ai_mark')
