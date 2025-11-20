-- ============================================================================
-- Add Documentation Module to System (CORRECTED)
-- ============================================================================
-- Version: 1.0.1
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
-- Grant access to all existing active users (OPTIONAL)
-- ============================================================================
-- Run this to give all existing users access to the documentation:

INSERT INTO user_module_permissions (user_id, module_id)
SELECT u.id, m.id
FROM users u
CROSS JOIN modules m
WHERE m.module_key = 'docs'
AND u.is_active = true
AND u.role = 'User'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Notes:
-- ============================================================================
-- 1. Admin users automatically have access to all modules
-- 2. The icon 'MenuBook' is a Material-UI icon name (will render as book icon)
-- 3. display_order = 100 places it at the bottom of the sidebar
-- 4. All new users will need to be granted access, or you can auto-grant
--    in your user creation logic
-- ============================================================================
