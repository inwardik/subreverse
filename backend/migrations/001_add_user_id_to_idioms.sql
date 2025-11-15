-- Migration: Add user_id to idioms table
-- This migration adds user ownership to idioms

-- Add user_id column
ALTER TABLE idioms ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);

-- Create index on user_id for better query performance
CREATE INDEX IF NOT EXISTS idx_idioms_user_id ON idioms(user_id);

-- Update status values: rename 'active' to 'published'
UPDATE idioms SET status = 'published' WHERE status = 'active';

-- For existing idioms without user_id, set to a default admin user
-- You may need to manually update this based on your admin user ID
-- UPDATE idioms SET user_id = 'your-admin-user-id' WHERE user_id IS NULL;

-- Note: After running this migration, you'll need to manually set user_id for existing idioms
-- or delete them if they're not needed.
