# Communication Module Testing Guide

**Version:** 1.0.0
**Date:** 2025-11-23
**Related to:** Handover #7 - Telegram Module Migration & Navigation Updates

---

## 📋 OVERVIEW

This guide provides step-by-step instructions for testing the Communication module migration and navigation updates. Follow each section carefully and report any issues found.

---

## 🔧 PRE-DEPLOYMENT STEPS

### 1. Verify Database Migrations

Before deploying the frontend, ensure the database migrations have been run:

```bash
# Connect to your PostgreSQL database
psql -U farm2_user -d farm2_db

# Run the verification script
\i backend/migrations/verify_communication_module.sql
```

**Expected Output:**
- ✓ Communication parent module exists
- ✓ All 5 child modules present (com_telegram, com_smtp, com_webhooks, com_api_keys, com_websockets)
- ✓ Legacy telegram module renamed to telegram_legacy
- ✓ Full hierarchy displayed with proper parent-child relationships
- ✓ Admin users have permissions for Communication modules

**If verification fails:**
```bash
# Run migrations in order:
\i backend/migrations/007_communication_module.sql
\i backend/migrations/007_communication_module_patch.sql

# Re-run verification
\i backend/migrations/verify_communication_module.sql
```

### 2. Deploy Frontend Changes

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (if needed)
npm install

# Build for production
npm run build

# Or run in development mode
npm run dev
```

---

## ✅ TESTING CHECKLIST

### Phase 1: Admin User Testing

#### Test 1.1: Navigation Visibility

**Steps:**
1. Log in as an **Admin** user
2. Look at the sidebar navigation

**Expected Results:**
- [ ] "Communication" appears in the sidebar with 📡 icon
- [ ] Clicking "Communication" expands to show 5 child items:
  - [ ] Telegram
  - [ ] Email (SMTP)
  - [ ] Webhooks
  - [ ] API Keys
  - [ ] Real-time
- [ ] **No standalone "API Keys" menu item** outside of Communication

**Screenshot Locations:**
- Full sidebar with Communication expanded
- Communication module highlighted

---

#### Test 1.2: Navigation to Each Sub-Module

Test each Communication sub-module navigation:

| Sub-Module | Route | Expected Page Title | Status |
|------------|-------|---------------------|--------|
| Telegram | `/communication/telegram` | "Telegram Notifications" | [ ] |
| Email (SMTP) | `/communication/smtp` | "Email Management" / "SMTP Settings" | [ ] |
| Webhooks | `/communication/webhooks` | "Webhooks" | [ ] |
| API Keys | `/communication/api-keys` | "API Keys" | [ ] |
| Real-time | `/communication/websockets` | "Real-time Notifications" | [ ] |

**Steps for Each:**
1. Click Communication in sidebar to expand
2. Click the sub-module name
3. Verify correct page loads
4. Verify URL is correct
5. Verify page displays without errors

**Common Issues:**
- 404 Not Found → Route not properly configured
- Blank page → Component import error
- Wrong content → Wrong component mapped to route

---

#### Test 1.3: Telegram Settings Page Functionality

**Steps:**
1. Navigate to Communication > Telegram
2. Check Bot Status section
3. Check Channel Configuration section
4. Try updating a setting (if bot configured)

**Expected Results:**
- [ ] Bot status shows Connected/Disconnected
- [ ] Channel ID fields visible for Tickets, POs, Inventory
- [ ] Enable/Disable toggles work
- [ ] Granular event toggles expand when main toggle enabled
- [ ] Test notification buttons work (if channels configured)
- [ ] Save Settings button functional
- [ ] Link Telegram Account section visible

**Issues to Report:**
- Settings not loading
- Bot status always showing disconnected
- Unable to save changes
- Test notifications failing

---

#### Test 1.4: WebSocket Settings Page

**Steps:**
1. Navigate to Communication > Real-time
2. Check connection status
3. Review listed features

**Expected Results:**
- [ ] Connection status shows "Connected" (green) or "Disconnected" (warning)
- [ ] Real-time features listed:
  - Dashboard Statistics
  - Ticket Notifications
  - Low Stock Alerts
  - User Presence
- [ ] Technical information displayed
- [ ] No console errors

**Note:** If disconnected, this may be expected if WebSocket server is not configured.

---

#### Test 1.5: Module Refresh Behavior

**Steps:**
1. Navigate to `/communication/telegram`
2. Refresh the browser (F5)
3. Check sidebar state

**Expected Results:**
- [ ] Communication module **stays expanded** after refresh
- [ ] Telegram sub-item remains highlighted/selected
- [ ] Page content reloads correctly
- [ ] No navigation collapse or reset

---

### Phase 2: Permissions Testing

#### Test 2.1: Admin Panel - Module Permissions UI

**Steps:**
1. Go to Admin Panel > Users
2. Click "Edit" on a non-admin user
3. Click "Manage Permissions"

**Expected Results:**
- [ ] Communication appears as a **parent module** with expand/collapse icon
- [ ] Clicking expand shows 5 children indented:
  - Telegram
  - Email (SMTP)
  - Webhooks
  - API Keys
  - Real-time
- [ ] Each has a checkbox
- [ ] "Grant All" / "Deselect All" button visible for children
- [ ] Parent checkbox works (selects/deselects with children consideration)
- [ ] Individual child checkboxes work independently

**Screenshot:**
- Permissions dialog showing Communication hierarchy

---

#### Test 2.2: Grant Partial Permissions

**Steps:**
1. Open Manage Permissions for a test user
2. **Uncheck** Communication parent (if checked)
3. **Check only** "Email (SMTP)" sub-module
4. Save permissions
5. Close and reopen Manage Permissions

**Expected Results:**
- [ ] Only Email (SMTP) remains checked
- [ ] Communication parent unchecked (or indeterminate if UI supports it)
- [ ] Other Communication children unchecked

**Then:**
6. Log in as that test user (in incognito/private window)
7. Check sidebar navigation

**Expected Results:**
- [ ] Communication appears in sidebar
- [ ] Expanding Communication shows **only** Email (SMTP)
- [ ] Other sub-modules (Telegram, Webhooks, etc.) **not visible**
- [ ] Navigating to `/communication/telegram` shows 403 Forbidden or redirects

---

#### Test 2.3: Revoke All Communication Access

**Steps:**
1. Open Manage Permissions for test user
2. Deselect all Communication sub-modules
3. Deselect Communication parent
4. Save permissions
5. Log in as test user

**Expected Results:**
- [ ] Communication module **not visible** in sidebar
- [ ] Direct navigation to `/communication/smtp` shows 403 or redirects
- [ ] No Communication routes accessible

---

### Phase 3: Non-Admin User Testing

#### Test 3.1: User with Full Communication Access

**Setup:**
1. Create/use a non-admin test user
2. Grant permissions to Communication parent + all 5 children

**Steps:**
1. Log in as test user
2. Check sidebar navigation
3. Navigate to each Communication sub-module

**Expected Results:**
- [ ] Communication visible and expandable
- [ ] All 5 sub-modules accessible
- [ ] Each page loads correctly
- [ ] No admin-only features visible (e.g., user management)

---

#### Test 3.2: User with No Permissions

**Setup:**
1. Create/use a test user with **no module permissions**

**Steps:**
1. Log in as test user
2. Check sidebar

**Expected Results:**
- [ ] Only Dashboard visible
- [ ] No Communication or other modules shown
- [ ] Direct navigation to module routes redirects to dashboard or shows 403

---

### Phase 4: Edge Cases & Error Handling

#### Test 4.1: Direct URL Access

**Steps:**
1. While logged in, directly visit these URLs:
   - `/communication/telegram`
   - `/communication/smtp`
   - `/communication/webhooks`
   - `/communication/api-keys`
   - `/communication/websockets`

**Expected Results:**
- [ ] Each URL loads the correct page
- [ ] Sidebar highlights the correct item
- [ ] Communication parent auto-expands
- [ ] No 404 errors

---

#### Test 4.2: Old Route Handling (Optional)

If old routes existed (e.g., `/webhooks`, `/api-keys`):

**Steps:**
1. Visit `/webhooks`
2. Visit `/api-keys`

**Expected Behavior (Choose one based on implementation):**
- **Option A:** Redirect to `/communication/webhooks` and `/communication/api-keys`
- **Option B:** Show 404 with message to use new routes

**Result:**
- [ ] Old routes handled appropriately
- [ ] No broken links

---

#### Test 4.3: Browser Console Errors

**Steps:**
1. Open browser DevTools (F12)
2. Navigate through all Communication sub-modules
3. Check Console tab

**Expected Results:**
- [ ] No JavaScript errors
- [ ] No 404 for missing assets/imports
- [ ] No permission denied errors (unless testing unauthorized access)
- [ ] WebSocket connection warnings acceptable if WS not configured

---

### Phase 5: Cross-Browser Testing

Test on multiple browsers (at least 2):

| Browser | Version | Test Result | Issues |
|---------|---------|-------------|--------|
| Chrome | _____ | [ ] Pass | |
| Firefox | _____ | [ ] Pass | |
| Safari | _____ | [ ] Pass | |
| Edge | _____ | [ ] Pass | |

---

## 🐛 ISSUE REPORTING TEMPLATE

If you encounter issues, please report using this format:

```
**Issue:** [Brief description]

**Test Phase:** [e.g., Phase 1, Test 1.2]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happened]

**Screenshots:**
[Attach if applicable]

**Browser/Environment:**
- Browser: [Chrome 120, Firefox 121, etc.]
- OS: [Windows 11, macOS 14, etc.]
- User Role: [Admin / Non-admin]

**Console Errors:**
[Paste any errors from browser console]
```

---

## ✅ SIGN-OFF CHECKLIST

Once all tests pass, confirm:

- [ ] All navigation items display correctly
- [ ] All 5 Communication sub-modules accessible
- [ ] No console errors
- [ ] Permissions hierarchy works as expected
- [ ] Non-admin users see correct modules based on permissions
- [ ] Direct URL navigation works
- [ ] Page refreshes maintain sidebar state
- [ ] Cross-browser compatibility verified

**Tested By:** _________________
**Date:** _________________
**Signature/Approval:** _________________

---

## 📞 SUPPORT

If you encounter issues not covered in this guide or need assistance:

1. Check browser console for errors
2. Verify database migrations ran successfully
3. Check backend logs for API errors
4. Report issues using the template above

---

**End of Testing Guide**
