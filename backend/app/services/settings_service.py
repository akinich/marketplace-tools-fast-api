"""
Settings Service - Manages system configuration
Version: 1.0.0
Description: Service layer for system settings with caching and validation
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
                au.email as changed_by
            FROM settings_audit_log sal
            LEFT JOIN auth.users au ON sal.changed_by = au.id
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
                au.email as changed_by
            FROM settings_audit_log sal
            LEFT JOIN auth.users au ON sal.changed_by = au.id
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
