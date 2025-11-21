-- Migration: v1.3.0 Sessions and Login History
-- Description: Add tables for active sessions tracking and login history

-- ============================================================================
-- USER SESSIONS TABLE (Active Sessions Management)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    refresh_token_hash TEXT NOT NULL,  -- Hashed refresh token for identification
    device_info TEXT,                   -- User agent / device description
    ip_address INET,                    -- IP address
    location TEXT,                      -- Approximate location (city, country)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by UUID REFERENCES user_profiles(id)
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_sessions_token_hash ON user_sessions(refresh_token_hash);

-- ============================================================================
-- LOGIN HISTORY TABLE (Login History/Alerts)
-- ============================================================================
CREATE TABLE IF NOT EXISTS login_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    login_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    device_info TEXT,                   -- User agent
    location TEXT,                      -- City, country
    login_status VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'locked'
    failure_reason TEXT,                -- Reason if failed
    is_new_device BOOLEAN DEFAULT FALSE,
    is_new_location BOOLEAN DEFAULT FALSE,
    notification_sent BOOLEAN DEFAULT FALSE
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON login_history(user_id);
CREATE INDEX IF NOT EXISTS idx_login_history_login_at ON login_history(login_at DESC);
CREATE INDEX IF NOT EXISTS idx_login_history_user_recent ON login_history(user_id, login_at DESC);

-- ============================================================================
-- RATE LIMITING TABLE (for persistent rate limit tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL,          -- IP address or user_id:endpoint
    endpoint VARCHAR(100),              -- API endpoint
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(key, endpoint)
);

-- Index for cleanup and lookup
CREATE INDEX IF NOT EXISTS idx_rate_limits_key ON rate_limits(key);
CREATE INDEX IF NOT EXISTS idx_rate_limits_window ON rate_limits(window_start);

-- ============================================================================
-- CLEANUP FUNCTION (auto-cleanup old records)
-- ============================================================================
CREATE OR REPLACE FUNCTION cleanup_old_security_records()
RETURNS void AS $$
BEGIN
    -- Delete login history older than 90 days
    DELETE FROM login_history WHERE login_at < NOW() - INTERVAL '90 days';

    -- Delete expired sessions
    DELETE FROM user_sessions WHERE expires_at < NOW() - INTERVAL '7 days';

    -- Delete old rate limit records
    DELETE FROM rate_limits WHERE window_start < NOW() - INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;

-- Comments
COMMENT ON TABLE user_sessions IS 'Tracks active user sessions for session management';
COMMENT ON TABLE login_history IS 'Records all login attempts for security auditing';
COMMENT ON TABLE rate_limits IS 'Tracks API rate limiting per IP/user';

-- ============================================================================
-- ADD SECURITY MODULE TO ADMIN
-- ============================================================================
INSERT INTO modules (module_key, module_name, description, is_active, display_order, parent_module_id, icon)
SELECT 'admin_security', 'Security', 'Security dashboard - sessions, login history', TRUE, 5,
       (SELECT id FROM modules WHERE module_key = 'admin'), 'Security'
WHERE NOT EXISTS (SELECT 1 FROM modules WHERE module_key = 'admin_security');
