# Database Migrations

This directory contains SQL migration scripts for the SubReverse application.

## How to Apply Migrations

### Using psql

```bash
# Connect to your PostgreSQL database
psql -h localhost -U subreverse -d subreverse -f 001_add_user_id_to_idioms.sql
```

### Using pgAdmin or other GUI tools

1. Open your database management tool
2. Connect to the `subreverse` database
3. Run the SQL script from `001_add_user_id_to_idioms.sql`

### Using Docker

```bash
# If running via docker-compose
docker exec -i subreverse-postgres-1 psql -U subreverse -d subreverse < 001_add_user_id_to_idioms.sql
```

## Migration Order

1. `001_add_user_id_to_idioms.sql` - Adds user ownership to idioms

## Post-Migration Steps

After running the migration:

1. **Update existing idioms**: You'll need to set a `user_id` for any existing idioms that don't have one. You can either:
   - Delete old idioms: `DELETE FROM idioms WHERE user_id IS NULL;`
   - Or assign them to an admin user: `UPDATE idioms SET user_id = 'your-admin-user-id' WHERE user_id IS NULL;`

2. **Make user_id NOT NULL** (optional, for data integrity):
   ```sql
   ALTER TABLE idioms ALTER COLUMN user_id SET NOT NULL;
   ```

## Notes

- Always backup your database before running migrations
- Migrations are designed to be idempotent (can be run multiple times safely)
- The `status` field has been updated from 'active' to 'published'
