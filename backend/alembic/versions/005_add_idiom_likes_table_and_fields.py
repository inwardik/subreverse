"""Add idiom likes table and likes/dislikes fields

Revision ID: 005
Revises: 004
Create Date: 2025-11-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add idiom_likes table and likes/dislikes fields to idioms table."""

    # Add likes and dislikes columns to idioms table
    op.add_column('idioms', sa.Column('likes', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('idioms', sa.Column('dislikes', sa.Integer(), nullable=False, server_default='0'))

    # Create idiom_likes table
    op.create_table(
        'idiom_likes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('idiom_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'idiom_id', name='uq_user_idiom')
    )

    # Create indexes for better query performance
    op.create_index('ix_idiom_likes_user_id', 'idiom_likes', ['user_id'])
    op.create_index('ix_idiom_likes_idiom_id', 'idiom_likes', ['idiom_id'])


def downgrade() -> None:
    """Remove idiom_likes table and likes/dislikes fields from idioms table."""

    # Drop indexes
    op.drop_index('ix_idiom_likes_idiom_id', table_name='idiom_likes')
    op.drop_index('ix_idiom_likes_user_id', table_name='idiom_likes')

    # Drop idiom_likes table
    op.drop_table('idiom_likes')

    # Remove likes and dislikes columns from idioms table
    op.drop_column('idioms', 'dislikes')
    op.drop_column('idioms', 'likes')
