# Deployment Guide

## Testing Automatic Migrations

To test that migrations run automatically on container startup:

### 1. Build and Start Services

```bash
# Stop any running containers
docker-compose down

# Remove backend image to force rebuild
docker rmi subreverse-backend 2>/dev/null || true

# Start services (this will rebuild the backend image)
docker-compose up --build
```

### 2. Expected Behavior

You should see output like:

```
backend    | Starting backend entrypoint script...
backend    | Waiting for PostgreSQL to be ready...
backend    | Connecting to PostgreSQL at postgres:5432...
backend    | PostgreSQL is ready!
backend    | Running database migrations...
backend    | INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
backend    | INFO  [alembic.runtime.migration] Will assume transactional DDL.
backend    | INFO  [alembic.runtime.migration] Running upgrade  -> abc123, initial schema
backend    | ✓ Migrations applied successfully!
backend    | Starting FastAPI application...
backend    | INFO:     Started server process [1]
backend    | INFO:     Waiting for application startup.
backend    | INFO:     Application startup complete.
```

### 3. Verify Migrations

Check that the database schema is up-to-date:

```bash
# Check current migration version
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history
```

### 4. Test with Fresh Database

To test migrations from scratch:

```bash
# Stop services
docker-compose down

# Remove PostgreSQL data volume (⚠️ destroys all data!)
docker volume rm subreverse_postgres_data

# Start services again - migrations will create schema from scratch
docker-compose up
```

---

## Production Deployment

### Environment Variables

Ensure these are set in your production environment:

```bash
POSTGRES_URL=postgresql+asyncpg://user:password@host:port/database
MONGODB_URL=mongodb://host:27017/
MONGODB_DB_NAME=subtitles
ELASTICSEARCH_URL=http://elasticsearch:9200
JWT_SECRET=your-secure-secret-key
ADMIN_PASS=your-admin-password
```

### Deployment Steps

1. **Pull latest code**:
   ```bash
   git pull origin main
   ```

2. **Build images**:
   ```bash
   docker-compose build
   ```

3. **Start services** (migrations run automatically):
   ```bash
   docker-compose up -d
   ```

4. **Verify migrations**:
   ```bash
   docker-compose logs backend | grep -A5 "Running database migrations"
   docker-compose exec backend alembic current
   ```

5. **Check application health**:
   ```bash
   curl http://localhost:8000/health
   ```

---

## Rollback

If a migration fails or causes issues:

### 1. Check Migration Status

```bash
docker-compose exec backend alembic current
docker-compose exec backend alembic history
```

### 2. Rollback One Migration

```bash
docker-compose exec backend alembic downgrade -1
```

### 3. Rollback to Specific Version

```bash
docker-compose exec backend alembic downgrade <revision_id>
```

### 4. Restart Services

```bash
docker-compose restart backend
```

---

## Troubleshooting

### Issue: "PostgreSQL is not ready yet"

**Cause**: PostgreSQL container is still starting up.

**Solution**: The entrypoint script waits up to 30 seconds. If this isn't enough:

```bash
# Increase wait time in backend/entrypoint.sh
# Change: for i in {1..30}; do
# To:     for i in {1..60}; do
```

### Issue: Migration fails with "revision not found"

**Cause**: Database and migration files are out of sync.

**Solution**: Stamp database to current version:

```bash
docker-compose exec backend alembic stamp head
docker-compose restart backend
```

### Issue: "Target database is not up to date"

**Cause**: New migrations exist but haven't been applied.

**Solution**: Restart the backend container (migrations will run automatically):

```bash
docker-compose restart backend
```

---

## Manual Migration Commands

If you need to run migrations manually (not recommended in production):

```bash
# Apply all pending migrations
docker-compose exec backend alembic upgrade head

# Generate new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Rollback last migration
docker-compose exec backend alembic downgrade -1

# View current version
docker-compose exec backend alembic current

# View history
docker-compose exec backend alembic history --verbose
```

---

## Best Practices

1. **Always test migrations** on staging before production
2. **Backup database** before deploying new migrations
3. **Monitor logs** during deployment for migration errors
4. **Have rollback plan** ready before deploying
5. **Review auto-generated migrations** before committing
6. **One logical change per migration** for easier troubleshooting
7. **Document breaking changes** in migration commit messages

---

## Migration Files

Migration files are in `backend/alembic/versions/`:

- `001_initial_schema.py` - Initial database schema (users, idioms tables)
- `002_add_ai_mark_to_idioms.py` - Add AI scoring to idioms
- `003_rename_ai_mark_to_ai_score.py` - Rename field
- `004_add_admin_user.py` - Create admin user from ADMIN_PASS env var

New migrations are auto-generated with timestamp prefixes.
