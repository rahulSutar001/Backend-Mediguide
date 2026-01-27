BEGIN;

ALTER TABLE family_connections
  ADD COLUMN IF NOT EXISTS sender_display_name TEXT,
  ADD COLUMN IF NOT EXISTS receiver_display_name TEXT;

COMMIT;
