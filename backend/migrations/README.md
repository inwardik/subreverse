# Database Migrations (Legacy)

⚠️ **Note**: This directory contains legacy SQL migration scripts. The project now uses **Alembic** for database migrations.

## For New Migrations

**Use Alembic instead**:

```bash
# From project root
make migrate           # Apply all pending migrations
make migrate-auto      # Generate migration from model changes
make migrate-history   # Show migration history
```

See project `Makefile` and `CLAUDE.md` for full Alembic documentation.

---

## Legacy Migrations (For Reference Only)

These SQL scripts were used before Alembic was adopted:

### `001_add_user_id_to_idioms.sql`
- Adds `user_id` column to idioms table
- Creates index on `user_id`
- Renames 'active' status to 'published'

**Note**: This migration has been incorporated into Alembic's initial schema (`backend/alembic/versions/001_initial_schema.py`).

### Manual Application (If Needed)

If you need to manually apply these legacy scripts:

```bash
# Using psql
psql -h localhost -U subreverse -d subreverse -f 001_add_user_id_to_idioms.sql

# Using docker
docker exec -i subreverse-postgres-1 psql -U subreverse -d subreverse < 001_add_user_id_to_idioms.sql
```

### Post-Migration Steps

If applying legacy migrations manually:

1. **Update existing idioms** (if any):
   ```sql
   -- Option 1: Delete orphaned idioms
   DELETE FROM idioms WHERE user_id IS NULL;

   -- Option 2: Assign to admin user
   UPDATE idioms SET user_id = 'your-admin-user-id' WHERE user_id IS NULL;
   ```

2. **Mark migration as applied in Alembic**:
   ```bash
   cd backend
   alembic stamp head
   ```

---

## Migration to Alembic

The project migrated to Alembic for better:
- Version control integration
- Automatic migration generation
- Rollback capabilities
- Environment-aware configurations

All future migrations should use Alembic.
