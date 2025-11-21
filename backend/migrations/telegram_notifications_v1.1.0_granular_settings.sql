-- ============================================================================
-- Telegram Notifications - Granular Settings Migration
-- ============================================================================
-- Version: 1.1.0
-- Created: 2025-11-21
--
-- Changelog:
-- ----------
-- v1.1.0 (2025-11-21):
--   - Added granular notification toggles per event type
--   - Tickets: created, updated, closed, comment, priority_changed
--   - POs: created, status_changed
--   - Inventory: first_alert, daily_summary
-- ============================================================================

-- Ticket notification toggles
INSERT INTO notification_settings (setting_key, setting_value, setting_type, description)
VALUES
    ('notify_ticket_created', 'true', 'boolean', 'Send notification when ticket is created'),
    ('notify_ticket_updated', 'true', 'boolean', 'Send notification when ticket is updated'),
    ('notify_ticket_closed', 'true', 'boolean', 'Send notification when ticket is closed'),
    ('notify_ticket_comment', 'true', 'boolean', 'Send notification when comment is added'),
    ('notify_ticket_priority_changed', 'true', 'boolean', 'Send notification when priority changes')
ON CONFLICT (setting_key) DO NOTHING;

-- PO notification toggles
INSERT INTO notification_settings (setting_key, setting_value, setting_type, description)
VALUES
    ('notify_po_created', 'true', 'boolean', 'Send notification when PO is created'),
    ('notify_po_status_changed', 'true', 'boolean', 'Send notification when PO status changes')
ON CONFLICT (setting_key) DO NOTHING;

-- Inventory notification toggles
INSERT INTO notification_settings (setting_key, setting_value, setting_type, description)
VALUES
    ('notify_low_stock_first_alert', 'true', 'boolean', 'Send first alert when item goes low'),
    ('notify_low_stock_daily_summary', 'true', 'boolean', 'Send daily summary of low stock items')
ON CONFLICT (setting_key) DO NOTHING;
