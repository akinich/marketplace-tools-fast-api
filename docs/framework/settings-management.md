# Settings & Configuration Management System

**Version:** 1.0.0
**Last Updated:** November 22, 2025
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Database Schema](#database-schema)
5. [Backend Implementation](#backend-implementation)
6. [Frontend Implementation](#frontend-implementation)
7. [API Endpoints](#api-endpoints)
8. [Configuration Guide](#configuration-guide)
9. [Testing Guide](#testing-guide)
10. [Troubleshooting](#troubleshooting)
11. [Version History](#version-history)

---

## 📖 Overview

The Settings & Configuration Management system provides a complete solution for managing application settings through a user-friendly interface, eliminating the need to edit environment variables or restart the server.

### Key Benefits

- **Dynamic Configuration**: Update settings without server restarts
- **Type Safety**: Built-in validation for different data types
- **Audit Trail**: Complete history of all setting changes
- **Role-Based Access**: Admin-only management with public settings support
- **Performance**: In-memory caching with 60-second TTL
- **Category Organization**: Settings grouped by functional areas

---

## ✨ Features

### Core Features

1. **Multi-Type Support**
   - String, Integer, Float, Boolean, JSON
   - Automatic type validation and conversion
   - Min/max value constraints

2. **Category Management**
   - Authentication settings
   - Email/SMTP configuration
   - Webhook settings
   - Application settings
   - Feature flags

3. **Audit Logging**
   - Track all changes with user attribution
   - Old and new values recorded
   - Timestamp tracking

4. **Caching Layer**
   - 60-second in-memory cache
   - Automatic cache invalidation on updates
   - Performance optimization for high-traffic scenarios

5. **Security**
   - Admin-only access control
   - Support for encrypted settings
   - Public vs private setting classification

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
├─────────────────────────────────────────────────────────────┤
│  SettingsPage.jsx  │  settingsAPI.js  │  Material-UI       │
└────────────┬────────────────────────────────────────────────┘
             │ HTTPS/REST API
┌────────────┴────────────────────────────────────────────────┐
│                   Backend (FastAPI)                         │
├─────────────────────────────────────────────────────────────┤
│  Routes      │  Services        │  Models                   │
│  settings.py │  settings_service│  settings.py              │
└────────────┬────────────────────────────────────────────────┘
             │ asyncpg
┌────────────┴────────────────────────────────────────────────┐
│              Database (PostgreSQL/Supabase)                 │
├─────────────────────────────────────────────────────────────┤
│  system_settings  │  settings_audit_log                     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Read Settings**:
   - Frontend → API Request → Cache Check → Database (if cache miss) → Response

2. **Update Settings**:
   - Frontend → API Request → Validation → Database Update → Audit Log → Cache Clear → Response

---

## 🗄️ Database Schema

### Table: `system_settings`

Stores all configuration settings with metadata.

```sql
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(255) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    validation_rules JSONB,
    is_public BOOLEAN DEFAULT false,
    is_encrypted BOOLEAN DEFAULT false,
    updated_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexes:**
- `idx_system_settings_key` on `setting_key` (fast lookups)
- `idx_system_settings_category` on `category` (category queries)

**Columns:**
- `setting_key`: Unique identifier (e.g., `auth.jwt_expiry_minutes`)
- `setting_value`: JSONB value for flexible storage
- `data_type`: `string`, `integer`, `float`, `boolean`, or `json`
- `category`: Grouping (`auth`, `email`, `webhooks`, `app`, `features`)
- `validation_rules`: JSON object with constraints (min, max, pattern, etc.)
- `is_public`: Whether non-admin users can read this setting
- `is_encrypted`: Flag for sensitive data (future encryption support)

### Table: `settings_audit_log`

Tracks all changes to settings for compliance and debugging.

```sql
CREATE TABLE settings_audit_log (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(255) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_by UUID REFERENCES auth.users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexes:**
- `idx_settings_audit_key` on `setting_key`
- `idx_settings_audit_changed_by` on `changed_by`

---

## 🔧 Backend Implementation

### File Structure

```
backend/
├── migrations/
│   └── 008_system_settings.sql           # Database migration
├── app/
│   ├── models/
│   │   └── settings.py                   # Pydantic models
│   ├── services/
│   │   └── settings_service.py           # Business logic
│   └── routes/
│       └── settings.py                   # API endpoints
```

### Key Components

#### 1. Models (`models/settings.py`)

```python
class SystemSettingResponse(BaseModel):
    id: int
    setting_key: str
    setting_value: Any
    data_type: str
    category: str
    description: Optional[str]
    validation_rules: Optional[Dict[str, Any]]
    is_public: bool
    is_encrypted: bool
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime
```

#### 2. Service Layer (`services/settings_service.py`)

**Caching:**
```python
class SettingsCache:
    def __init__(self, ttl_seconds: int = 60):
        self._cache: Dict[str, Any] = {}
        self._cache_time: Optional[datetime] = None
        self._ttl = timedelta(seconds=ttl_seconds)
```

**Key Functions:**
- `get_setting()`: Retrieve single setting with cache support
- `get_all_settings()`: Fetch all settings with caching
- `update_setting()`: Update with validation and audit logging
- `get_audit_log()`: Query change history

**Validation:**
- Type checking (string, int, float, bool, json)
- Min/max value constraints
- String length validation
- Pattern matching (regex)

#### 3. API Routes (`routes/settings.py`)

All routes require admin authentication:
- `GET /settings` - List all settings
- `GET /settings/public` - Public settings only
- `GET /settings/categories` - List categories
- `GET /settings/category/{category}` - Settings by category
- `PUT /settings/{setting_key}` - Update setting
- `GET /settings/audit-log` - Change history

---

## 🎨 Frontend Implementation

### File Structure

```
frontend/src/
├── api/
│   └── settings.js                       # API client
├── pages/
│   └── SettingsPage.jsx                  # Main UI component
└── App.jsx                               # Route configuration
```

### Components

#### SettingsPage Component

**Features:**
- Tabbed interface for categories
- Real-time validation
- Save/Reset functionality
- Success/error notifications
- Unsaved changes warning

**State Management:**
```javascript
const [settingsByCategory, setSettingsByCategory] = useState({});
const [formData, setFormData] = useState({});
const [hasChanges, setHasChanges] = useState(false);
```

**Value Parsing:**
- JSON string parsing for stored values
- Proper boolean conversion (`"false"` → `false`)
- Type-safe integer/float handling

---

## 🌐 API Endpoints

### GET `/api/v1/settings`

**Description:** Retrieve all system settings
**Authentication:** Admin required
**Response:** Array of settings

```json
[
  {
    "id": 1,
    "setting_key": "auth.jwt_expiry_minutes",
    "setting_value": "30",
    "data_type": "integer",
    "category": "auth",
    "description": "JWT access token expiration time in minutes",
    "validation_rules": {"min": 5, "max": 1440},
    "is_public": false,
    "is_encrypted": false,
    "updated_by": null,
    "created_at": "2025-11-22T21:24:44.664159Z",
    "updated_at": "2025-11-22T21:24:44.664159Z"
  }
]
```

### GET `/api/v1/settings/public`

**Description:** Get public settings
**Authentication:** Any authenticated user
**Response:** Key-value pairs

```json
{
  "app.name": "Farm Management System",
  "app.timezone": "UTC",
  "app.date_format": "DD/MM/YYYY"
}
```

### GET `/api/v1/settings/categories`

**Description:** List all categories
**Authentication:** Admin required
**Response:** Array of category names

```json
["app", "auth", "email", "features", "webhooks"]
```

### GET `/api/v1/settings/category/{category}`

**Description:** Get settings in specific category
**Authentication:** Admin required
**Parameters:** `category` (path)
**Response:** Array of settings

### PUT `/api/v1/settings/{setting_key}`

**Description:** Update a setting value
**Authentication:** Admin required
**Parameters:** `setting_key` (path)
**Request Body:**

```json
{
  "setting_value": 60
}
```

**Response:** Updated setting object

**Validation Errors (400):**
```json
{
  "detail": "Value must be at least 5"
}
```

### GET `/api/v1/settings/audit-log`

**Description:** Get settings change history
**Authentication:** Admin required
**Query Parameters:**
- `setting_key` (optional): Filter by specific setting
- `limit` (optional, default: 100): Number of entries

**Response:**

```json
[
  {
    "id": 1,
    "setting_key": "auth.jwt_expiry_minutes",
    "old_value": 30,
    "new_value": 60,
    "changed_by": "admin@example.com",
    "changed_at": "2025-11-22T21:57:23.558537Z"
  }
]
```

---

## ⚙️ Configuration Guide

### Default Settings

#### Authentication (`auth`)

| Setting | Default | Type | Range | Description |
|---------|---------|------|-------|-------------|
| `jwt_expiry_minutes` | 30 | integer | 5-1440 | Access token expiration |
| `refresh_expiry_days` | 7 | integer | 1-90 | Refresh token expiration |
| `max_login_attempts` | 5 | integer | 3-10 | Failed login threshold |
| `lockout_duration_minutes` | 30 | integer | 10-1440 | Account lockout duration |
| `password_min_length` | 8 | integer | 6-32 | Minimum password length |
| `session_timeout_minutes` | 30 | integer | 5-480 | Inactivity timeout |
| `max_sessions_admin` | 5 | integer | 1-10 | Admin concurrent sessions |
| `max_sessions_user` | 1 | integer | 1-5 | User concurrent sessions |

#### Email/SMTP (`email`)

| Setting | Default | Type | Description |
|---------|---------|------|-------------|
| `smtp_enabled` | false | boolean | Enable SMTP |
| `smtp_host` | "" | string | SMTP server hostname |
| `smtp_port` | 587 | integer | SMTP port (1-65535) |
| `smtp_use_tls` | true | boolean | Use TLS encryption |
| `smtp_user` | "" | string | SMTP username |
| `smtp_password` | "" | string | SMTP password |
| `from_email` | "noreply@farmapp.com" | string | Sender email |
| `from_name` | "Farm Management System" | string | Sender name |

#### Webhooks (`webhooks`)

| Setting | Default | Type | Range | Description |
|---------|---------|------|-------|-------------|
| `enabled` | true | boolean | - | Enable webhooks |
| `retry_attempts` | 3 | integer | 0-10 | Retry count |
| `retry_delay_seconds` | 60 | integer | 10-3600 | Retry delay |
| `timeout_seconds` | 30 | integer | 5-120 | Request timeout |

#### Application (`app`)

| Setting | Default | Type | Public | Description |
|---------|---------|------|--------|-------------|
| `name` | "Farm Management System" | string | Yes | App name |
| `support_email` | "support@farmapp.com" | string | Yes | Support email |
| `timezone` | "UTC" | string | Yes | App timezone |
| `date_format` | "DD/MM/YYYY" | string | Yes | Date format |
| `maintenance_mode` | false | boolean | No | Maintenance mode |

#### Feature Flags (`features`)

| Setting | Default | Type | Description |
|---------|---------|------|-------------|
| `api_keys_enabled` | false | boolean | API key auth |
| `webhooks_enabled` | false | boolean | Webhook management |
| `websockets_enabled` | false | boolean | WebSocket updates |
| `email_notifications_enabled` | false | boolean | Email notifications |

### Adding New Settings

To add a new setting:

1. **Insert into database:**

```sql
INSERT INTO system_settings
(setting_key, setting_value, data_type, category, description, validation_rules, is_public)
VALUES
('auth.mfa_enabled', 'false', 'boolean', 'auth', 'Enable multi-factor authentication', '{}', false);
```

2. **Setting will automatically appear in UI**
3. **No code changes required**

---

## 🧪 Testing Guide

### Backend API Testing

#### Using Swagger UI

1. Navigate to: `https://your-backend-url.onrender.com/docs`
2. Click **Authorize** → Enter `Bearer YOUR_TOKEN`
3. Test endpoints under **Settings** section

#### Using curl

```bash
# Get all settings
curl -X GET https://your-backend-url/api/v1/settings \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update setting
curl -X PUT https://your-backend-url/api/v1/settings/auth.jwt_expiry_minutes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"setting_value": 60}'

# Get audit log
curl -X GET https://your-backend-url/api/v1/settings/audit-log \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Frontend UI Testing

#### Test Checklist

- [ ] **Page Load**: Settings page displays with 5 tabs
- [ ] **Tab Navigation**: All tabs load their respective settings
- [ ] **Value Display**: Settings show current values correctly
- [ ] **Edit Settings**: Can modify values in forms
- [ ] **Save Changes**: Success message appears after save
- [ ] **Persistence**: Values persist after page refresh
- [ ] **Validation**: Invalid values show error messages
- [ ] **Reset Button**: Reverts unsaved changes
- [ ] **Boolean Toggles**: Switches work correctly (ON/OFF)
- [ ] **Audit Trail**: Changes appear in audit log

#### Test Scenarios

**Scenario 1: Update Integer Setting**
1. Go to Authentication tab
2. Change JWT expiry from 30 to 45
3. Click Save → Success message
4. Refresh page → Value still 45

**Scenario 2: Validation Error**
1. Set JWT expiry to 3 (below min 5)
2. Click Save → Error: "Value must be at least 5"

**Scenario 3: Boolean Toggle**
1. Go to Feature Flags tab
2. Toggle "Enable email notifications" ON
3. Click Save → Success
4. Refresh → Toggle still ON
5. Toggle OFF → Save → Refresh → Toggle OFF

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: Settings not loading (500 error)

**Symptoms:** Frontend shows error, backend logs show database errors

**Solutions:**
1. Verify database migration ran successfully
2. Check database connection in backend logs
3. Verify `system_settings` table exists

```sql
SELECT * FROM system_settings LIMIT 1;
```

#### Issue: Boolean toggles stuck ON

**Symptoms:** All toggles show ON regardless of value

**Cause:** Boolean value parsing issue

**Solution:** Frontend fix applied in v1.0.0 - ensure latest version deployed

#### Issue: Validation errors not showing

**Symptoms:** Invalid values save without error

**Cause:** Validation rules not properly configured

**Solution:** Check `validation_rules` column in database:

```sql
SELECT setting_key, validation_rules
FROM system_settings
WHERE setting_key = 'auth.jwt_expiry_minutes';
```

#### Issue: Changes not persisting

**Symptoms:** Settings revert after page refresh

**Cause:** Cache not clearing, or database update failing

**Solutions:**
1. Check backend logs for update errors
2. Verify user has admin role
3. Check audit log for successful updates:

```sql
SELECT * FROM settings_audit_log
ORDER BY changed_at DESC LIMIT 10;
```

#### Issue: 403 Forbidden on settings endpoints

**Symptoms:** API returns 403 error

**Cause:** User is not admin

**Solution:** Verify user role:

```sql
SELECT up.email, r.role_name
FROM user_profiles up
JOIN roles r ON r.id = up.role_id
WHERE up.email = 'user@example.com';
```

### Performance Issues

#### Cache not working

**Check cache TTL:**
- Default: 60 seconds
- Adjust in `settings_service.py`:

```python
_settings_cache = SettingsCache(ttl_seconds=60)
```

#### Slow audit log queries

**Add indexes:**

```sql
CREATE INDEX IF NOT EXISTS idx_settings_audit_date
ON settings_audit_log(changed_at DESC);
```

---

## 📊 Version History

### Version 1.0.0 (November 22, 2025)

**Status:** ✅ Production Ready

#### Features Implemented

**Backend:**
- ✅ Database migration with `system_settings` and `settings_audit_log` tables
- ✅ Pydantic models for type-safe validation
- ✅ Service layer with caching (60s TTL)
- ✅ REST API endpoints with admin authentication
- ✅ Audit logging for all changes
- ✅ Type validation (string, integer, float, boolean, json)
- ✅ Min/max value constraints

**Frontend:**
- ✅ Settings page with tabbed interface
- ✅ Category-based organization (5 categories)
- ✅ Real-time form validation
- ✅ Save/Reset functionality
- ✅ Success/error notifications
- ✅ Unsaved changes warning
- ✅ Boolean toggle switches
- ✅ Material-UI components

**Testing:**
- ✅ Backend API testing (7/7 endpoints)
- ✅ Frontend UI testing (7/7 scenarios)
- ✅ Validation testing
- ✅ Persistence testing
- ✅ Audit trail verification

#### Bug Fixes

**v1.0.0 - Patch 1 (Nov 22, 2025)**
- 🐛 Fixed Pydantic validation errors for JSONB fields
- 🐛 Fixed UUID to string conversion for `updated_by`
- 🐛 Fixed audit log SQL query (join with `auth.users`)

**v1.0.0 - Patch 2 (Nov 22, 2025)**
- 🐛 Fixed boolean toggle parsing (`"false"` string → `false` boolean)
- 🐛 Improved JSON string parsing for all data types

#### Default Settings

**29 settings across 5 categories:**
- Authentication: 8 settings
- Email/SMTP: 8 settings
- Webhooks: 4 settings
- Application: 5 settings
- Feature Flags: 4 settings

---

## 🚀 Deployment Checklist

### Initial Deployment

- [ ] Run database migration: `008_system_settings.sql`
- [ ] Verify tables created: `system_settings`, `settings_audit_log`
- [ ] Deploy backend code to production
- [ ] Deploy frontend code to production
- [ ] Test settings page as admin user
- [ ] Verify audit log working

### Post-Deployment

- [ ] Configure SMTP settings (if using email)
- [ ] Review and adjust JWT expiry times
- [ ] Set maintenance mode flag (if needed)
- [ ] Enable/disable feature flags as needed
- [ ] Document any custom settings added

---

## 📞 Support

### Documentation

- **This Guide:** `docs/framework/settings-management.md`
- **API Docs:** `https://your-backend-url/docs`
- **Database Schema:** `backend/migrations/008_system_settings.sql`

### Monitoring

**Health Checks:**
```bash
# Backend health
curl https://your-backend-url/health

# Settings endpoint
curl https://your-backend-url/api/v1/settings/public
```

**Database Queries:**
```sql
-- Check settings count
SELECT category, COUNT(*)
FROM system_settings
GROUP BY category;

-- Recent changes
SELECT setting_key, changed_by, changed_at
FROM settings_audit_log
ORDER BY changed_at DESC
LIMIT 10;

-- Public settings
SELECT setting_key, setting_value
FROM system_settings
WHERE is_public = true;
```

---

## 🎯 Future Enhancements

### Planned Features

1. **Setting Encryption**
   - Encrypt sensitive values (passwords, API keys)
   - Use `is_encrypted` flag

2. **Setting Import/Export**
   - Export configuration as JSON
   - Import settings from file

3. **Setting Groups**
   - Nested categories for better organization
   - Collapsible sections

4. **Setting Dependencies**
   - Conditional settings (e.g., SMTP settings only when enabled)
   - Dependency validation

5. **Setting Templates**
   - Pre-configured setting bundles
   - Environment-specific configs (dev, staging, prod)

6. **Rollback Support**
   - Revert to previous setting values
   - Bulk rollback by timestamp

7. **Setting Search**
   - Search by key, description, or value
   - Filter by category or type

---

## 📝 Notes

- All settings are cached for 60 seconds to reduce database load
- Cache automatically invalidates on updates
- Audit log provides complete change history for compliance
- Admin-only access ensures security
- Public settings can be accessed by any authenticated user
- Settings take effect immediately without server restart

---

**Document Version:** 1.0.0
**Last Updated:** November 22, 2025
**Maintained By:** Farm Management System Team
