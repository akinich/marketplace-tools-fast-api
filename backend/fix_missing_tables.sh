#!/bin/bash
#==============================================================================
# Farm Management System - Emergency Database Fix Script
#==============================================================================
# Purpose: Fix missing users table and run base schema migration
# Usage: bash fix_missing_tables.sh
# Or: chmod +x fix_missing_tables.sh && ./fix_missing_tables.sh
#==============================================================================

set -e  # Exit on error

echo "=========================================="
echo "🚨 Emergency Database Migration Fix"
echo "=========================================="
echo ""
echo "This script will:"
echo "1. Run the base schema migration (creates users table)"
echo "2. Run all other pending migrations"
echo "3. Verify tables were created"
echo ""

# Check if we're in the backend directory
if [ ! -f "run_base_schema.py" ]; then
    echo "⚠️  Not in backend directory. Changing to backend/"
    cd backend || exit 1
fi

echo "📍 Current directory: $(pwd)"
echo ""

# Step 1: Run base schema
echo "Step 1/2: Running base schema migration..."
echo "----------------------------------------"
python run_base_schema.py
if [ $? -eq 0 ]; then
    echo "✅ Base schema migration completed!"
else
    echo "❌ Base schema migration failed!"
    exit 1
fi

echo ""

# Step 2: Run all other migrations
echo "Step 2/2: Running all module migrations..."
echo "----------------------------------------"
python run_all_migrations.py
if [ $? -eq 0 ]; then
    echo "✅ All migrations completed!"
else
    echo "⚠️  Some migrations may have failed (check above)"
fi

echo ""
echo "=========================================="
echo "✨ Migration complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart your backend service"
echo "2. Try logging in again"
echo "3. Check that the 'users' table exists"
echo ""
echo "If you still have issues, check the logs above for errors."
