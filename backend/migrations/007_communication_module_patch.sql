-- ============================================================================
-- Migration 007 Patch: Fix Telegram Module Migration
-- ============================================================================
-- Description: Corrects the telegram module migration to use admin_telegram
--              instead of the legacy inactive telegram module
-- Author: System
-- Date: 2025-11-22
-- Version: 1.0.1
-- Depends on: 007_communication_module.sql
-- ============================================================================

-- BACKGROUND:
-- The original migration incorrectly moved the old inactive 'telegram' module
-- (id: 54) under Communication. The correct module to move was 'admin_telegram'
-- (id: 61), which is the active telegram notifications module.

-- THIS PATCH FIXES:
-- 1. Renames old telegram module (id: 54) to 'telegram_legacy'
-- 2. Moves admin_telegram (id: 61) under Communication as 'com_telegram'

DO $$
DECLARE
    comm_module_id INT;
    old_telegram_id INT;
    admin_telegram_id INT;
BEGIN
    -- Get Communication module ID
    SELECT id INTO comm_module_id FROM modules WHERE module_key = 'communication';

    -- Get module IDs
    -- The old telegram might already be renamed to com_telegram or still be telegram
    SELECT id INTO old_telegram_id FROM modules
    WHERE module_key IN ('telegram', 'com_telegram')
    AND is_active = false;

    -- Get the active admin_telegram module
    SELECT id INTO admin_telegram_id FROM modules WHERE module_key = 'admin_telegram';

    -- Only proceed if we found the modules
    IF old_telegram_id IS NOT NULL AND admin_telegram_id IS NOT NULL THEN

        -- Step 1: Rename the old module to avoid unique constraint conflict
        UPDATE modules
        SET
            module_key = 'telegram_legacy',
            parent_module_id = NULL,
            display_order = 99
        WHERE id = old_telegram_id;

        RAISE NOTICE 'Renamed old telegram module (id: %) to telegram_legacy', old_telegram_id;

        -- Step 2: Move admin_telegram under Communication as com_telegram
        UPDATE modules
        SET
            module_key = 'com_telegram',
            parent_module_id = comm_module_id,
            display_order = 1
        WHERE id = admin_telegram_id;

        RAISE NOTICE 'Moved admin_telegram (id: %) under Communication as com_telegram', admin_telegram_id;

    ELSIF admin_telegram_id IS NULL THEN
        RAISE NOTICE 'admin_telegram module not found - patch not needed or already applied';
    ELSIF old_telegram_id IS NULL THEN
        RAISE NOTICE 'Legacy telegram module not found - patch may already be applied';
    END IF;

END $$;

-- Verify the patch
SELECT
    m.id,
    m.module_key,
    m.module_name,
    CASE WHEN m.parent_module_id IS NULL THEN 'Parent/Standalone' ELSE 'Child' END as type,
    p.module_name as parent_name,
    m.display_order,
    m.is_active
FROM modules m
LEFT JOIN modules p ON m.parent_module_id = p.id
WHERE m.module_key LIKE '%telegram%' OR m.module_key LIKE 'com%' OR m.module_key = 'communication'
ORDER BY COALESCE(m.parent_module_id, m.id), m.display_order;

-- Expected result after patch:
-- telegram_legacy (id: 54): Standalone, inactive, display_order: 99
-- com_telegram (id: 61): Child of Communication, active, display_order: 1
-- All other com_* modules under Communication
