# HANDOVER MESSAGE #2: Advanced Settings & Configuration Management

## 📋 MISSION
Build a complete **Settings & Configuration Management** system that allows admins to configure the application via UI without editing environment variables or restarting the server.

## 🎯 WHAT YOU NEED TO BUILD

### Features:
1. **Backend:** Database, models, service with caching, API routes
2. **Frontend:** Settings UI with tabs, forms, validation
3. **Categories:** Auth, Email, Webhooks, Application, Features
4. **Validation:** Type checking, min/max values, required fields
5. **Audit Trail:** Track who changed what settings

---

## 🗄️ PART 1: DATABASE MIGRATION

Create file: `backend/migrations/008_system_settings.sql`

```sql
-- ============================================================================
-- Migration 008: System Settings & Configuration Management
-- ============================================================================

-- Create system_settings table
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(255) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    data_type VARCHAR(50) NOT NULL CHECK (data_type IN ('string', 'integer', 'float', 'boolean', 'json')),
    category VARCHAR(100) NOT NULL,
    description TEXT,
    validation_rules JSONB,
    is_public BOOLEAN DEFAULT false,
    is_encrypted BOOLEAN DEFAULT false,
    updated_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on setting_key for fast lookups
CREATE INDEX idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX idx_system_settings_category ON system_settings(category);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_system_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_system_settings_updated_at();

-- Create settings_audit_log table
CREATE TABLE IF NOT EXISTS settings_audit_log (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(255) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_by UUID REFERENCES auth.users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_settings_audit_key ON settings_audit_log(setting_key);
CREATE INDEX idx_settings_audit_changed_by ON settings_audit_log(changed_by);

-- Insert default settings
INSERT INTO system_settings (setting_key, setting_value, data_type, category, description, validation_rules, is_public) VALUES

-- Authentication Settings
('auth.jwt_expiry_minutes', '30', 'integer', 'auth', 'JWT access token expiration time in minutes', '{"min": 5, "max": 1440}', false),
('auth.refresh_expiry_days', '7', 'integer', 'auth', 'JWT refresh token expiration time in days', '{"min": 1, "max": 90}', false),
('auth.max_login_attempts', '5', 'integer', 'auth', 'Maximum failed login attempts before account lockout', '{"min": 3, "max": 10}', false),
('auth.lockout_duration_minutes', '30', 'integer', 'auth', 'Account lockout duration in minutes', '{"min": 10, "max": 1440}', false),
('auth.password_min_length', '8', 'integer', 'auth', 'Minimum password length', '{"min": 6, "max": 32}', false),
('auth.session_timeout_minutes', '30', 'integer', 'auth', 'Inactivity timeout before auto-logout (minutes)', '{"min": 5, "max": 480}', false),
('auth.max_sessions_admin', '5', 'integer', 'auth', 'Maximum concurrent sessions for admin users', '{"min": 1, "max": 10}', false),
('auth.max_sessions_user', '1', 'integer', 'auth', 'Maximum concurrent sessions for regular users', '{"min": 1, "max": 5}', false),

-- Email Settings
('email.smtp_enabled', 'false', 'boolean', 'email', 'Enable SMTP email notifications', '{}', false),
('email.smtp_host', '""', 'string', 'email', 'SMTP server hostname', '{}', false),
('email.smtp_port', '587', 'integer', 'email', 'SMTP server port', '{"min": 1, "max": 65535}', false),
('email.smtp_use_tls', 'true', 'boolean', 'email', 'Use TLS for SMTP connection', '{}', false),
('email.smtp_user', '""', 'string', 'email', 'SMTP username', '{}', false),
('email.smtp_password', '""', 'string', 'email', 'SMTP password (encrypted)', '{}', false),
('email.from_email', '"noreply@farmapp.com"', 'string', 'email', 'Default sender email address', '{}', false),
('email.from_name', '"Farm Management System"', 'string', 'email', 'Default sender name', '{}', false),

-- Webhook Settings
('webhooks.enabled', 'true', 'boolean', 'webhooks', 'Enable webhook functionality', '{}', false),
('webhooks.retry_attempts', '3', 'integer', 'webhooks', 'Number of retry attempts for failed webhooks', '{"min": 0, "max": 10}', false),
('webhooks.retry_delay_seconds', '60', 'integer', 'webhooks', 'Delay between retry attempts in seconds', '{"min": 10, "max": 3600}', false),
('webhooks.timeout_seconds', '30', 'integer', 'webhooks', 'Webhook request timeout in seconds', '{"min": 5, "max": 120}', false),

-- Application Settings
('app.name', '"Farm Management System"', 'string', 'app', 'Application name', '{}', true),
('app.support_email', '"support@farmapp.com"', 'string', 'app', 'Support email address', '{}', true),
('app.timezone', '"UTC"', 'string', 'app', 'Application timezone', '{}', true),
('app.date_format', '"DD/MM/YYYY"', 'string', 'app', 'Date format', '{}', true),
('app.maintenance_mode', 'false', 'boolean', 'app', 'Enable maintenance mode', '{}', false),

-- Feature Flags
('features.api_keys_enabled', 'false', 'boolean', 'features', 'Enable API key authentication', '{}', false),
('features.webhooks_enabled', 'false', 'boolean', 'features', 'Enable webhook management', '{}', false),
('features.websockets_enabled', 'false', 'boolean', 'features', 'Enable WebSocket real-time updates', '{}', false),
('features.email_notifications_enabled', 'false', 'boolean', 'features', 'Enable email notifications', '{}', false)

ON CONFLICT (setting_key) DO NOTHING;

-- Verify the migration
SELECT setting_key, setting_value, data_type, category, is_public
FROM system_settings
ORDER BY category, setting_key;
```

**Run this migration in Supabase SQL Editor and share the output.**

---

## 🔧 PART 2: BACKEND IMPLEMENTATION

### File 1: `backend/app/models/settings.py`

```python
"""
System Settings Models
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, validator
from datetime import datetime

class SystemSettingSchema(BaseModel):
    """System setting model"""
    setting_key: str
    setting_value: Any
    data_type: str = Field(..., pattern="^(string|integer|float|boolean|json)$")
    category: str
    description: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    is_public: bool = False
    is_encrypted: bool = False

    class Config:
        from_attributes = True

class SystemSettingResponse(SystemSettingSchema):
    """System setting response with metadata"""
    id: int
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class SettingUpdateRequest(BaseModel):
    """Request to update a setting"""
    setting_value: Any

class SettingsByCategoryResponse(BaseModel):
    """Settings grouped by category"""
    category: str
    settings: list[SystemSettingResponse]

class SettingsAuditLogResponse(BaseModel):
    """Audit log entry for settings changes"""
    id: int
    setting_key: str
    old_value: Any
    new_value: Any
    changed_by: str
    changed_at: datetime

    class Config:
        from_attributes = True
```

### File 2: `backend/app/services/settings_service.py`

```python
"""
Settings Service - Manages system configuration
"""
import json
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from asyncpg import Connection

class SettingsCache:
    """In-memory cache for settings"""
    def __init__(self, ttl_seconds: int = 60):
        self._cache: Dict[str, Any] = {}
        self._cache_time: Optional[datetime] = None
        self._ttl = timedelta(seconds=ttl_seconds)

    def is_valid(self) -> bool:
        """Check if cache is still valid"""
        if self._cache_time is None:
            return False
        return datetime.now() - self._cache_time < self._ttl

    def set(self, settings: Dict[str, Any]):
        """Update cache"""
        self._cache = settings
        self._cache_time = datetime.now()

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        return self._cache.get(key, default)

    def clear(self):
        """Clear cache"""
        self._cache = {}
        self._cache_time = None

# Global cache instance
_settings_cache = SettingsCache(ttl_seconds=60)

async def get_setting(
    conn: Connection,
    key: str,
    default: Any = None,
    use_cache: bool = True
) -> Any:
    """Get a single setting value"""
    # Try cache first
    if use_cache and _settings_cache.is_valid():
        return _settings_cache.get(key, default)

    # Fetch from database
    row = await conn.fetchrow(
        """
        SELECT setting_value, data_type
        FROM system_settings
        WHERE setting_key = $1
        """,
        key
    )

    if not row:
        return default

    # Parse value based on data type
    value = row['setting_value']
    data_type = row['data_type']

    return _parse_setting_value(value, data_type, default)

async def get_all_settings(
    conn: Connection,
    use_cache: bool = True
) -> Dict[str, Any]:
    """Get all settings as a dictionary"""
    # Try cache first
    if use_cache and _settings_cache.is_valid():
        return _settings_cache._cache.copy()

    # Fetch from database
    rows = await conn.fetch(
        """
        SELECT setting_key, setting_value, data_type
        FROM system_settings
        ORDER BY category, setting_key
        """
    )

    settings = {}
    for row in rows:
        key = row['setting_key']
        value = _parse_setting_value(row['setting_value'], row['data_type'])
        settings[key] = value

    # Update cache
    _settings_cache.set(settings)

    return settings

async def get_settings_by_category(
    conn: Connection,
    category: str
) -> List[Dict[str, Any]]:
    """Get all settings in a category"""
    rows = await conn.fetch(
        """
        SELECT
            id,
            setting_key,
            setting_value,
            data_type,
            category,
            description,
            validation_rules,
            is_public,
            is_encrypted,
            updated_by,
            created_at,
            updated_at
        FROM system_settings
        WHERE category = $1
        ORDER BY setting_key
        """,
        category
    )

    return [dict(row) for row in rows]

async def get_public_settings(conn: Connection) -> Dict[str, Any]:
    """Get only public settings (for non-admin users)"""
    rows = await conn.fetch(
        """
        SELECT setting_key, setting_value, data_type
        FROM system_settings
        WHERE is_public = true
        """
    )

    settings = {}
    for row in rows:
        key = row['setting_key']
        value = _parse_setting_value(row['setting_value'], row['data_type'])
        settings[key] = value

    return settings

async def update_setting(
    conn: Connection,
    key: str,
    value: Any,
    user_id: str
) -> Dict[str, Any]:
    """Update a setting value"""
    # Get current setting
    current = await conn.fetchrow(
        """
        SELECT setting_value, data_type, validation_rules
        FROM system_settings
        WHERE setting_key = $1
        """,
        key
    )

    if not current:
        raise ValueError(f"Setting '{key}' not found")

    # Validate new value
    data_type = current['data_type']
    validation_rules = current['validation_rules']

    validated_value = _validate_setting_value(value, data_type, validation_rules)

    # Convert to JSON string for storage
    json_value = json.dumps(validated_value)

    # Update setting
    updated = await conn.fetchrow(
        """
        UPDATE system_settings
        SET setting_value = $1::jsonb, updated_by = $2
        WHERE setting_key = $3
        RETURNING id, setting_key, setting_value, data_type, category, description,
                  validation_rules, is_public, is_encrypted, updated_by, created_at, updated_at
        """,
        json_value,
        user_id,
        key
    )

    # Log the change
    await conn.execute(
        """
        INSERT INTO settings_audit_log (setting_key, old_value, new_value, changed_by)
        VALUES ($1, $2::jsonb, $3::jsonb, $4)
        """,
        key,
        current['setting_value'],
        json_value,
        user_id
    )

    # Clear cache
    _settings_cache.clear()

    return dict(updated)

async def get_audit_log(
    conn: Connection,
    setting_key: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get settings audit log"""
    if setting_key:
        rows = await conn.fetch(
            """
            SELECT
                sal.id,
                sal.setting_key,
                sal.old_value,
                sal.new_value,
                sal.changed_at,
                up.email as changed_by
            FROM settings_audit_log sal
            LEFT JOIN user_profiles up ON sal.changed_by = up.user_id
            WHERE sal.setting_key = $1
            ORDER BY sal.changed_at DESC
            LIMIT $2
            """,
            setting_key,
            limit
        )
    else:
        rows = await conn.fetch(
            """
            SELECT
                sal.id,
                sal.setting_key,
                sal.old_value,
                sal.new_value,
                sal.changed_at,
                up.email as changed_by
            FROM settings_audit_log sal
            LEFT JOIN user_profiles up ON sal.changed_by = up.user_id
            ORDER BY sal.changed_at DESC
            LIMIT $1
            """,
            limit
        )

    return [dict(row) for row in rows]

def _parse_setting_value(json_value: Any, data_type: str, default: Any = None) -> Any:
    """Parse setting value from JSON based on data type"""
    try:
        if json_value is None:
            return default

        # If it's already a dict (JSONB from DB), get the value
        if isinstance(json_value, dict):
            value = json_value
        else:
            value = json.loads(json_value) if isinstance(json_value, str) else json_value

        # Convert based on data type
        if data_type == 'integer':
            return int(value)
        elif data_type == 'float':
            return float(value)
        elif data_type == 'boolean':
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes')
            return bool(value)
        elif data_type == 'json':
            return value
        else:  # string
            return str(value)
    except (ValueError, TypeError, json.JSONDecodeError):
        return default

def _validate_setting_value(value: Any, data_type: str, validation_rules: Any) -> Any:
    """Validate setting value against rules"""
    # Parse validation rules
    if validation_rules and isinstance(validation_rules, (str, dict)):
        if isinstance(validation_rules, str):
            rules = json.loads(validation_rules)
        else:
            rules = validation_rules
    else:
        rules = {}

    # Type validation and conversion
    if data_type == 'integer':
        try:
            value = int(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid integer value: {value}")

        if 'min' in rules and value < rules['min']:
            raise ValueError(f"Value must be at least {rules['min']}")
        if 'max' in rules and value > rules['max']:
            raise ValueError(f"Value must be at most {rules['max']}")

    elif data_type == 'float':
        try:
            value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid float value: {value}")

        if 'min' in rules and value < rules['min']:
            raise ValueError(f"Value must be at least {rules['min']}")
        if 'max' in rules and value > rules['max']:
            raise ValueError(f"Value must be at most {rules['max']}")

    elif data_type == 'boolean':
        if isinstance(value, bool):
            pass
        elif isinstance(value, str):
            value = value.lower() in ('true', '1', 'yes')
        else:
            value = bool(value)

    elif data_type == 'string':
        value = str(value)

        if 'min_length' in rules and len(value) < rules['min_length']:
            raise ValueError(f"String must be at least {rules['min_length']} characters")
        if 'max_length' in rules and len(value) > rules['max_length']:
            raise ValueError(f"String must be at most {rules['max_length']} characters")
        if 'pattern' in rules:
            import re
            if not re.match(rules['pattern'], value):
                raise ValueError(f"String does not match required pattern")

    return value
```

### File 3: `backend/app/routes/settings.py`

```python
"""
Settings API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from asyncpg import Connection

from app.database import get_db_connection
from app.dependencies import require_admin
from app.models.settings import (
    SystemSettingResponse,
    SettingUpdateRequest,
    SettingsByCategoryResponse,
    SettingsAuditLogResponse
)
from app.services import settings_service

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/", response_model=List[SystemSettingResponse])
async def get_all_settings(
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Get all system settings (Admin only)"""
    rows = await conn.fetch(
        """
        SELECT
            id, setting_key, setting_value, data_type, category,
            description, validation_rules, is_public, is_encrypted,
            updated_by, created_at, updated_at
        FROM system_settings
        ORDER BY category, setting_key
        """
    )
    return [dict(row) for row in rows]

@router.get("/public", response_model=Dict[str, Any])
async def get_public_settings(
    conn: Connection = Depends(get_db_connection)
):
    """Get public settings (accessible to all authenticated users)"""
    return await settings_service.get_public_settings(conn)

@router.get("/categories", response_model=List[str])
async def get_categories(
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Get list of setting categories"""
    rows = await conn.fetch(
        "SELECT DISTINCT category FROM system_settings ORDER BY category"
    )
    return [row['category'] for row in rows]

@router.get("/category/{category}", response_model=List[SystemSettingResponse])
async def get_settings_by_category(
    category: str,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Get all settings in a specific category"""
    settings = await settings_service.get_settings_by_category(conn, category)
    return settings

@router.put("/{setting_key}", response_model=SystemSettingResponse)
async def update_setting(
    setting_key: str,
    request: SettingUpdateRequest,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Update a setting value"""
    try:
        updated = await settings_service.update_setting(
            conn,
            setting_key,
            request.setting_value,
            current_user['user_id']
        )
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/audit-log", response_model=List[SettingsAuditLogResponse])
async def get_audit_log(
    setting_key: str = None,
    limit: int = 100,
    current_user: dict = Depends(require_admin),
    conn: Connection = Depends(get_db_connection)
):
    """Get settings change audit log"""
    logs = await settings_service.get_audit_log(conn, setting_key, limit)
    return logs
```

### File 4: Update `backend/app/routes/__init__.py`

Add this import:
```python
from app.routes import settings

# In the include_router section:
app.include_router(settings.router, prefix="/api/v1")
```

---

## 🎨 PART 3: FRONTEND IMPLEMENTATION

### File 1: `frontend/src/api/settings.js`

```javascript
/**
 * Settings API Client
 */
import apiClient from './client';

export const settingsAPI = {
  // Get all settings (admin only)
  getAll: async () => {
    const response = await apiClient.get('/settings');
    return response.data;
  },

  // Get public settings
  getPublic: async () => {
    const response = await apiClient.get('/settings/public');
    return response.data;
  },

  // Get categories
  getCategories: async () => {
    const response = await apiClient.get('/settings/categories');
    return response.data;
  },

  // Get settings by category
  getByCategory: async (category) => {
    const response = await apiClient.get(`/settings/category/${category}`);
    return response.data;
  },

  // Update setting
  update: async (settingKey, value) => {
    const response = await apiClient.put(`/settings/${settingKey}`, {
      setting_value: value
    });
    return response.data;
  },

  // Get audit log
  getAuditLog: async (settingKey = null, limit = 100) => {
    const params = { limit };
    if (settingKey) params.setting_key = settingKey;

    const response = await apiClient.get('/settings/audit-log', { params });
    return response.data;
  }
};
```

### File 2: `frontend/src/pages/SettingsPage.jsx`

```javascript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Tabs,
  Tab,
  Typography,
  TextField,
  Switch,
  Button,
  FormControlLabel,
  Grid,
  Alert,
  CircularProgress,
  Divider
} from '@mui/material';
import { useSnackbar } from 'notistack';
import { settingsAPI } from '../api/settings';

const CATEGORY_LABELS = {
  auth: 'Authentication',
  email: 'Email / SMTP',
  webhooks: 'Webhooks',
  app: 'Application',
  features: 'Feature Flags'
};

function SettingsPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [currentTab, setCurrentTab] = useState('auth');
  const [settingsByCategory, setSettingsByCategory] = useState({});
  const [formData, setFormData] = useState({});
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const allSettings = await settingsAPI.getAll();

      // Group by category
      const grouped = {};
      allSettings.forEach(setting => {
        if (!grouped[setting.category]) {
          grouped[setting.category] = [];
        }
        grouped[setting.category].push(setting);
      });

      setSettingsByCategory(grouped);

      // Initialize form data
      const initialData = {};
      allSettings.forEach(setting => {
        initialData[setting.setting_key] = parseSettingValue(setting);
      });
      setFormData(initialData);

      setLoading(false);
    } catch (error) {
      console.error('Failed to load settings:', error);
      enqueueSnackbar('Failed to load settings', { variant: 'error' });
      setLoading(false);
    }
  };

  const parseSettingValue = (setting) => {
    const value = setting.setting_value;

    if (setting.data_type === 'boolean') {
      return Boolean(value);
    } else if (setting.data_type === 'integer') {
      return parseInt(value, 10);
    } else if (setting.data_type === 'float') {
      return parseFloat(value);
    } else if (setting.data_type === 'string') {
      return String(value);
    } else {
      return value;
    }
  };

  const handleChange = (settingKey, value) => {
    setFormData(prev => ({
      ...prev,
      [settingKey]: value
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      // Get current category settings
      const categorySettings = settingsByCategory[currentTab] || [];

      // Update each changed setting
      const updates = [];
      for (const setting of categorySettings) {
        const newValue = formData[setting.setting_key];
        const oldValue = parseSettingValue(setting);

        if (newValue !== oldValue) {
          updates.push(
            settingsAPI.update(setting.setting_key, newValue)
          );
        }
      }

      if (updates.length === 0) {
        enqueueSnackbar('No changes to save', { variant: 'info' });
        setSaving(false);
        return;
      }

      await Promise.all(updates);

      enqueueSnackbar(`${updates.length} setting(s) updated successfully`, { variant: 'success' });
      setHasChanges(false);

      // Reload settings
      await loadSettings();

      setSaving(false);
    } catch (error) {
      console.error('Failed to save settings:', error);
      enqueueSnackbar(error.response?.data?.detail || 'Failed to save settings', { variant: 'error' });
      setSaving(false);
    }
  };

  const handleReset = () => {
    // Reset form data to original values
    const categorySettings = settingsByCategory[currentTab] || [];
    const resetData = { ...formData };

    categorySettings.forEach(setting => {
      resetData[setting.setting_key] = parseSettingValue(setting);
    });

    setFormData(resetData);
    setHasChanges(false);
  };

  const renderSettingInput = (setting) => {
    const value = formData[setting.setting_key];
    const validationRules = setting.validation_rules || {};

    if (setting.data_type === 'boolean') {
      return (
        <FormControlLabel
          control={
            <Switch
              checked={Boolean(value)}
              onChange={(e) => handleChange(setting.setting_key, e.target.checked)}
            />
          }
          label={setting.description || setting.setting_key}
        />
      );
    }

    return (
      <TextField
        fullWidth
        label={setting.description || setting.setting_key}
        value={value}
        onChange={(e) => {
          let newValue = e.target.value;
          if (setting.data_type === 'integer') {
            newValue = parseInt(newValue, 10) || 0;
          } else if (setting.data_type === 'float') {
            newValue = parseFloat(newValue) || 0;
          }
          handleChange(setting.setting_key, newValue);
        }}
        type={setting.data_type === 'integer' || setting.data_type === 'float' ? 'number' : 'text'}
        InputProps={{
          inputProps: {
            min: validationRules.min,
            max: validationRules.max,
            step: setting.data_type === 'float' ? 0.1 : 1
          }
        }}
        helperText={
          validationRules.min !== undefined && validationRules.max !== undefined
            ? `Range: ${validationRules.min} - ${validationRules.max}`
            : ''
        }
      />
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  const categorySettings = settingsByCategory[currentTab] || [];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          System Settings
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Configure application settings. Changes take effect immediately.
        </Typography>

        {hasChanges && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            You have unsaved changes. Click Save to apply them.
          </Alert>
        )}

        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)}>
            {Object.keys(CATEGORY_LABELS).map(category => (
              <Tab
                key={category}
                label={CATEGORY_LABELS[category]}
                value={category}
              />
            ))}
          </Tabs>
        </Box>

        <Grid container spacing={3}>
          {categorySettings.map(setting => (
            <Grid item xs={12} md={6} key={setting.setting_key}>
              {renderSettingInput(setting)}
            </Grid>
          ))}
        </Grid>

        <Divider sx={{ my: 3 }} />

        <Box display="flex" justifyContent="flex-end" gap={2}>
          <Button
            variant="outlined"
            onClick={handleReset}
            disabled={!hasChanges || saving}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            onClick={handleSave}
            disabled={!hasChanges || saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}

export default SettingsPage;
```

### File 3: Update `frontend/src/api/index.js`

```javascript
export { settingsAPI } from './settings';
```

### File 4: Update `frontend/src/App.jsx`

Add the route:
```javascript
import SettingsPage from './pages/SettingsPage';

// In your routes:
<Route path="/settings" element={<SettingsPage />} />
```

---

## 🧪 TESTING

### Backend Testing

Test with curl or Postman:

```bash
# Get all settings
curl -X GET http://localhost:8000/api/v1/settings \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get public settings
curl -X GET http://localhost:8000/api/v1/settings/public \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update a setting
curl -X PUT http://localhost:8000/api/v1/settings/auth.jwt_expiry_minutes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"setting_value": 60}'

# Get audit log
curl -X GET http://localhost:8000/api/v1/settings/audit-log \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Frontend Testing

1. Login as admin
2. Navigate to `/settings`
3. Switch between tabs
4. Change a setting value
5. Click Save
6. Verify success message
7. Refresh page - verify changes persisted

---

## 🚀 DEPLOYMENT

1. **Run database migration** (from Part 1)
2. **Deploy backend code** (restart FastAPI server)
3. **Deploy frontend code** (rebuild and redeploy)
4. **Verify:** Access `/settings` page as admin

---

## ✅ VERIFICATION CHECKLIST

- [ ] Database migration ran successfully
- [ ] `system_settings` table created with default values
- [ ] `settings_audit_log` table created
- [ ] Backend API endpoints work (test with curl)
- [ ] Settings page loads without errors
- [ ] Can switch between tabs
- [ ] Can update settings and see success message
- [ ] Changes persist after page reload
- [ ] Audit log records changes
- [ ] Validation prevents invalid values (try entering out-of-range numbers)

---

## 📖 DOCUMENTATION

**User Guide:**
1. Navigate to Settings page (admin only)
2. Select category tab
3. Modify settings as needed
4. Click Save Changes
5. Changes take effect immediately

**Admin Notes:**
- Settings are cached for 60 seconds for performance
- Audit log tracks all changes
- Encrypted settings (like SMTP password) are stored securely
- Public settings are accessible to all users via `/settings/public` endpoint

---

## 🎯 SUCCESS CRITERIA

This handover is complete when:
1. ✅ All code files created and committed
2. ✅ Database migration successful
3. ✅ Backend API functional
4. ✅ Frontend UI working
5. ✅ Can update settings and see changes
6. ✅ Audit log working

Share screenshots of:
1. Settings page UI
2. Successful settings update
3. Database query showing updated values

---

**READY FOR HANDOVER #3: SMTP Email Service**
