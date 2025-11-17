# SQL Scripts - Version History

This folder contains all database migration scripts for the Farm Management System.

## Version History

### v1.0.0 (2025-11-17)
- Initial database schema creation
- Core tables: users, roles, modules, permissions
- Inventory tables: items, batches, transactions, purchase orders, suppliers, categories
- Biofloc tables: tanks, water tests, growth records, feed logs
- Activity logging table
- Database views and triggers
- Indexes for performance optimization

## How to Apply Scripts

1. Log in to your Supabase dashboard
2. Go to SQL Editor
3. Run scripts in order:
   - `v1.0.0_initial_schema.sql` - Creates all tables, views, triggers, and indexes

## Important Notes

- **Always backup your database before running migration scripts**
- Scripts are designed to be idempotent where possible (using IF NOT EXISTS)
- Each version builds on the previous version
- Do not modify old version files - create new versions instead

## Script Naming Convention

Format: `v{MAJOR}.{MINOR}.{PATCH}_{description}.sql`

Example: `v1.0.0_initial_schema.sql`

---

**Last Updated**: 2025-11-17
**Current Version**: v1.0.0
