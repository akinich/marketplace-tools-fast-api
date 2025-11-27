-- ============================================================================
-- Migration 000: Base Schema for Testing
-- Description: Creates core tables needed for tests (without Supabase auth)
-- Author: Claude
-- Date: 2025-11-24
-- Updated: 2025-11-27 - Added auth schema to match production structure
-- ============================================================================

-- Create auth schema (to match Supabase production structure)
CREATE SCHEMA IF NOT EXISTS auth;

-- Users table in auth schema (simulates Supabase auth.users)
-- This matches the production structure where auth.users is in a separate schema
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth.users(email);

COMMENT ON TABLE auth.users IS 'User accounts (simulates Supabase auth.users)';

-- Roles table (referenced by user_profiles)
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default roles
INSERT INTO roles (role_name, description) VALUES
    ('Admin', 'Administrator with full access'),
    ('User', 'Regular user with limited access')
ON CONFLICT (role_name) DO NOTHING;

COMMENT ON TABLE roles IS 'User roles for role-based access control';

-- User profiles table (main table with all user data)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    role_id INTEGER REFERENCES roles(id) DEFAULT 2,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    must_change_password BOOLEAN DEFAULT false,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    last_password_change TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    phone_number VARCHAR(20),
    address TEXT,
    bio TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_role_id ON user_profiles(role_id);
CREATE INDEX idx_user_profiles_is_active ON user_profiles(is_active);

COMMENT ON TABLE user_profiles IS 'Extended user profile information with authentication data';

-- Login history table (tracks all login attempts)
CREATE TABLE IF NOT EXISTS login_history (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    ip_address INET,
    device_info TEXT,
    location VARCHAR(255),
    login_status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'locked'
    failure_reason TEXT,
    is_new_device BOOLEAN DEFAULT false,
    is_new_location BOOLEAN DEFAULT false,
    login_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_login_history_user_id ON login_history(user_id);
CREATE INDEX idx_login_history_login_status ON login_history(login_status);
CREATE INDEX idx_login_history_login_at ON login_history(login_at DESC);

COMMENT ON TABLE login_history IS 'Track login attempts and history for security monitoring';

-- User sessions table (tracks active user sessions)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) UNIQUE NOT NULL,
    device_info TEXT,
    ip_address INET,
    location VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_refresh_token_hash ON user_sessions(refresh_token_hash);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active);

COMMENT ON TABLE user_sessions IS 'Track active user sessions and refresh tokens';

-- Modules table (for module-based permissions and activity tracking)
CREATE TABLE IF NOT EXISTS modules (
    id SERIAL PRIMARY KEY,
    module_key VARCHAR(100) UNIQUE NOT NULL,
    module_name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    parent_module_id INTEGER REFERENCES modules(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_modules_module_key ON modules(module_key);
CREATE INDEX idx_modules_is_active ON modules(is_active);
CREATE INDEX idx_modules_parent_module_id ON modules(parent_module_id);

COMMENT ON TABLE modules IS 'System modules for feature organization and access control';

-- Insert base modules for testing
INSERT INTO modules (module_key, module_name, description, icon, display_order, is_active) VALUES
    ('admin', 'Administration', 'System administration and user management', '⚙️', 1, true),
    ('auth', 'Authentication', 'User authentication and security', '🔐', 2, true)
ON CONFLICT (module_key) DO NOTHING;

-- User module permissions table (for fine-grained access control)
CREATE TABLE IF NOT EXISTS user_module_permissions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    can_access BOOLEAN DEFAULT true,
    can_create BOOLEAN DEFAULT false,
    can_update BOOLEAN DEFAULT false,
    can_delete BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, module_id)
);

CREATE INDEX idx_user_module_permissions_user_id ON user_module_permissions(user_id);
CREATE INDEX idx_user_module_permissions_module_id ON user_module_permissions(module_id);
CREATE INDEX idx_user_module_permissions_can_access ON user_module_permissions(can_access);

COMMENT ON TABLE user_module_permissions IS 'Fine-grained user permissions for each module';

-- Activity logs table
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    user_role VARCHAR(50),
    action_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    module_key VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    success BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_action_type ON activity_logs(action_type);
CREATE INDEX idx_activity_logs_module_key ON activity_logs(module_key);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at DESC);

COMMENT ON TABLE activity_logs IS 'Audit trail of user activities';

-- Webhooks table
CREATE TABLE IF NOT EXISTS webhooks (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    secret VARCHAR(100) NOT NULL,
    events TEXT[] NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    custom_headers JSONB,
    retry_count INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_webhooks_user_id ON webhooks(user_id);
CREATE INDEX idx_webhooks_is_active ON webhooks(is_active);

COMMENT ON TABLE webhooks IS 'Webhook subscriptions for event notifications';

-- Webhook deliveries table
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id SERIAL PRIMARY KEY,
    webhook_id INTEGER REFERENCES webhooks(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    response_status_code INTEGER,
    response_body TEXT,
    error_message TEXT,
    attempts INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'success', 'failed', 'retrying'
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id);
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status);
CREATE INDEX idx_webhook_deliveries_created_at ON webhook_deliveries(created_at DESC);

COMMENT ON TABLE webhook_deliveries IS 'Webhook delivery attempts and results';

-- Email queue table
CREATE TABLE IF NOT EXISTS email_queue (
    id SERIAL PRIMARY KEY,
    recipient_email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body_html TEXT,
    body_plain TEXT,
    from_email VARCHAR(255),
    reply_to VARCHAR(255),
    cc TEXT[],
    bcc TEXT[],
    priority INTEGER DEFAULT 5,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sending', 'sent', 'failed'
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_email_queue_status ON email_queue(status);
CREATE INDEX idx_email_queue_priority ON email_queue(priority DESC);
CREATE INDEX idx_email_queue_created_at ON email_queue(created_at);

COMMENT ON TABLE email_queue IS 'Queue for outgoing emails';

-- API Keys table - REMOVED FROM BASE SCHEMA
-- This table is now created by migration 011_api_keys.sql
-- which has the proper schema with key_hash and key_prefix columns

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify tables exist (api_keys excluded - created in migration 011)
-- Check auth schema
SELECT
    'auth.' || table_name as full_table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'auth' AND table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'auth'
  AND table_name IN ('users')
UNION ALL
-- Check public schema
SELECT
    table_name as full_table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN (
    'user_profiles', 'roles', 'modules', 'login_history', 'user_sessions',
    'activity_logs', 'webhooks', 'webhook_deliveries', 'email_queue', 'user_module_permissions'
  )
ORDER BY full_table_name;
