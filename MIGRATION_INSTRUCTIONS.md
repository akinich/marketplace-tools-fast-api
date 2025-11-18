# Database Migration Instructions - v1.1.0

## Overview
This migration adds hierarchical module support and user creation functionality to your Farm Management System.

## Changes in This Migration
1. **Hierarchical Modules**: Modules can now have parent-child relationships (e.g., Inventory → Dashboard, Items, etc.)
2. **Password-Based User Creation**: Admins can create users directly from the UI
3. **11 Inventory Sub-Modules**: Added granular access control for inventory features

## Steps to Apply Migration

### Step 1: Run Migration SQL in Supabase

1. Open your Supabase project dashboard
2. Go to **SQL Editor**
3. Create a new query
4. Copy the entire contents of `sql_scripts/v1.1.0_hierarchical_modules_and_user_creation.sql`
5. Paste into the SQL Editor
6. Click **Run** (or press Ctrl+Enter)

### Step 2: Verify Migration Success

You should see output messages like:
```
NOTICE: Inventory sub-modules created successfully
NOTICE: === Migration v1.1.0 Verification ===
NOTICE: Modules table: parent_module_id column exists = t
NOTICE: User_profiles table: password_hash column exists = t
NOTICE: Total modules count = 14
NOTICE: Inventory sub-modules count = 11
NOTICE: View user_accessible_modules exists = t
NOTICE: Function user_can_access_module exists = t
NOTICE: === Migration v1.1.0 Complete ===
```

### Step 3: Verify in Database Tables

Check the `modules` table:
```sql
SELECT id, module_key, module_name, parent_module_id, display_order
FROM modules
ORDER BY parent_module_id NULLS FIRST, display_order;
```

You should see:
- **Top-level modules** (parent_module_id = NULL): dashboard, inventory, biofloc, admin
- **Inventory sub-modules** (parent_module_id = <inventory_id>): 11 sub-modules

### Step 4: Test the New Features

After running the migration:

1. **Deploy Backend**: The backend code will automatically support the new structure
2. **Deploy Frontend**: The frontend will be updated to show hierarchical modules
3. **Test User Creation**: Admin can create users from Admin Panel → User Management
4. **Test Sub-Module Permissions**: Admin can assign specific inventory sub-modules to users

## New Inventory Sub-Modules

The following 11 sub-modules are created under "Inventory Management":

| # | Module Key | Module Name | Description |
|---|------------|-------------|-------------|
| 1 | inventory_dashboard | Dashboard | Inventory overview and key metrics |
| 2 | inventory_current_stock | Current Stock | View current stock levels |
| 3 | inventory_add_stock | Add Stock | Add new stock to inventory |
| 4 | inventory_adjustments | Adjustments | Stock adjustments and corrections |
| 5 | inventory_purchase_orders | Purchase Orders | Manage purchase orders |
| 6 | inventory_alerts | Alerts | Low stock and expiry alerts |
| 7 | inventory_history | History | Transaction history and audit trail |
| 8 | inventory_items | Item Master | Manage inventory items |
| 9 | inventory_categories | Categories | Manage item categories |
| 10 | inventory_suppliers | Suppliers | Manage suppliers and vendors |
| 11 | inventory_analytics | Analytics | Reports and analytics |

## Permission System Logic

### For Admin Users:
- Full access to all modules and sub-modules automatically

### For Regular Users:
- **Option 1**: Grant access to parent module (e.g., "Inventory Management")
  - If NO sub-module permissions exist → User gets ALL 11 sub-modules

- **Option 2**: Grant access to parent module + specific sub-modules
  - User gets ONLY the sub-modules explicitly granted
  - Example: User gets "Current Stock" + "Alerts" but not the others

### Example Scenarios:

**Scenario A - Full Inventory Access:**
```
✓ Inventory Management
  (no sub-module restrictions)

→ User sees all 11 inventory sub-modules
```

**Scenario B - Limited Inventory Access:**
```
✓ Inventory Management
  ✓ Current Stock
  ✓ Alerts
  ✓ Add Stock

→ User sees only these 3 sub-modules
```

**Scenario C - No Inventory Access:**
```
✗ Inventory Management

→ User sees no inventory sub-modules
```

## Rollback (If Needed)

If you need to rollback this migration:

```sql
-- Remove sub-modules
DELETE FROM modules WHERE parent_module_id IS NOT NULL;

-- Remove columns
ALTER TABLE modules DROP COLUMN IF EXISTS parent_module_id;
ALTER TABLE user_profiles DROP COLUMN IF EXISTS password_hash;

-- Drop function and view
DROP FUNCTION IF EXISTS user_can_access_module(UUID, VARCHAR);
DROP VIEW IF EXISTS user_accessible_modules;

-- Recreate original view (see v1.0.0_initial_schema.sql)
```

## Questions or Issues?

If you encounter any errors during migration, please provide:
1. The exact error message from Supabase SQL Editor
2. The query that caused the error
3. Screenshots if helpful

---

**Migration Created**: 2025-11-17
**Version**: 1.1.0
**Database**: Supabase PostgreSQL
