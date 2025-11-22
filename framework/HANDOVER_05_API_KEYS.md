# HANDOVER MESSAGE #5: API Key Management

## 📋 MISSION
Build **API Key Authentication** system for programmatic access. Allow users/admins to generate API keys with scoped permissions for automation, scripts, and integrations.

## 🎯 FEATURES

1. **API Key Generation:** Create keys with custom scopes
2. **Scope-based Permissions:** `resource:action` format (e.g., `inventory:read`)
3. **Usage Tracking:** Log all API key usage
4. **Key Management:** List, revoke, rotate keys
5. **Security:** Hash keys like passwords, show full key only once
6. **Admin UI:** Manage API keys, view usage stats

---

## 🗄️ PART 1: DATABASE MIGRATION

Create file: `backend/migrations/011_api_keys.sql`

```sql
-- ============================================================================
-- Migration 011: API Key Management
-- ============================================================================

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);

-- API Key usage log
CREATE TABLE IF NOT EXISTS api_key_usage (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER REFERENCES api_keys(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    ip_address INET,
    user_agent TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_api_key_usage_key_id ON api_key_usage(api_key_id);
CREATE INDEX idx_api_key_usage_created_at ON api_key_usage(created_at DESC);

-- Verify migration
SELECT * FROM api_keys;
```

Run this in Supabase.

---

## 🔧 PART 2: BACKEND IMPLEMENTATION

### File 1: `backend/app/models/api_keys.py`

```python
"""
API Key Models
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

class APIKeyCreate(BaseModel):
    """Create API key request"""
    name: str
    description: Optional[str] = None
    scopes: List[str] = []
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)

class APIKeyResponse(BaseModel):
    """API key response (without full key)"""
    id: int
    user_id: str
    key_prefix: str
    name: str
    description: Optional[str] = None
    scopes: List[str]
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class APIKeyCreatedResponse(APIKeyResponse):
    """API key creation response (includes full key - shown once)"""
    api_key: str

class APIKeyUsageResponse(BaseModel):
    """API key usage log entry"""
    id: int
    endpoint: str
    method: str
    status_code: Optional[int]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
```

### File 2: `backend/app/services/api_key_service.py`

```python
"""
API Key Service
"""
import secrets
import hashlib
import bcrypt
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from asyncpg import Connection

# Available scopes
AVAILABLE_SCOPES = [
    # Inventory
    "inventory:read",
    "inventory:write",
    "inventory:delete",
    "inventory:*",

    # Tickets
    "tickets:read",
    "tickets:write",
    "tickets:delete",
    "tickets:*",

    # Users (Admin)
    "users:read",
    "users:write",
    "users:delete",
    "users:*",

    # Dashboard
    "dashboard:read",

    # Development
    "development:read",
    "development:write",
    "development:*",

    # Docs
    "docs:read",

    # Settings (Admin)
    "settings:read",
    "settings:write",

    # Webhooks (Admin)
    "webhooks:read",
    "webhooks:write",
    "webhooks:*",

    # Admin (Meta - includes all admin scopes)
    "admin:*",

    # God mode (use with caution)
    "*:*"
]

def generate_api_key() -> tuple[str, str, str]:
    """
    Generate API key
    Returns: (full_key, key_hash, key_prefix)
    """
    # Generate random key
    random_bytes = secrets.token_bytes(32)
    key = f"sk_live_{secrets.token_urlsafe(32)}"

    # Hash for storage
    key_hash = bcrypt.hashpw(key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Prefix for display (first 12 chars)
    key_prefix = key[:12] + "..."

    return key, key_hash, key_prefix

async def create_api_key(
    conn: Connection,
    user_id: str,
    name: str,
    scopes: List[str],
    description: Optional[str] = None,
    expires_in_days: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new API key"""
    # Validate scopes
    invalid_scopes = [s for s in scopes if s not in AVAILABLE_SCOPES]
    if invalid_scopes:
        raise ValueError(f"Invalid scopes: {', '.join(invalid_scopes)}")

    # Generate key
    api_key, key_hash, key_prefix = generate_api_key()

    # Calculate expiry
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    # Insert into database
    created = await conn.fetchrow(
        """
        INSERT INTO api_keys (
            user_id, key_hash, key_prefix, name, description, scopes, expires_at
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id, user_id, key_prefix, name, description, scopes, is_active, expires_at, created_at
        """,
        user_id,
        key_hash,
        key_prefix,
        name,
        description,
        scopes,
        expires_at
    )

    return {
        **dict(created),
        'api_key': api_key  # Return full key (only time it's shown)
    }

async def verify_api_key(
    conn: Connection,
    api_key: str
) -> Optional[Dict[str, Any]]:
    """
    Verify API key and return user info
    """
    # Get all active API keys
    api_keys = await conn.fetch(
        """
        SELECT
            ak.id, ak.user_id, ak.key_hash, ak.scopes, ak.is_active, ak.expires_at,
            up.email, up.role_id, r.role_name
        FROM api_keys ak
        JOIN user_profiles up ON ak.user_id = up.user_id
        JOIN roles r ON up.role_id = r.id
        WHERE ak.is_active = true
          AND (ak.expires_at IS NULL OR ak.expires_at > NOW())
        """
    )

    # Check each key (bcrypt comparison)
    for key_row in api_keys:
        if bcrypt.checkpw(api_key.encode('utf-8'), key_row['key_hash'].encode('utf-8')):
            # Update last used
            await conn.execute(
                "UPDATE api_keys SET last_used_at = NOW() WHERE id = $1",
                key_row['id']
            )

            return {
                'api_key_id': key_row['id'],
                'user_id': key_row['user_id'],
                'email': key_row['email'],
                'role_name': key_row['role_name'],
                'scopes': key_row['scopes']
            }

    return None

async def check_scope(scopes: List[str], required_scope: str) -> bool:
    """Check if API key has required scope"""
    # God mode
    if "*:*" in scopes:
        return True

    # Admin wildcard
    if "admin:*" in scopes and required_scope.startswith(('users:', 'modules:', 'settings:', 'webhooks:')):
        return True

    # Exact match
    if required_scope in scopes:
        return True

    # Wildcard match (e.g., "inventory:*" includes "inventory:read")
    resource = required_scope.split(':')[0]
    if f"{resource}:*" in scopes:
        return True

    return False

async def log_api_key_usage(
    conn: Connection,
    api_key_id: int,
    endpoint: str,
    method: str,
    status_code: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    response_time_ms: Optional[int] = None
):
    """Log API key usage"""
    await conn.execute(
        """
        INSERT INTO api_key_usage (
            api_key_id, endpoint, method, status_code, ip_address, user_agent, response_time_ms
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        api_key_id,
        endpoint,
        method,
        status_code,
        ip_address,
        user_agent,
        response_time_ms
    )

async def revoke_api_key(conn: Connection, api_key_id: int, user_id: str) -> bool:
    """Revoke an API key"""
    result = await conn.execute(
        """
        UPDATE api_keys
        SET is_active = false, revoked_at = NOW()
        WHERE id = $1 AND user_id = $2
        """,
        api_key_id,
        user_id
    )

    return result != "UPDATE 0"
```

### File 3: `backend/app/dependencies.py`

Update with API key authentication:

```python
from fastapi import Header, HTTPException, status, Request
from app.services import api_key_service

async def require_api_key(
    request: Request,
    x_api_key: str = Header(None, alias="X-API-Key"),
    conn = Depends(get_db_connection)
):
    """Require valid API key"""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    # Verify API key
    user_info = await api_key_service.verify_api_key(conn, x_api_key)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    # Log usage (non-blocking)
    try:
        await api_key_service.log_api_key_usage(
            conn,
            api_key_id=user_info['api_key_id'],
            endpoint=str(request.url.path),
            method=request.method,
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent')
        )
    except Exception as e:
        logger.warning(f"Failed to log API key usage: {e}")

    return user_info

def require_api_key_scope(required_scope: str):
    """Factory for scope-based API key auth"""
    async def dependency(
        user_info: dict = Depends(require_api_key)
    ):
        if not await api_key_service.check_scope(user_info['scopes'], required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {required_scope}"
            )
        return user_info

    return dependency
```

### File 4: `backend/app/routes/api_keys.py`

```python
"""
API Key Routes
"""
from fastapi import APIRouter, Depends
from typing import List
from asyncpg import Connection

from app.database import get_db_connection
from app.dependencies import get_current_user, require_admin
from app.models.api_keys import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreatedResponse,
    APIKeyUsageResponse
)
from app.services import api_key_service

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db_connection)
):
    """List user's API keys"""
    keys = await conn.fetch(
        "SELECT * FROM api_keys WHERE user_id = $1 ORDER BY created_at DESC",
        current_user['user_id']
    )
    return [dict(k) for k in keys]

@router.post("/", response_model=APIKeyCreatedResponse)
async def create_api_key(
    request: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db_connection)
):
    """Create new API key"""
    try:
        created = await api_key_service.create_api_key(
            conn,
            user_id=current_user['user_id'],
            name=request.name,
            scopes=request.scopes,
            description=request.description,
            expires_in_days=request.expires_in_days
        )
        return created
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{api_key_id}")
async def revoke_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db_connection)
):
    """Revoke API key"""
    success = await api_key_service.revoke_api_key(conn, api_key_id, current_user['user_id'])

    if not success:
        raise HTTPException(status_code=404, detail="API key not found")

    return {"message": "API key revoked"}

@router.get("/{api_key_id}/usage", response_model=List[APIKeyUsageResponse])
async def get_api_key_usage(
    api_key_id: int,
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_db_connection)
):
    """Get API key usage logs"""
    # Verify ownership
    key = await conn.fetchrow(
        "SELECT user_id FROM api_keys WHERE id = $1",
        api_key_id
    )

    if not key or key['user_id'] != current_user['user_id']:
        raise HTTPException(status_code=404, detail="API key not found")

    usage = await conn.fetch(
        """
        SELECT id, endpoint, method, status_code, ip_address, created_at
        FROM api_key_usage
        WHERE api_key_id = $1
        ORDER BY created_at DESC
        LIMIT $2
        """,
        api_key_id,
        limit
    )

    return [dict(u) for u in usage]

@router.get("/scopes/available")
async def get_available_scopes(
    current_user: dict = Depends(get_current_user)
):
    """Get list of available scopes"""
    return {"scopes": api_key_service.AVAILABLE_SCOPES}
```

### File 5: Example usage in routes

Allow both JWT and API key auth:

```python
from fastapi import Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

async def get_current_user_or_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    x_api_key: str = Header(None, alias="X-API-Key"),
    conn = Depends(get_db_connection)
):
    """Allow both JWT and API key authentication"""
    # Try API key first
    if x_api_key:
        user_info = await api_key_service.verify_api_key(conn, x_api_key)
        if user_info:
            # Log usage
            await api_key_service.log_api_key_usage(...)
            return user_info

    # Fall back to JWT
    if credentials:
        return await verify_jwt_token(credentials.credentials)

    raise HTTPException(status_code=401, detail="Authentication required")

# Use in routes:
@router.get("/inventory")
async def get_inventory(
    user: dict = Depends(get_current_user_or_api_key)
):
    # Works with both JWT and API key
    pass
```

---

## 🎨 PART 3: FRONTEND

### File 1: `frontend/src/api/apiKeys.js`

```javascript
import apiClient from './client';

export const apiKeysAPI = {
  list: async () => {
    const response = await apiClient.get('/api-keys');
    return response.data;
  },

  create: async (data) => {
    const response = await apiClient.post('/api-keys', data);
    return response.data;
  },

  revoke: async (id) => {
    const response = await apiClient.delete(`/api-keys/${id}`);
    return response.data;
  },

  getUsage: async (id, limit = 100) => {
    const response = await apiClient.get(`/api-keys/${id}/usage`, { params: { limit } });
    return response.data;
  },

  getAvailableScopes: async () => {
    const response = await apiClient.get('/api-keys/scopes/available');
    return response.data;
  }
};
```

### File 2: `frontend/src/pages/APIKeysPage.jsx`

```javascript
import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Typography,
  Box,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, ContentCopy as CopyIcon } from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { apiKeysAPI } from '../api/apiKeys';

function APIKeysPage() {
  const { enqueueSnackbar } = useSnackbar();
  const [apiKeys, setApiKeys] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [keyCreatedDialogOpen, setKeyCreatedDialogOpen] = useState(false);
  const [newApiKey, setNewApiKey] = useState('');
  const [availableScopes, setAvailableScopes] = useState([]);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    scopes: [],
    expires_in_days: 365
  });

  useEffect(() => {
    loadApiKeys();
    loadAvailableScopes();
  }, []);

  const loadApiKeys = async () => {
    try {
      const data = await apiKeysAPI.list();
      setApiKeys(data);
    } catch (error) {
      enqueueSnackbar('Failed to load API keys', { variant: 'error' });
    }
  };

  const loadAvailableScopes = async () => {
    try {
      const data = await apiKeysAPI.getAvailableScopes();
      setAvailableScopes(data.scopes);
    } catch (error) {
      console.error('Failed to load scopes');
    }
  };

  const handleCreate = async () => {
    try {
      const result = await apiKeysAPI.create(formData);
      setNewApiKey(result.api_key);
      setKeyCreatedDialogOpen(true);
      setDialogOpen(false);
      loadApiKeys();
      setFormData({ name: '', description: '', scopes: [], expires_in_days: 365 });
    } catch (error) {
      enqueueSnackbar(error.response?.data?.detail || 'Failed to create API key', { variant: 'error' });
    }
  };

  const handleRevoke = async (id) => {
    if (!confirm('Revoke this API key? This cannot be undone.')) return;

    try {
      await apiKeysAPI.revoke(id);
      enqueueSnackbar('API key revoked', { variant: 'success' });
      loadApiKeys();
    } catch (error) {
      enqueueSnackbar('Failed to revoke API key', { variant: 'error' });
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    enqueueSnackbar('Copied to clipboard', { variant: 'success' });
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4">API Keys</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setDialogOpen(true)}
          >
            Create API Key
          </Button>
        </Box>

        <Alert severity="info" sx={{ mb: 2 }}>
          API keys allow programmatic access to your account. Keep them secure and never share them publicly.
        </Alert>

        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Key Prefix</TableCell>
              <TableCell>Scopes</TableCell>
              <TableCell>Expires</TableCell>
              <TableCell>Last Used</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {apiKeys.map(key => (
              <TableRow key={key.id}>
                <TableCell>{key.name}</TableCell>
                <TableCell>
                  <code>{key.key_prefix}</code>
                </TableCell>
                <TableCell>
                  {key.scopes.slice(0, 3).map(scope => (
                    <Chip key={scope} label={scope} size="small" sx={{ mr: 0.5 }} />
                  ))}
                  {key.scopes.length > 3 && <Chip label={`+${key.scopes.length - 3} more`} size="small" />}
                </TableCell>
                <TableCell>
                  {key.expires_at ? new Date(key.expires_at).toLocaleDateString() : 'Never'}
                </TableCell>
                <TableCell>
                  {key.last_used_at ? new Date(key.last_used_at).toLocaleString() : 'Never'}
                </TableCell>
                <TableCell>
                  <IconButton size="small" onClick={() => handleRevoke(key.id)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {/* Create Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create API Key</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            sx={{ mt: 2, mb: 2 }}
          />
          <TextField
            fullWidth
            label="Description"
            multiline
            rows={2}
            value={formData.description}
            onChange={(e) => setFormData({...formData, description: e.target.value})}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Scopes</InputLabel>
            <Select
              multiple
              value={formData.scopes}
              onChange={(e) => setFormData({...formData, scopes: e.target.value})}
              renderValue={(selected) => selected.join(', ')}
            >
              {availableScopes.map(scope => (
                <MenuItem key={scope} value={scope}>{scope}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Expires in (days)"
            type="number"
            value={formData.expires_in_days}
            onChange={(e) => setFormData({...formData, expires_in_days: parseInt(e.target.value)})}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreate} variant="contained" disabled={!formData.name || formData.scopes.length === 0}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Key Created Dialog */}
      <Dialog open={keyCreatedDialogOpen} onClose={() => setKeyCreatedDialogOpen(false)}>
        <DialogTitle>API Key Created</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This is the only time you'll see this key. Copy it now and store it securely.
          </Alert>
          <Box display="flex" alignItems="center" gap={1}>
            <TextField
              fullWidth
              value={newApiKey}
              InputProps={{ readOnly: true }}
            />
            <IconButton onClick={() => copyToClipboard(newApiKey)}>
              <CopyIcon />
            </IconButton>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setKeyCreatedDialogOpen(false)} variant="contained">
            I've Saved My Key
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default APIKeysPage;
```

---

## 🧪 TESTING

1. Create API key with `inventory:read` scope
2. Copy the key
3. Test with curl:
```bash
curl -H "X-API-Key: YOUR_KEY_HERE" http://localhost:8000/api/v1/inventory
```
4. Verify access works
5. Try accessing endpoint without permission - should fail

---

## ✅ VERIFICATION CHECKLIST

- [ ] Can create API key
- [ ] Key shown only once
- [ ] Can authenticate with API key
- [ ] Scope restrictions work
- [ ] Usage logging works
- [ ] Can revoke key

**READY FOR HANDOVER #6: WebSocket Real-time System**
