-- ============================================================================
-- Password Reset Tokens Table
-- Version: 1.1.2
-- Created: 2025-11-17
-- Description: Stores password reset tokens for email-based password recovery
-- ============================================================================

-- Create password_reset_tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    used_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_password_reset_tokens_expires_at ON password_reset_tokens(expires_at);

-- Add comments
COMMENT ON TABLE password_reset_tokens IS 'Stores password reset tokens with expiry';
COMMENT ON COLUMN password_reset_tokens.token IS 'Unique token sent in reset email';
COMMENT ON COLUMN password_reset_tokens.expires_at IS 'Token expiry timestamp (typically 1 hour)';
COMMENT ON COLUMN password_reset_tokens.used IS 'Whether token has been used';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON password_reset_tokens TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE password_reset_tokens_id_seq TO authenticated;

-- ============================================================================
-- Cleanup Job (Optional - run periodically to delete expired tokens)
-- ============================================================================
-- DELETE FROM password_reset_tokens WHERE expires_at < NOW() AND used = TRUE;
