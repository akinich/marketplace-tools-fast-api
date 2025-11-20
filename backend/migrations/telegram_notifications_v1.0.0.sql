-- ============================================================================
-- Telegram Notifications Module Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-11-20
--
-- Changelog:
-- ----------
-- v1.0.0 (2025-11-20):
--   - Initial telegram notifications system database schema
--   - Created notification_settings table for global bot configuration
--   - Created telegram_link_codes table for user account linking
--   - Created low_stock_notifications table to track alert history
--   - Added telegram_chat_id column to user_profiles for personal DMs
--   - Created indexes for performance optimization
--   - Created triggers for automatic timestamp management
--
-- Description:
--   Sets up the complete database schema for the telegram notifications system,
--   including bot settings, user linking, and notification tracking.
-- ============================================================================

-- ============================================================================
-- 1. NOTIFICATION SETTINGS TABLE
-- ============================================================================
-- Stores global notification configuration (channel IDs, toggles, thresholds)

CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) NOT NULL DEFAULT 'string',
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW(),
    updated_by UUID REFERENCES user_profiles(id),
    CONSTRAINT valid_setting_type CHECK (setting_type IN ('string', 'integer', 'boolean', 'bigint'))
);

-- Create index for quick lookups
CREATE INDEX IF NOT EXISTS idx_notification_settings_key ON notification_settings(setting_key);

-- Insert default settings
INSERT INTO notification_settings (setting_key, setting_value, setting_type, description)
VALUES
    ('tickets_channel_id', NULL, 'bigint', 'Telegram channel ID for ticket notifications'),
    ('po_channel_id', NULL, 'bigint', 'Telegram channel ID for purchase order notifications'),
    ('inventory_channel_id', NULL, 'bigint', 'Telegram channel ID for inventory notifications'),
    ('enable_ticket_notifications', 'true', 'boolean', 'Enable/disable ticket notifications'),
    ('enable_po_notifications', 'true', 'boolean', 'Enable/disable purchase order notifications'),
    ('enable_inventory_notifications', 'true', 'boolean', 'Enable/disable inventory low stock notifications'),
    ('enable_personal_notifications', 'false', 'boolean', 'Enable/disable personal DM notifications (future feature)'),
    ('bot_status', 'inactive', 'string', 'Bot health status: active, inactive, error'),
    ('last_health_check', NULL, 'string', 'ISO timestamp of last successful bot health check'),
    ('last_error', NULL, 'string', 'Last error message from bot')
ON CONFLICT (setting_key) DO NOTHING;

-- ============================================================================
-- 2. USER TELEGRAM LINKING
-- ============================================================================
-- Add telegram_chat_id column to user_profiles for personal notifications

ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS telegram_chat_id BIGINT DEFAULT NULL;

-- Create index for telegram chat ID lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_telegram_chat_id ON user_profiles(telegram_chat_id);

-- Add unique constraint (one Telegram account per user)
ALTER TABLE user_profiles
ADD CONSTRAINT unique_telegram_chat_id UNIQUE (telegram_chat_id);

-- ============================================================================
-- 3. TELEGRAM LINK CODES TABLE
-- ============================================================================
-- One-time codes for users to link their Telegram accounts

CREATE TABLE IF NOT EXISTS telegram_link_codes (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    link_code VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    telegram_chat_id BIGINT,
    CONSTRAINT valid_expiry CHECK (expires_at > created_at)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_user ON telegram_link_codes(user_id);
CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_code ON telegram_link_codes(link_code);
CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_expires ON telegram_link_codes(expires_at);

-- ============================================================================
-- 4. LOW STOCK NOTIFICATIONS TRACKING
-- ============================================================================
-- Track which items have been notified to avoid duplicate alerts

CREATE TABLE IF NOT EXISTS low_stock_notifications (
    id SERIAL PRIMARY KEY,
    item_master_id INTEGER NOT NULL REFERENCES item_master(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    current_qty NUMERIC(10,2) NOT NULL,
    reorder_threshold NUMERIC(10,2) NOT NULL,
    notified_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    is_resolved BOOLEAN DEFAULT FALSE,
    CONSTRAINT valid_notification_type CHECK (notification_type IN ('first_alert', 'daily_summary'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_low_stock_notifications_item ON low_stock_notifications(item_master_id);
CREATE INDEX IF NOT EXISTS idx_low_stock_notifications_resolved ON low_stock_notifications(is_resolved);
CREATE INDEX IF NOT EXISTS idx_low_stock_notifications_notified_at ON low_stock_notifications(notified_at DESC);

-- ============================================================================
-- 5. TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Trigger for notification_settings updated_at
CREATE OR REPLACE FUNCTION update_notification_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_notification_settings_updated_at
    BEFORE UPDATE ON notification_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_settings_updated_at();

-- ============================================================================
-- 6. HELPER FUNCTIONS
-- ============================================================================

-- Function to get setting value with type casting
CREATE OR REPLACE FUNCTION get_notification_setting(p_key VARCHAR)
RETURNS TEXT AS $$
DECLARE
    v_value TEXT;
BEGIN
    SELECT setting_value INTO v_value
    FROM notification_settings
    WHERE setting_key = p_key;

    RETURN v_value;
END;
$$ LANGUAGE plpgsql;

-- Function to check if item has active unresolved low stock alert
CREATE OR REPLACE FUNCTION has_active_low_stock_alert(p_item_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM low_stock_notifications
    WHERE item_master_id = p_item_id
      AND is_resolved = FALSE
      AND notification_type = 'first_alert';

    RETURN v_count > 0;
END;
$$ LANGUAGE plpgsql;

-- Function to resolve low stock alerts when item is restocked
CREATE OR REPLACE FUNCTION resolve_low_stock_alerts_on_restock()
RETURNS TRIGGER AS $$
BEGIN
    -- If item quantity goes above reorder threshold, resolve all alerts
    IF NEW.current_qty > NEW.reorder_threshold THEN
        UPDATE low_stock_notifications
        SET is_resolved = TRUE,
            resolved_at = NOW()
        WHERE item_master_id = NEW.id
          AND is_resolved = FALSE;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_resolve_low_stock_on_restock
    AFTER UPDATE OF current_qty ON item_master
    FOR EACH ROW
    WHEN (NEW.current_qty > OLD.current_qty)  -- Only when qty increases
    EXECUTE FUNCTION resolve_low_stock_alerts_on_restock();

-- ============================================================================
-- 7. ADD TELEGRAM MODULE TO MODULES TABLE
-- ============================================================================

INSERT INTO modules (module_key, module_name, description, icon, display_order, is_active, parent_module_id)
VALUES ('telegram', 'Telegram Notifications', 'Configure Telegram bot for notifications', '📱', 99, TRUE,
    (SELECT id FROM modules WHERE module_key = 'admin'))
ON CONFLICT (module_key) DO NOTHING;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
