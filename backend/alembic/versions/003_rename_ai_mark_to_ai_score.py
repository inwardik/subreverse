"""Rename ai_mark to ai_score in idioms table

Revision ID: 003
Revises: 002
Create Date: 2025-11-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename ai_mark column to ai_score in idioms table."""
    op.alter_column('idioms', 'ai_mark', new_column_name='ai_score')


def downgrade() -> None:
    """Rename ai_score column back to ai_mark in idioms table."""
    op.alter_column('idioms', 'ai_score', new_column_name='ai_mark')
