-- ============================================================================
-- Telegram Notifications Module Migration - Patch v1.0.1
-- ============================================================================
-- Version: 1.0.1
-- Created: 2025-11-21
--
-- Changelog:
-- ----------
-- v1.0.1 (2025-11-21):
--   - Fix: Ensure updated_by column in notification_settings is nullable
--   - This allows system-initiated updates to pass NULL instead of requiring a UUID
--
-- Description:
--   Patches the notification_settings table to ensure updated_by can be NULL
--   for system-initiated status updates (bot health checks, etc.)
-- ============================================================================

-- Ensure updated_by column is nullable (this is safe to run even if already nullable)
ALTER TABLE notification_settings
ALTER COLUMN updated_by DROP NOT NULL;

-- Update any existing 'system' values to NULL if they somehow got inserted
UPDATE notification_settings
SET updated_by = NULL
WHERE updated_by IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM user_profiles WHERE id = updated_by
  );
