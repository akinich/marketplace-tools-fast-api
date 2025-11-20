-- ============================================================================
-- Tickets Module Migration
-- ============================================================================
-- Version: 1.0.0
-- Created: 2025-11-20
--
-- Changelog:
-- ----------
-- v1.0.0 (2025-11-20):
--   - Initial ticket system database schema
--   - Created tickets table with status, priority, and type fields
--   - Created ticket_comments table for discussion threads
--   - Added foreign key relationships to user_profiles
--   - Created indexes for performance optimization
--   - Added module registration in modules table
--   - Created triggers for automatic updated_at timestamp management
--
-- Description:
--   Sets up the complete database schema for the ticket system module,
--   including tables, indexes, constraints, and triggers.
-- ============================================================================

-- Create tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    ticket_type VARCHAR(50) NOT NULL DEFAULT 'issue',
    status VARCHAR(20) DEFAULT 'open',
    priority VARCHAR(20) DEFAULT NULL,
    created_by_id UUID NOT NULL REFERENCES user_profiles(id),
    closed_by_id UUID REFERENCES user_profiles(id),
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_ticket_type CHECK (ticket_type IN ('issue', 'feature_request', 'upgrade', 'others')),
    CONSTRAINT valid_status CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    CONSTRAINT valid_priority CHECK (priority IS NULL OR priority IN ('low', 'medium', 'high', 'critical'))
);

-- Create ticket_comments table
CREATE TABLE IF NOT EXISTS ticket_comments (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES user_profiles(id),
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for tickets
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_ticket_type ON tickets(ticket_type);
CREATE INDEX IF NOT EXISTS idx_tickets_created_by ON tickets(created_by_id);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);

-- Create indexes for ticket_comments
CREATE INDEX IF NOT EXISTS idx_ticket_comments_ticket_id ON ticket_comments(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_comments_user_id ON ticket_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_ticket_comments_created_at ON ticket_comments(created_at DESC);

-- Add tickets module to modules table (if not exists)
INSERT INTO modules (module_key, module_name, description, icon, display_order, is_active)
VALUES ('tickets', 'Ticket System', 'Raise issues, feature requests, and upgrade suggestions', 'ticket', 10, TRUE)
ON CONFLICT (module_key) DO NOTHING;

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_tickets_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_tickets_updated_at();

CREATE OR REPLACE TRIGGER trigger_ticket_comments_updated_at
    BEFORE UPDATE ON ticket_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_tickets_updated_at();
