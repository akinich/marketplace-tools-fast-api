-- ============================================================================
-- Add Documentation Module to System
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-11-20
-- Description: Adds the Documentation/Help module to the sidebar navigation
-- ============================================================================

-- Insert the Documentation module
INSERT INTO modules (
  module_key,
  module_name,
  description,
  icon,
  display_order,
  is_active
) VALUES (
  'docs',                                         -- module_key
  'Help & Documentation',                         -- module_name
  'In-app help guides and documentation',         -- description
  'MenuBook',                                     -- icon (Material-UI icon name)
  100,                                            -- display_order (put at bottom)
  true                                            -- is_active
)
ON CONFLICT (module_key) DO UPDATE SET
  module_name = EXCLUDED.module_name,
  description = EXCLUDED.description,
  icon = EXCLUDED.icon,
  display_order = EXCLUDED.display_order,
  is_active = EXCLUDED.is_active;

-- Verify the module was added
SELECT
  id AS module_id,
  module_key,
  module_name,
  description,
  icon,
  display_order,
  is_active,
  created_at
FROM modules
WHERE module_key = 'docs';

-- ============================================================================
-- Notes:
-- ============================================================================
-- 1. All users (including regular users and admins) will see this module
--    since it's for help/documentation
-- 2. No special permissions needed - documentation is available to everyone
-- 3. To make it available to all existing users, run:
--
--    INSERT INTO user_module_permissions (user_id, module_id)
--    SELECT u.id, m.id
--    FROM users u
--    CROSS JOIN modules m
--    WHERE m.module_key = 'docs'
--    AND u.is_active = true
--    AND u.role = 'User'
--    ON CONFLICT DO NOTHING;
--
-- 4. Admin users automatically have access to all modules, no permission needed
-- ============================================================================
