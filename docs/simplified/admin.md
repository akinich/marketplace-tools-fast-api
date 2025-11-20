# Admin Module - Simple Guide 👥

## What Does This Module Do?

The Admin module is like being the "manager" of the app. You control:
- Who can use the app (users)
- What each person can access (permissions)
- See what people have been doing (activity logs)

**Note:** Only people with "Admin" role can use this module!

## Main Sections

### 1. User Management

Think of this as your team roster. You can see everyone who uses the app.

#### Viewing Users

1. Click **Admin** in the menu
2. Click **Users**
3. You'll see a list showing:
   - Person's name
   - Email address
   - Role (Admin or User)
   - Status (Active or Inactive)

**What the colors mean:**
- 🟢 Green "Active" = Person can log in
- 🔴 Red "Inactive" = Person cannot log in

#### Adding a New Person

**When:** A new employee joins and needs access

**Steps:**
1. Click **+ Add User** button
2. Fill in:
   - **Email:** Their work email (they'll use this to log in)
   - **Full Name:** Their complete name
   - **Role:** Choose Admin or User
     - **User** = Regular person (most common)
     - **Admin** = Manager with full access (use carefully!)
3. Click **Create User**
4. **IMPORTANT:** A temporary password will show up - copy it!
5. Give this password to the new person securely (don't put it in a text message!)

#### Changing Someone's Information

**When:** Someone's role changes or they need to be deactivated

**Steps:**
1. Find the person in the list
2. Click the pencil ✏️ icon
3. Change what you need:
   - Name (if they changed it)
   - Role (promote to Admin or demote to User)
   - Status (Active/Inactive)
4. Click **Save Changes**

#### Removing Someone

**When:** Someone leaves the company or no longer needs access

**Steps:**
1. Find the person in the list
2. Click the trash can 🗑️ icon
3. Confirm you want to remove them
4. They're now marked "Inactive" (they can't log in anymore)

**Note:** You can't delete yourself! (This prevents you from locking yourself out)

---

### 2. Module Management

Modules are different sections of the app (like Inventory, Biofloc, etc.). You can turn them on or off.

#### Viewing Modules

1. Click **Admin** in the menu
2. Click **Module Management**
3. You'll see cards for each module with:
   - Name (e.g., "Inventory Management")
   - What it does
   - ON/OFF switch

#### Turning a Module ON

**When:** You want people to start using a feature

**Steps:**
1. Find the module card
2. Click the switch to turn it **ON** (green)
3. Done! People with permission can now use it

#### Turning a Module OFF

**When:** You want to disable a feature

**WARNING:** This removes access for EVERYONE using it!

**Steps:**
1. Find the module card
2. Click the switch to turn it **OFF**
3. A warning will pop up showing:
   - How many people will lose access
   - List of affected users
4. Click **Disable Module** if you're sure, or **Cancel** to stop

**Note:** Some modules like "Dashboard" and "Admin" can NEVER be turned off (for safety!)

---

### 3. Permission Management

Permissions control which modules each person can see and use.

**Important Rules:**
- **Admin users** automatically see everything (you can't change this)
- **Regular users** only see what you give them access to
- **Dashboard** is automatically available to everyone

#### Giving Someone Access to a Module

**When:** A person needs to use a new feature

**Steps:**
1. Go to **Admin** → **Users**
2. Find the person
3. Click the key 🔑 icon (Manage Permissions)
4. A window pops up showing all modules
5. Check the boxes for modules they should access:
   - ☑️ Checked = They can use it
   - ☐ Unchecked = They cannot use it
6. Click **Save**
7. Done! They can now see those modules in their menu

**Example:**
```
John needs to track inventory and manage fish tanks:
☑️ Inventory Management
☑️ Biofloc Management
☐ Admin (he's not an admin)
```

#### Removing Someone's Access

**When:** A person changes roles and no longer needs certain features

**Steps:**
1. Open their permissions (same as above)
2. Uncheck the boxes for modules to remove
3. Click **Save**
4. They immediately lose access to those modules

---

### 4. Activity Logs

This is like a security camera for the app - it records everything that happens!

#### What Gets Recorded?

- When people log in/out
- When users are added or removed
- When permissions are changed
- When modules are turned on/off

#### Viewing Activity Logs

1. Click **Admin** in the menu
2. Click **Activity Logs**
3. You'll see a list showing:
   - Date and time
   - Who did it
   - What they did
   - Which module was affected

#### Filtering Logs

**To find specific activities:**

1. Use the filter dropdowns:
   - **Time Period:** Last 7 days, 30 days, etc.
   - **User:** See only one person's actions
   - **Module:** See changes to one module
   - **Action Type:** See only specific types of actions
2. Click **Apply Filters**
3. The list updates to show only matching records

**Example Use Case:**

*"Someone said they lost access to Inventory. When did that happen?"*

1. Filter by: Module = "Inventory"
2. Filter by: Action Type = "update_permissions"
3. Look at recent dates
4. Find the entry showing permission removal
5. You'll see who removed it and when!

---

## Common Tasks

### Task: Onboarding a New Employee

**Checklist:**
- [ ] Create their user account
- [ ] Copy the temporary password
- [ ] Give them access to needed modules
- [ ] Send them their login info securely
- [ ] Ask them to change password after first login

### Task: Employee Leaving the Company

**Checklist:**
- [ ] Remove their account (mark inactive)
- [ ] Verify they can't log in anymore
- [ ] Check activity logs for their recent actions
- [ ] Document the removal

### Task: Someone Needs New Access

**Checklist:**
- [ ] Find their user account
- [ ] Open permissions
- [ ] Add the new module
- [ ] Save and tell them it's ready

---

## Quick Reference

### User Roles Explained

| Role | What They Can Do | When to Use |
|------|-----------------|-------------|
| **User** | Use modules they're given access to | Most people - farm workers, operators |
| **Admin** | Everything! Manage users, control all modules | Managers, supervisors (only 2-3 people) |

### Module Status Colors

| Color | Meaning |
|-------|---------|
| 🟢 Green Switch | Module is ON and working |
| Gray Switch | Module is OFF (disabled) |
| Red "Critical" | Cannot be turned off (protected) |

### Permission Tips

✅ **Good Practice:**
- Only give people access to what they need for their job
- Review permissions every few months
- Remove access when people change jobs

❌ **Bad Practice:**
- Giving everyone admin access (too risky!)
- Keeping old employees active after they leave
- Never checking who has access to what

---

## Troubleshooting

### Problem: Can't Add a New User - "Email Already Exists"

**What it means:** That email is already in the system

**Fix:**
1. Search for the email in the users list
2. If you find them and they're inactive, just activate them
3. If you find them and they're active, they don't need a new account!

### Problem: Person Can't See a Module Even Though I Gave Permission

**Possible causes and fixes:**

**Check 1:** Is the module turned ON?
- Go to Module Management
- Make sure the module switch is green/ON

**Check 2:** Is their account active?
- Go to Users
- Make sure their status is green "Active"

**Check 3:** Did they log out and back in?
- Ask them to log out completely
- Then log back in
- This refreshes their permissions

### Problem: Can't Turn Off a Module - "Cannot Disable Critical Module"

**What it means:** You're trying to turn off Dashboard or Admin module

**Why it won't let you:** These are essential! If you turn them off, nobody could use the app or manage it anymore

**Fix:** You can't turn these off (and shouldn't need to!)

---

## Safety Rules

🔒 **Never share admin passwords** - Each person should have their own account

⚠️ **Be careful with admin role** - Only give it to people who really need it

📋 **Check logs regularly** - Look for anything suspicious

🚫 **Can't delete yourself** - The app prevents this so you don't lock yourself out

---

## Need More Help?

- Check the activity logs to see what happened
- Ask another admin for assistance
- Contact your IT support team

Remember: Admin tools are powerful - use them carefully!
