# Changelog - Security Features

## Version 1.3.0 (2025-11-21) - Security Dashboard & Session Management

### SQL Migration
- **File:** `sql_scripts/v1.3.0_sessions_and_login_history.sql`
- Added `user_sessions` table for active session tracking
- Added `login_history` table for login attempt auditing
- Added `rate_limits` table for API rate limiting
- Added `admin_security` module to Admin panel

### Backend Changes

#### New Services
| File | Version | Description |
|------|---------|-------------|
| `security_service.py` | 1.0.0 | Session management, login history tracking, security stats |
| `rate_limit.py` | 1.0.0 | Rate limiting middleware (100 req/min, 5/min for auth) |

#### Updated Services
| File | Changes |
|------|---------|
| `auth_service.py` | - Record login attempts in login_history<br>- Create sessions on successful login |
| `main.py` | - Added security router<br>- Added rate limiting middleware |

#### New Routes
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/security/sessions` | GET | Get user's active sessions |
| `/security/sessions/{id}` | DELETE | Revoke a session |
| `/security/sessions` | DELETE | Revoke all other sessions |
| `/security/login-history` | GET | Get user's login history |
| `/security/admin/sessions` | GET | Admin: Get all sessions |
| `/security/admin/sessions/{id}` | DELETE | Admin: Revoke any session |
| `/security/admin/users/{id}/sessions` | DELETE | Admin: Revoke all user sessions |
| `/security/admin/login-history` | GET | Admin: Get all login history |
| `/security/admin/stats` | GET | Admin: Security statistics |

### Frontend Changes

#### New Components
| File | Version | Description |
|------|---------|-------------|
| `SecurityDashboard.jsx` | 1.0.0 | Admin security dashboard with sessions, login history, stats |

#### Updated Components
| File | Changes |
|------|---------|
| `AdminPanel.jsx` | - Added `/admin/security` route |
| `DashboardLayout.jsx` | - Added admin_security route mapping<br>- Added last_activity timestamp tracking<br>- Session timeout enforced even when tab closed |
| `api/index.js` | - Added securityAPI with all endpoints<br>- Added adminAPI.unlockUser |

### Features

#### 1. Active Sessions Management
- View all active sessions (device, IP, location, last activity)
- Revoke specific sessions or all other sessions
- Admin can view/revoke any user's sessions
- **Role-based session limits:**
  - **Admin:** 5 concurrent sessions max
  - **User:** 1 session only (single device)
- Oldest sessions auto-revoked when limit exceeded

#### 2. Login History & Alerts
- Records all login attempts (success, failed, locked)
- Tracks new device and new location flags
- Admin can view all login history with filtering
- Security statistics dashboard
- Admin can unlock locked accounts from login history

#### 3. Rate Limiting
- In-memory rate limiting middleware
- Default: 100 requests/minute
- Auth endpoints: 5 requests/minute
- Prevents brute force and DDoS attacks

#### 4. Session Timeout Enhancement
- 30-minute inactivity timeout
- **Now enforces timeout even when tab is closed/reopened**
- Stores last_activity timestamp in localStorage
- Auto-logout if >30 minutes since last activity

### Security Statistics
Dashboard shows:
- Active sessions count
- Logins in last 24 hours
- Failed logins in last 24 hours
- Account lockouts in last 24 hours
- Users with active sessions

---

## Version 1.2.0 (2025-11-21) - Account Security Features

### SQL Migration
- **File:** `sql_scripts/v1.2.0_account_security.sql`
- Added `failed_login_attempts` column
- Added `locked_until` column
- Added `must_change_password` column
- Added `last_password_change` column

### Backend Changes

#### Updated Services
| File | Version | Changes |
|------|---------|---------|
| `auth_service.py` | 1.3.0 | - Account lockout (5 attempts/15 min)<br>- `change_password()` function<br>- `admin_unlock_account()` function |
| `password.py` | - | - Added 50+ common passwords blocklist<br>- Enhanced `validate_password_strength()` |
| `admin_service.py` | - | - Temp password = `firstname@year`<br>- Sets `must_change_password=TRUE` on user creation |

#### Updated Routes
| File | Version | Changes |
|------|---------|---------|
| `auth.py` | 1.1.0 | - Added `/change-password` endpoint<br>- Login returns `must_change_password` flag<br>- Added 423 Locked response |
| `admin.py` | - | - Added `/users/{id}/unlock` endpoint |

#### New Schemas
| Schema | Description |
|--------|-------------|
| `ChangePasswordRequest` | Current password + new password |
| `ChangePasswordResponse` | Success message |

### Frontend Changes

#### New Components
| File | Version | Description |
|------|---------|-------------|
| `ChangePasswordPage.jsx` | 1.0.0 | Password change page with requirements checklist |

#### Updated Components
| File | Version | Changes |
|------|---------|---------|
| `authStore.js` | 1.1.0 | - Added `mustChangePassword` state<br>- Clear `last_activity` on logout |
| `App.jsx` | 1.1.0 | - Added `/change-password` route<br>- Auto-redirect when `mustChangePassword=true` |
| `LoginPage.jsx` | - | - Redirect to change password when required |
| `DashboardLayout.jsx` | - | - Added "Change Password" to user menu |
| `auth.js` | - | - Added `changePassword()` API method |

### Features

#### 1. Account Lockout After Failed Logins
- Lock account after 5 failed login attempts
- 15-minute lockout duration
- Shows remaining attempts to user
- Admin can unlock via `/admin/users/{id}/unlock`
- Prevents brute force attacks

#### 2. Password Strength Enforcement
- Minimum 8 characters
- Requires uppercase, lowercase, number, special character
- Blocks 50+ common passwords (password, 123456, etc.)
- Real-time validation in frontend with checklist

#### 3. Force Password Change on First Login
- Users created by admin have `must_change_password=TRUE`
- Login returns `must_change_password` flag
- Auto-redirects to `/change-password` page
- Cannot access other pages until password changed
- Temporary password format: `firstname@year` (e.g., `john@2025`)

#### 4. In-App Password Change
- Requires current password verification
- Shows password requirements checklist with icons
- Validates new password strength
- Clears `must_change_password` flag on success
- Accessible via user menu (top right)
- Route: `/change-password`

---

## Git Commits

```
68724e8 feat: Add role-based session limits (Admin: 5, User: 1)
1c904cb fix: Enforce 30-min session timeout even when tab is closed/reopened
f95c57a feat: Record login history and create sessions on login
c1b9081 fix: Use react-query instead of @tanstack/react-query in SecurityDashboard
9e352f5 fix: Correct column names in modules INSERT (is_active, parent_module_id)
4d26793 feat: Add security dashboard with sessions, login history, rate limiting
6d25f09 feat: Add Change Password option to user menu
7056f0f feat: Simplify temp password to firstname@year format
55df5f9 feat: Add account security features
```

---

## Deployment Checklist

### 1. Database Migrations
```sql
-- Run in order:
psql -f sql_scripts/v1.2.0_account_security.sql
psql -f sql_scripts/v1.3.0_sessions_and_login_history.sql
```

### 2. Backend
```bash
# Pull latest changes
git pull origin claude/account-lockout-password-strength-01WzJBS9KMQo64fysRrQeyA8

# Restart backend
# (uvicorn will auto-reload if in dev mode)
```

### 3. Frontend
```bash
# Pull latest changes
git pull origin claude/account-lockout-password-strength-01WzJBS9KMQo64fysRrQeyA8

# Rebuild
npm run build  # or your build command
```

### 4. Post-Deployment Testing

#### Test Account Lockout
1. Try to login with wrong password 5 times
2. Should get locked for 15 minutes
3. Admin can unlock via Security Dashboard

#### Test Session Limits
- **User:** Log in on 2 devices, 2nd login should kick out 1st
- **Admin:** Log in on 5 devices, all work. 6th device kicks out oldest

#### Test Session Timeout
1. Log in, use app
2. Close tab, wait 31 minutes
3. Reopen - should be logged out

#### Test Force Password Change
1. Admin creates new user
2. User gets temp password `firstname@year`
3. User logs in, forced to change password
4. Can't access other pages until changed

#### Test Security Dashboard (Admin)
1. Go to `/admin/security`
2. View active sessions
3. View login history
4. Check statistics

---

## Configuration

### Rate Limiting
Edit `backend/app/middleware/rate_limit.py`:
```python
RATE_LIMIT_CONFIG = {
    "default_limit": 100,  # requests per minute
    "window_seconds": 60,
}

endpoint_limits = {
    "/api/auth/login": (5, 60),           # 5 per minute
    "/api/auth/forgot-password": (3, 300), # 3 per 5 minutes
}
```

### Session Limits
Edit `backend/app/services/security_service.py`:
```python
MAX_SESSIONS = {
    "Admin": 5,
    "User": 1
}
```

### Session Timeout
Edit `frontend/src/components/DashboardLayout.jsx`:
```javascript
const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
const WARNING_TIME = 60 * 1000; // Warning 1 min before
```

### Account Lockout
Edit `backend/app/services/auth_service.py`:
```python
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
```

---

## Security Impact

| Threat | Mitigation | Effectiveness |
|--------|------------|---------------|
| Brute Force Login | Account lockout + Rate limiting | **High** |
| Weak Passwords | Strength enforcement + Common password check | **High** |
| Session Hijacking | Session management + Revocation | **Medium** |
| DDoS Attacks | Rate limiting | **Medium** |
| Password Sharing | Single session for users | **Medium** |
| Inactive Sessions | 30-min timeout (enforced even when closed) | **High** |
| Admin-generated Passwords | Force change on first login | **High** |

---

## API Documentation

For full API documentation, visit: `http://localhost:8000/docs` (Swagger UI)

Key endpoints:
- **Auth:** `/api/auth/*`
- **Security:** `/api/security/*`
- **Admin:** `/api/admin/*`
