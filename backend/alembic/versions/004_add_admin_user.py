"""Add admin user

Revision ID: 004
Revises: 003
Create Date: 2025-11-15 16:00:00.000000

"""
from typing import Sequence, Union
import os
import secrets
import hashlib
from datetime import datetime
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash a password with salt using SHA256.

    This uses the same algorithm as PasswordHandler in the application.

    Args:
        password: Plain text password
        salt: Optional salt (generated if not provided)

    Returns:
        Tuple of (password_hash, salt)
    """
    if not salt:
        salt = secrets.token_hex(16)

    # Combine salt and password
    combined = f"{salt}:{password}"

    # Hash with SHA256
    password_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()

    return password_hash, salt


def upgrade() -> None:
    """Create admin user if it doesn't exist."""
    # Get database connection
    connection = op.get_bind()

    # Check if admin user already exists
    result = connection.execute(
        text("SELECT id FROM users WHERE username = 'admin'")
    ).fetchone()

    if result is None:
        # Get admin password from environment variable
        admin_password = os.environ.get('ADMIN_PASS', 'change_me')

        # Generate password hash and salt
        password_hash, salt = hash_password(admin_password)

        # Generate UUID for admin user
        admin_id = str(uuid.uuid4())

        # Insert admin user
        connection.execute(
            text("""
                INSERT INTO users (
                    id, username, email, password_hash, salt,
                    created_at, energy, max_energy, level, xp, role, last_recharge
                ) VALUES (
                    :id, :username, :email, :password_hash, :salt,
                    :created_at, :energy, :max_energy, :level, :xp, :role, :last_recharge
                )
            """),
            {
                'id': admin_id,
                'username': 'admin',
                'email': 'admin@subreverse.fun',
                'password_hash': password_hash,
                'salt': salt,
                'created_at': datetime.utcnow(),
                'energy': 10,
                'max_energy': 10,
                'level': 1,
                'xp': 0,
                'role': 'admin',
                'last_recharge': datetime.utcnow()
            }
        )

        print(f"Admin user created with ID: {admin_id}")
    else:
        print("Admin user already exists, skipping creation")


def downgrade() -> None:
    """Remove admin user."""
    connection = op.get_bind()

    # Delete admin user
    connection.execute(
        text("DELETE FROM users WHERE username = 'admin'")
    )

    print("Admin user removed")
