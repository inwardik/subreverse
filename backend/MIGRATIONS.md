# Database Migrations Guide

SubReverse uses **Alembic** for PostgreSQL schema migrations.

## Quick Start

### Apply All Pending Migrations

```bash
make migrate
```

This runs all unapplied migrations from `backend/alembic/versions/`.

### Check Current Version

```bash
make migrate-current
```

Shows which migration is currently applied.

### View Migration History

```bash
make migrate-history
```

Lists all migrations with their status.

---

## Creating New Migrations

### Method 1: Auto-generate (Recommended)

Alembic can automatically detect changes in your SQLAlchemy models:

```bash
# 1. Modify models in backend/src/infrastructure/database/postgres_models.py
# 2. Generate migration
make migrate-auto
# You'll be prompted for a migration message

# 3. Review the generated file in backend/alembic/versions/
# 4. Apply the migration
make migrate
```

**Example**:
```bash
make migrate-auto
# Enter migration message: add description field to users

# Review backend/alembic/versions/abc123_add_description_field_to_users.py
# Apply
make migrate
```

### Method 2: Manual Migration

For complex migrations or data transformations:

```bash
cd backend
alembic revision -m "your migration description"
```

This creates a new migration file in `alembic/versions/`. Edit the file to add:

```python
def upgrade() -> None:
    """Apply migration."""
    op.add_column('users', sa.Column('description', sa.Text(), nullable=True))

def downgrade() -> None:
    """Rollback migration."""
    op.drop_column('users', 'description')
```

Then apply:

```bash
make migrate
```

---

## Rollback Migrations

⚠️ **Use with caution!** This will undo the last migration.

```bash
make migrate-downgrade
```

You'll be prompted to confirm before rollback.

---

## Environment Configuration

Alembic uses the following to determine the database URL (in order):

1. **Environment variable**: `POSTGRES_URL`
2. **alembic.ini**: Default URL in config file

### For Docker/Production

Set the `POSTGRES_URL` environment variable:

```bash
export POSTGRES_URL=postgresql+asyncpg://user:password@host:port/database
make migrate
```

### For Local Development

Edit `backend/alembic.ini`:

```ini
sqlalchemy.url = postgresql+asyncpg://subreverse:subreverse@localhost:5432/subreverse
```

---

## Migration File Structure

Migration files are in `backend/alembic/versions/`:

```
backend/alembic/versions/
├── 001_initial_schema.py           # Initial database schema
└── abc123_your_migration_name.py   # Auto-generated migrations
```

Each file contains:

```python
revision = 'abc123'           # This migration's ID
down_revision = 'xyz789'      # Previous migration's ID

def upgrade() -> None:
    """Apply changes."""
    pass

def downgrade() -> None:
    """Rollback changes."""
    pass
```

---

## Common Operations

### Add a New Column

```python
def upgrade() -> None:
    op.add_column('table_name',
        sa.Column('new_column', sa.String(255), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('table_name', 'new_column')
```

### Create an Index

```python
def upgrade() -> None:
    op.create_index('idx_table_column', 'table_name', ['column_name'])

def downgrade() -> None:
    op.drop_index('idx_table_column', table_name='table_name')
```

### Modify a Column

```python
def upgrade() -> None:
    op.alter_column('table_name', 'column_name',
        type_=sa.String(500),
        existing_type=sa.String(255)
    )

def downgrade() -> None:
    op.alter_column('table_name', 'column_name',
        type_=sa.String(255),
        existing_type=sa.String(500)
    )
```

### Data Migration

```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Update data
    op.execute("""
        UPDATE users
        SET role = 'admin'
        WHERE username = 'admin'
    """)

def downgrade() -> None:
    # Revert data
    op.execute("""
        UPDATE users
        SET role = 'user'
        WHERE username = 'admin'
    """)
```

---

## Troubleshooting

### "Can't locate revision identified by 'xyz'"

Your database and migration files are out of sync.

**Solution 1**: Stamp to current version
```bash
cd backend
alembic stamp head
```

**Solution 2**: Start fresh (⚠️ destroys data)
```bash
# Drop all tables
# Run migrations
make migrate
```

### "Target database is not up to date"

You have unapplied migrations.

```bash
make migrate
```

### Auto-generate creates empty migration

Alembic couldn't detect changes. Ensure:
1. Models are imported in `alembic/env.py`
2. You modified `postgres_models.py` correctly
3. Changes are actually new (not already in database)

---

## Best Practices

1. **Always review auto-generated migrations** before applying
2. **Test migrations** on dev/staging before production
3. **Create backups** before running migrations in production
4. **Write reversible migrations** (proper `downgrade()` functions)
5. **One logical change per migration** for easier troubleshooting
6. **Use descriptive migration messages**

---

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- Project documentation: `CLAUDE.md`
- Database schema: See `CLAUDE.md` → Database Schema section
