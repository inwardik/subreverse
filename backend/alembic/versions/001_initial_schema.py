"""Initial schema with users and idioms tables

Revision ID: 001
Revises:
Create Date: 2025-11-15 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('salt', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('energy', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_energy', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('xp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('role', sa.String(50), nullable=False, server_default='user'),
        sa.Column('last_recharge', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )

    # Create idioms table with user_id
    op.create_table(
        'idioms',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('en', sa.Text(), nullable=False),
        sa.Column('ru', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft', index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('idioms')
    op.drop_table('users')
