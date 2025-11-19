# Admin Module - User Guide

**Version:** 1.5.0
**Audience:** System Administrators, IT Managers

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [User Management](#user-management)
3. [Module Management](#module-management)
4. [Permission Management](#permission-management)
5. [Activity Monitoring](#activity-monitoring)
6. [Common Administrative Tasks](#common-administrative-tasks)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing the Admin Panel

1. **Login Requirements:**
   - You must have an account with "Admin" role
   - Only admin users can access the admin panel
   - Regular users will see "Access Denied" if they try

2. **Navigate to Admin:**
   - Click "Admin" in the main navigation menu
   - You'll see three main sections:
     - **Users** - Manage user accounts
     - **Module Management** - Configure system modules
     - **Activity Logs** - View system audit trail

### Admin Panel Overview

The admin panel provides:
- **User Management** - Create, update, and deactivate user accounts
- **Module Management** - Enable/disable system modules
- **Permission Management** - Control which modules users can access
- **Activity Logs** - Monitor all administrative actions

---

## User Management

### Viewing Users

1. Navigate to **Admin → Users**
2. You'll see a table with all users showing:
   - **Full Name** - User's display name
   - **Email** - Login email address
   - **Role** - Admin or User
   - **Status** - Active (green) or Inactive (red)
   - **Created Date** - When account was created
   - **Actions** - Manage permissions icon

**Filters:**
- **Status Filter:** Show All, Active Only, Inactive Only
- **Role Filter:** Show All, Admins Only, Users Only
- **Search:** Type to filter by name or email

**Pagination:**
- Default: 50 users per page
- Use navigation buttons at bottom to browse pages

---

### Creating a New User

**Scenario:** You need to give a new employee access to the system.

**Steps:**

1. Click **"Add User"** button (top right)

2. **Fill in the form:**
   - **Email:** Enter user's work email (e.g., john.smith@company.com)
   - **Full Name:** Enter user's full name (e.g., John Smith)
   - **Role:** Select from dropdown:
     - **User** - Regular user (most common)
     - **Admin** - Full system access (use sparingly)

3. Click **"Create User"**

4. **Temporary Password Display:**
   - A dialog will show the temporary password
   - **IMPORTANT:** Copy this password - it's shown only once!
   - Example: `TempPass7aH9k2X!`

5. **Share Password Securely:**
   - Email the user their credentials:
     ```
     Welcome to the Farm Management System!

     Login URL: https://your-system.com
     Email: john.smith@company.com
     Temporary Password: TempPass7aH9k2X!

     Please log in and change your password immediately.
     ```
   - Use encrypted email or secure messaging
   - DO NOT share passwords in plain text chat

6. **User First Login:**
   - User logs in with temporary password
   - System prompts to change password
   - User sets new secure password

---

### Updating a User

**Use Cases:**
- Promote user to admin
- Change user's name (marriage, legal change)
- Temporarily deactivate user (leave of absence)

**Steps:**

1. Find user in the list
2. Click the **edit icon** (pencil) next to their name
3. Update fields:
   - **Full Name** - Change if needed
   - **Role** - Change to Admin or User
   - **Status** - Toggle active/inactive
4. Click **"Save Changes"**

**Important Notes:**
- Cannot change email address (it's the login ID)
- Cannot edit your own admin status (prevents lockout)
- Deactivating a user immediately revokes all access

---

### Deactivating a User

**When to Deactivate:**
- Employee leaves company
- User no longer needs access
- Security concern (suspicious activity)

**Steps:**

1. Find user in the list
2. Click the **delete icon** (trash can)
3. Confirm the action
4. User is marked "Inactive" (soft delete)

**What Happens:**
- User status changes to "Inactive"
- User cannot log in
- User's data is preserved (audit trail)
- User's permissions are hidden but not deleted
- Can be reactivated later if needed

**Security Note:**
- You CANNOT deactivate yourself (prevents admin lockout)
- If you try, you'll see: "Cannot delete your own account"

---

## Module Management

### Understanding Modules

**Modules** are functional areas of the system. Examples:
- **Dashboard** - System overview and metrics
- **Inventory** - Inventory management
- **Biofloc** - Biofloc aquaculture operations
- **Admin** - System administration (this module!)

**Hierarchical Structure:**

Some modules are organized in parent-child relationships:

```
Aquaculture (parent)
  ├─ Biofloc (child)
  ├─ Hatchery (child)
  └─ Nursery (child)
```

**Why Hierarchy Matters:**
- Disabling a parent automatically disables all children
- Cannot enable a child if parent is disabled
- Helps organize related functionality

---

### Viewing Modules

1. Navigate to **Admin → Module Management**
2. You'll see module cards grouped by parent
3. Each card shows:
   - **Module Name** - e.g., "Inventory Management"
   - **Description** - What the module does
   - **Icon** - Visual identifier
   - **Status Toggle** - Enable/disable switch
   - **Display Order** - Affects menu ordering

**Status Indicators:**
- **Green Switch (ON)** - Module is enabled
- **Gray Switch (OFF)** - Module is disabled
- **Red "Critical" Chip** - Cannot be disabled
- **Gray Switch (Disabled)** - Parent is disabled, cannot enable child

---

### Enabling a Module

**Scenario:** You want to activate the Biofloc module for your team.

**Steps:**

1. Find the module card (e.g., "Biofloc Management")
2. Check if parent is enabled (e.g., "Aquaculture")
3. Click the toggle switch to **ON**
4. Module is now enabled

**What Happens:**
- Module appears in navigation for users with permissions
- Users can access module functionality
- No user impact (enabling is safe)

**Note:** If the toggle is disabled and grayed out, check:
- Is this a child module? → Ensure parent is enabled first
- Is there a parent module card above it? → Enable that first

---

### Disabling a Module

**Scenario:** You're decommissioning the Hatchery operations and want to remove the module.

**Important:** Disabling a module removes access for ALL users currently using it. Use with caution!

**Steps:**

1. Find the module card (e.g., "Hatchery Operations")

2. Click the toggle switch to **OFF**

3. **User Impact Warning Dialog appears:**
   ```
   ⚠️ Confirm Module Disable

   Disabling "Hatchery Operations" will affect 12 users.

   Affected users:
   - John Smith (john@example.com)
   - Jane Doe (jane@example.com)
   - ... (10 more)

   Are you sure you want to disable this module?

   [Cancel] [Disable Module]
   ```

4. **Review the Impact:**
   - See how many users will lose access
   - See list of affected users
   - Decide if you want to proceed

5. Click **"Disable Module"** to confirm OR **"Cancel"** to abort

**What Happens:**
- Module is disabled
- All users lose access to this module
- If module has children, they are also disabled
- All permissions are removed automatically
- Action is logged in activity logs

**Critical Modules:**

Some modules **CANNOT be disabled** (security protection):
- **Dashboard** - System homepage, needed for navigation
- **Admin** - This panel, prevents admin lockout

You'll see a red "Critical" chip on these modules, and the toggle is disabled.

---

### Cascading Disable (Parent Modules)

**Scenario:** You disable "Aquaculture" parent module.

**What Happens:**
```
Disabling Aquaculture (parent)
  ↓
Automatically disables:
  ├─ Biofloc (child)
  ├─ Hatchery (child)
  └─ Nursery (child)
  ↓
All users lose access to all 4 modules
```

**Warning Dialog shows:**
```
⚠️ Disabling "Aquaculture" will also disable:
- Biofloc Management
- Hatchery Operations
- Nursery Management

This will affect 45 users across all modules.
```

**Why Cascading Disable?**
- Maintains logical hierarchy
- Prevents orphaned child modules
- Ensures data consistency

---

## Permission Management

### Understanding Permissions

**Permissions** control which modules a user can access.

**Key Rules:**
1. **Admin users:** Automatically have access to ALL modules (cannot be modified)
2. **Regular users:** Need explicit permission grants per module
3. **Hierarchical grants:** Granting parent grants all children

**Example:**
```
User: John Smith (Role: User)

Permissions:
✓ Dashboard (always granted)
✓ Inventory (granted by admin)
✗ Biofloc (not granted)
✓ Aquaculture (granted)
  ✓ Hatchery (auto-granted, child of Aquaculture)
  ✓ Nursery (auto-granted, child of Aquaculture)
```

---

### Granting Permissions to a User

**Scenario:** New user needs access to Inventory and Biofloc modules.

**Steps:**

1. Navigate to **Admin → Users**

2. Find the user (e.g., "John Smith")

3. Click the **"Manage Permissions"** icon (key icon)

4. **Permissions Dialog opens:**
   - Shows all modules grouped by parent
   - Checkboxes next to each module
   - Currently granted modules are checked

5. **Select Modules:**

   **Option A - Individual Selection:**
   - Click checkbox next to "Inventory Management"
   - Click checkbox next to "Biofloc Management"

   **Option B - Hierarchical Selection:**
   - Click "Grant All" button next to "Aquaculture"
   - This grants: Aquaculture + Biofloc + Hatchery + Nursery

6. Click **"Save"** button

7. **Confirmation:**
   - Success message appears
   - User can now access granted modules
   - Changes take effect immediately

**Visual Example:**
```
Permissions for: John Smith

□ Inventory Management
□ Reports

Aquaculture Operations [Grant All]
  ↳ □ Biofloc Management
  ↳ □ Hatchery Operations
  ↳ □ Nursery Management

[Cancel] [Save]
```

After granting Inventory and clicking "Grant All" for Aquaculture:
```
✓ Inventory Management
□ Reports

✓ Aquaculture Operations [Grant All]
  ↳ ✓ Biofloc Management
  ↳ ✓ Hatchery Operations
  ↳ ✓ Nursery Management

[Cancel] [Save]
```

---

### Revoking Permissions

**Scenario:** User changed roles, no longer needs Biofloc access.

**Steps:**

1. Open user's **Permissions Dialog** (same as granting)
2. **Uncheck** the module(s) to revoke
3. Click **"Save"**
4. User immediately loses access to those modules

**Important:**
- Revoking parent also revokes all children
- User will see "Access Denied" if they try to access revoked module
- Can be re-granted anytime

---

### Special Cases

#### **Admin Users**
- Cannot modify permissions via the dialog
- "Manage Permissions" icon is hidden for admin users
- Admins automatically have ALL module access
- To remove admin access, change role to "User" first

#### **Inactive Modules**
- Cannot grant permissions to disabled modules
- If module is disabled after grant, permission hidden (but not deleted)
- Re-enabling module restores previous permissions

---

## Activity Monitoring

### Viewing Activity Logs

**Purpose:** Monitor all administrative actions for security and audit.

**Access:**
1. Navigate to **Admin → Activity Logs**
2. You'll see a table with recent activities

**What's Logged:**
- User logins and logouts
- User creation, updates, deletions
- Permission changes
- Module enable/disable actions
- Any administrative action

**Log Entry Details:**
- **Timestamp** - When action occurred
- **User** - Who performed the action
- **Role** - User's role at time of action
- **Action Type** - Type of action (create_user, update_permissions, etc.)
- **Module** - Affected module (if applicable)
- **Description** - Human-readable summary

---

### Filtering Logs

**Default View:**
- Last 7 days of activity
- 50 entries per page
- All users, all actions

**Available Filters:**

1. **Time Period:**
   - Last 1 day
   - Last 7 days (default)
   - Last 30 days
   - Last 90 days (maximum)

2. **User Filter:**
   - Select specific user from dropdown
   - See only that user's actions

3. **Module Filter:**
   - Select specific module
   - See only actions affecting that module

4. **Action Type Filter:**
   - Select specific action type
   - See only that type of action (e.g., all "update_permissions")

**Example Filters:**
```
Time Period: Last 30 days
User: John Admin
Action Type: update_permissions

Result: Shows all permission changes made by John Admin in last 30 days
```

---

### Investigating an Incident

**Scenario:** A user reports they lost access to Inventory module unexpectedly.

**Investigation Steps:**

1. Navigate to **Activity Logs**

2. **Apply Filters:**
   - Time Period: Last 7 days
   - Module: Inventory
   - Action Type: update_permissions

3. **Review Results:**
   - Look for permission updates affecting this user
   - Check timestamp when access was removed
   - Identify which admin made the change

4. **Example Log Entry:**
   ```
   2025-11-18 14:30:00
   User: Jane Admin
   Action: update_permissions
   Description: Updated permissions for user john.smith@example.com
   Metadata: { "modules_granted": ["biofloc"], "modules_count": 1 }
   ```

5. **Analysis:**
   - Jane Admin updated John's permissions on Nov 18
   - Only granted "biofloc" module
   - This removed previous Inventory access

6. **Resolution:**
   - Contact Jane Admin to understand why
   - Re-grant Inventory access if needed
   - Document the incident

---

### Understanding Metadata

Many log entries include **metadata** (additional details in JSON format).

**Examples:**

**User Creation:**
```json
{
  "user_id": "uuid-123",
  "email": "newuser@example.com",
  "role": "User"
}
```

**Permission Update:**
```json
{
  "user_id": "uuid-456",
  "modules_granted": ["inventory", "biofloc", "reports"],
  "modules_count": 3
}
```

**Module Disable:**
```json
{
  "module_id": 5,
  "module_key": "hatchery",
  "children_disabled": ["hatchery_feeding", "hatchery_grading"],
  "users_affected": 12
}
```

**How to View:**
- Metadata is visible in the logs table
- Provides context for investigation
- Helps understand scope of changes

---

## Common Administrative Tasks

### Task 1: Onboarding a New Employee

**Scenario:** New farm manager starting Monday, needs full aquaculture access.

**Checklist:**

1. **Create User Account:**
   - Email: newmanager@farm.com
   - Full Name: New Manager
   - Role: User
   - Note temporary password: `TempPass9xK2!`

2. **Grant Permissions:**
   - Open Permissions Dialog
   - Grant "Aquaculture Operations" (includes all children)
   - Grant "Inventory Management"
   - Grant "Dashboard" (if not auto-granted)
   - Save permissions

3. **Share Credentials:**
   - Email user with login URL, email, temp password
   - CC HR for documentation
   - Request password change within 24 hours

4. **Verify Access:**
   - Ask user to log in and confirm modules visible
   - User should see: Dashboard, Inventory, Aquaculture (with children)

**Timeline:**
- Friday: Create account and grant permissions
- Monday: User logs in, changes password, starts work

---

### Task 2: Employee Offboarding

**Scenario:** Employee leaving company Friday, needs access removed.

**Checklist:**

1. **Deactivate User:**
   - Find user in Users list
   - Click delete icon
   - Confirm deactivation
   - User status changes to "Inactive"

2. **Verify Deactivation:**
   - User status shows red "Inactive" chip
   - User cannot log in (test if possible)

3. **Document in Activity Logs:**
   - Activity log automatically records deactivation
   - Note: "Deleted user user@example.com"

4. **Optional: Review User's Activity:**
   - Check activity logs for user's recent actions
   - Identify any critical operations done recently
   - Ensure handoff to replacement

**Timing:**
- Do NOT deactivate until employee's last day
- Deactivate at end of business day Friday
- Immediate effect - user locked out

---

### Task 3: Quarterly Permission Audit

**Scenario:** Company policy requires quarterly review of user access.

**Checklist:**

1. **Export User List:**
   - Navigate to Users page
   - Review all active users
   - Note users, roles, and creation dates

2. **Review Each User:**
   - For each user, click "Manage Permissions"
   - Verify permissions match current job role
   - Look for over-permissioned users
   - Identify inactive users with active status

3. **Make Adjustments:**
   - Revoke unnecessary permissions
   - Deactivate users no longer with company
   - Promote users if role changed

4. **Document Findings:**
   - Create audit report:
     ```
     Q4 2025 Access Audit
     Date: Nov 19, 2025
     Reviewed: 50 users
     Changes:
     - Revoked biofloc access from 3 users (role change)
     - Deactivated 2 users (no longer employed)
     - Promoted 1 user to admin
     ```

5. **Review Activity Logs:**
   - Filter: Last 90 days
   - Look for suspicious patterns
   - Verify all admin actions were authorized

**Frequency:**
- Quarterly (every 3 months)
- After major organizational changes
- When new modules deployed

---

### Task 4: Deploying a New Module

**Scenario:** Development team deployed "Growout" module, ready for production.

**Checklist:**

1. **Verify Module Exists:**
   - Navigate to Module Management
   - Find "Growout Management" module
   - Status should be "Disabled" initially

2. **Enable Module:**
   - Click toggle switch to ON
   - Module is now active

3. **Test Access:**
   - Log in as a test user (or create one)
   - Verify module appears in navigation
   - Test basic functionality

4. **Grant Permissions:**
   - Identify users who need access
   - For each user, grant "Growout" permission
   - Consider hierarchical structure (parent/child)

5. **Communicate to Users:**
   - Send announcement email:
     ```
     New Module Available: Growout Management

     We're excited to announce the Growout Management module
     is now available.

     If you need access, contact IT admin.

     Documentation: [link]
     ```

6. **Monitor Initial Usage:**
   - Check activity logs for module usage
   - Address any access issues
   - Gather user feedback

---

## Best Practices

### User Management Best Practices

**1. Use Descriptive Full Names**
- ✅ Good: "John Smith - Aquaculture Manager"
- ❌ Bad: "JS" or "John"
- Helps identify users quickly in logs

**2. Limit Admin Users**
- Only grant Admin role when absolutely necessary
- Regular users can perform most tasks with proper permissions
- Recommended: 2-3 admin users max for small teams

**3. Regular Account Reviews**
- Quarterly: Review all active users
- Monthly: Check for users who haven't logged in recently
- Immediately: Remove access for terminated employees

**4. Secure Password Sharing**
- Never share passwords in plain text email
- Use encrypted email or secure messaging
- Require password change on first login

**5. Document User Changes**
- Keep records of who was granted admin
- Note reasons for deactivations
- Track permission changes with business justification

---

### Permission Management Best Practices

**1. Principle of Least Privilege**
- Grant only the modules users need for their job
- Review permissions when job role changes
- Revoke unused permissions

**2. Use Hierarchical Grants**
- If user needs all aquaculture modules, grant parent
- Easier to manage than individual grants
- Automatically includes future child modules

**3. Test Permission Changes**
- Before granting to multiple users, test with one user
- Verify module functionality works as expected
- Confirm no unintended side effects

**4. Communicate Permission Changes**
- Notify users when granting new access
- Explain what they can do with new modules
- Provide training resources

**5. Regular Audits**
- Quarterly permission reviews
- Verify permissions match organizational chart
- Remove "permission creep" (accumulated unnecessary access)

---

### Module Management Best Practices

**1. Test Before Disabling**
- Check user impact count first
- Notify affected users in advance
- Have a rollback plan

**2. Communicate Module Changes**
- Announce module deployments
- Warn users before disabling modules
- Provide alternative solutions if needed

**3. Understand Hierarchy**
- Know parent-child relationships
- Predict cascading effects
- Disable children before parent if selective disable needed

**4. Critical Module Protection**
- Never attempt to disable Dashboard or Admin
- These are protected for a reason
- Contact developer if you think they should be disabled

**5. Document Module Changes**
- Keep change log of module status changes
- Note reasons for disabling modules
- Track which modules are actively used

---

### Security Best Practices

**1. Monitor Activity Logs**
- Daily: Check for suspicious logins
- Weekly: Review permission changes
- Monthly: Audit all admin actions

**2. Protect Admin Accounts**
- Use strong passwords (min 12 characters)
- Change passwords quarterly
- Enable 2FA if available (future feature)

**3. Immediate Offboarding**
- Deactivate users on their last day
- Don't wait until next week
- Check activity logs after deactivation

**4. Incident Response**
- If suspicious activity detected, deactivate user immediately
- Investigate using activity logs
- Document findings and actions taken

**5. Regular Backups**
- Ensure database backups are running
- Test restore procedures
- Keep activity logs in archive

---

## Troubleshooting

### Common Issues

#### Issue 1: Cannot Create User - "Email already exists"

**Cause:** Email address is already registered in the system.

**Solution:**
1. Search for the email in the Users list
2. Check if user is:
   - **Active:** User already exists, no need to create
   - **Inactive:** Reactivate the existing user instead
3. If user should be re-created:
   - Use a different email address (e.g., add a number)
   - OR contact developer to hard-delete the old account

---

#### Issue 2: User Cannot Access Module Despite Permission

**Possible Causes:**

**Cause A: Module is Disabled**
- Solution: Enable the module in Module Management

**Cause B: Parent Module is Disabled**
- Solution: Enable the parent module first

**Cause C: User is Inactive**
- Solution: Reactivate the user account

**Cause D: User is Admin but permissions not showing**
- Solution: Admins don't need explicit permissions, they auto-access all

**Debugging Steps:**
1. Navigate to Module Management → Verify module is enabled
2. Check if module has parent → Verify parent is enabled
3. Navigate to Users → Verify user status is "Active"
4. Check activity logs for recent permission changes
5. Ask user to log out and log back in (refresh session)

---

#### Issue 3: Cannot Disable Module - "Cannot disable critical module"

**Cause:** Attempting to disable Dashboard or Admin module.

**Explanation:**
- These modules are critical for system operation
- Disabling them would lock you out of the system
- This is a security protection

**Solution:**
- Accept that these modules cannot be disabled
- If you genuinely need to disable them (rare), contact developer
- Developer can modify via database if absolutely necessary

---

#### Issue 4: Forgot Temporary Password After User Creation

**Cause:** Temporary password is shown only once, not stored.

**Solution:**

**Option A: Reset User Password (if feature available)**
1. Find user in Users list
2. Click "Reset Password" button
3. New temporary password generated
4. Share with user securely

**Option B: Manual Password Reset (database access required)**
1. Contact developer or database admin
2. Request password reset for the user
3. Developer runs SQL update:
   ```sql
   -- Developer resets password
   UPDATE auth.users
   SET encrypted_password = crypt('NewTempPass123!', gen_salt('bf'))
   WHERE email = 'user@example.com';
   ```
4. Share new password with user

**Prevention:**
- Copy temporary password immediately when creating user
- Store in password manager temporarily
- Email user immediately after creation

---

#### Issue 5: Activity Logs Not Showing Recent Actions

**Possible Causes:**

**Cause A: Time Filter Too Restrictive**
- Solution: Change filter from "Last 1 day" to "Last 7 days"

**Cause B: Action Outside Date Range**
- Solution: Extend date range to "Last 30 days" or "Last 90 days"

**Cause C: Filtering by Wrong User/Module**
- Solution: Clear filters to show all actions

**Cause D: Action Actually Didn't Complete**
- Solution: Check if operation succeeded (look for success message)

**Debugging:**
1. Clear all filters (user, module, action type)
2. Set time period to "Last 7 days"
3. Look for your own recent actions (should appear)
4. If still missing, contact developer (logging may be broken)

---

#### Issue 6: Cannot Edit User - "Admin access required"

**Cause:** Your account doesn't have Admin role.

**Solution:**
1. **Verify Your Role:**
   - Ask another admin to check your user account
   - Navigate to Users → Find yourself → Check role

2. **If You Should Be Admin:**
   - Ask another admin to change your role to "Admin"
   - OR contact developer for database update

3. **If You're Not Admin:**
   - Request admin privileges from your supervisor
   - Admin creation requires approval
   - Cannot self-promote for security

---

### Error Messages Explained

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| "Admin access required" | You're not an admin | Request admin role or use admin account |
| "Cannot delete your own account" | Self-deletion prevention | Ask another admin to deactivate you |
| "Cannot disable critical module" | Dashboard/Admin protection | These modules cannot be disabled |
| "Email already exists" | Duplicate email | Use different email or reactivate existing |
| "User not found" | Invalid user ID | Refresh page, verify user exists |
| "Access denied" | Insufficient permissions | Grant module permission to user |
| "Cannot enable child module" | Parent is disabled | Enable parent module first |

---

## Getting Help

### For Admin Panel Issues

1. **Check this guide** - Most common tasks are documented
2. **Review activity logs** - Investigate recent changes
3. **Ask another admin** - Collaborate with team
4. **Contact IT support** - For technical issues
5. **Contact developer** - For bugs or feature requests

### Escalation Path

**Level 1: Self-Service**
- Review documentation
- Check activity logs
- Verify module status

**Level 2: Peer Support**
- Ask another admin
- Consult team lead
- Review company policies

**Level 3: IT Support**
- Submit support ticket
- Provide error messages
- Include screenshots

**Level 4: Developer**
- Report bugs
- Request database fixes
- Suggest feature enhancements

---

## Appendix: Admin Checklist

### Daily Tasks
- [ ] Check activity logs for unusual activity
- [ ] Monitor recent logins (last 24 hours)
- [ ] Respond to access requests

### Weekly Tasks
- [ ] Review pending user access requests
- [ ] Check for inactive users (no recent login)
- [ ] Verify critical modules are enabled

### Monthly Tasks
- [ ] Review all active users
- [ ] Audit admin user list
- [ ] Check module usage statistics
- [ ] Backup activity logs

### Quarterly Tasks
- [ ] Comprehensive permission audit
- [ ] Review and update module list
- [ ] Analyze activity log trends
- [ ] Update documentation
- [ ] Rotate admin passwords

### Annual Tasks
- [ ] Complete security audit
- [ ] Review all policies and procedures
- [ ] Update user training materials
- [ ] Archive old activity logs

---

**End of User Guide**

For technical details and architecture, see [Technical Guide](./technical-guide.md).
