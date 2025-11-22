# Migration 011: API Key Management - Changelog

## Version: 1.0.0
## Date: 2025-11-22
## Author: Claude

---

## Overview
Implements API Key authentication system for programmatic access with scope-based permissions and usage tracking.

---

## Changes Made

### New Tables

#### 1. `api_keys`
**Purpose:** Store API keys with hashed values and metadata

**Columns:**
- `id` (SERIAL PRIMARY KEY) - Unique identifier
- `user_id` (UUID) - Foreign key to auth.users
- `key_hash` (VARCHAR(255)) - Bcrypt hash of the API key
- `key_prefix` (VARCHAR(20)) - First 12 chars for display (e.g., "sk_live_abc...")
- `name` (VARCHAR(255)) - User-friendly name for the key
- `description` (TEXT) - Optional description
- `scopes` (TEXT[]) - Array of permission scopes (e.g., ["inventory:read", "tickets:write"])
- `is_active` (BOOLEAN) - Whether the key is currently active
- `expires_at` (TIMESTAMP WITH TIME ZONE) - Optional expiration date
- `last_used_at` (TIMESTAMP WITH TIME ZONE) - Last time the key was used
- `created_at` (TIMESTAMP WITH TIME ZONE) - Creation timestamp
- `revoked_at` (TIMESTAMP WITH TIME ZONE) - When the key was revoked (if applicable)

**Indexes:**
- `idx_api_keys_user_id` - Fast lookup by user
- `idx_api_keys_key_hash` - Fast lookup during authentication
- `idx_api_keys_is_active` - Filter active keys efficiently

#### 2. `api_key_usage`
**Purpose:** Log all API key usage for auditing and analytics

**Columns:**
- `id` (SERIAL PRIMARY KEY) - Unique identifier
- `api_key_id` (INTEGER) - Foreign key to api_keys
- `endpoint` (VARCHAR(255)) - API endpoint accessed
- `method` (VARCHAR(10)) - HTTP method (GET, POST, etc.)
- `status_code` (INTEGER) - HTTP response status
- `ip_address` (INET) - Client IP address
- `user_agent` (TEXT) - Client user agent
- `response_time_ms` (INTEGER) - Response time in milliseconds
- `created_at` (TIMESTAMP WITH TIME ZONE) - Request timestamp

**Indexes:**
- `idx_api_key_usage_key_id` - Fast lookup by API key
- `idx_api_key_usage_created_at` - Efficient time-based queries

---

## Security Features

1. **Password-like Hashing:** API keys are hashed with bcrypt before storage
2. **One-time Display:** Full key is only shown once during creation
3. **Scope-based Permissions:** Fine-grained access control
4. **Usage Tracking:** Complete audit trail of API key usage
5. **Expiration Support:** Optional time-based key expiration
6. **Revocation:** Keys can be deactivated without deletion

---

## Migration Steps

1. Run this migration in Supabase SQL editor
2. Verify tables are created with verification queries
3. Check indexes are in place
4. Test with backend implementation

---

## Rollback Instructions

```sql
-- WARNING: This will delete all API keys and usage data
DROP TABLE IF EXISTS api_key_usage CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
```

---

## Dependencies

- Requires `auth.users` table (from Supabase Auth)
- No other application tables required

---

## Breaking Changes

None - This is a new feature addition.

---

## Next Steps

1. Deploy backend API key service and routes
2. Implement frontend API key management UI
3. Add API key authentication to protected endpoints
4. Create user documentation

---

## Testing Checklist

- [ ] Tables created successfully
- [ ] Indexes exist and are functional
- [ ] Foreign key constraints work (cascade delete)
- [ ] Can insert test API key record
- [ ] Can insert usage log record
- [ ] Verification queries return expected results
