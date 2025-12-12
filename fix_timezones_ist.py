#!/usr/bin/env python3
"""
Script to standardize all datetime.now() calls to IST across all service files.
Converts naive datetime.now() and UTC datetime.now(timezone.utc) to now_ist()
"""

import re
from pathlib import Path

# Files to fix
SERVICE_FILES = [
    'backend/app/services/batch_tracking_service.py',
    'backend/app/services/wastage_tracking_service.py',
    'backend/app/services/label_service.py',
    'backend/app/services/mrp_label_service.py',
    'backend/app/services/admin_service.py',
    'backend/app/services/settings_service.py',
    'backend/app/services/zoho_vendor_service.py',
    'backend/app/services/zoho_item_service.py',
    'backend/app/services/zoho_customer_service.py',
]

def fix_file(filepath: str):
    """Fix timezone usage in a single file."""
    path = Path(filepath)
    if not path.exists():
        print(f"⚠️  Skipping {filepath} (not found)")
        return False
    
    with open(path, 'r') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # 1. Add timezone import if datetime is imported but not our helper
    if 'from datetime import' in content and 'from app.utils.timezone import now_ist' not in content:
        # Find the datetime import line
        import_match = re.search(r'from datetime import ([^\n]+)', content)
        if import_match:
            # Add our import after datetime import
            datetime_import_line = import_match.group(0)
            new_imports = datetime_import_line + '\nfrom app.utils.timezone import now_ist'
            content = content.replace(datetime_import_line, new_imports, 1)
            changes.append("Added timezone import")
    
    # 2. Replace datetime.now(timezone.utc) with now_ist()
    utc_pattern = r'datetime\.now\(timezone\.utc\)'
    utc_matches = re.findall(utc_pattern, content)
    if utc_matches:
        content = re.sub(utc_pattern, 'now_ist()', content)
        changes.append(f"Replaced {len(utc_matches)} UTC datetime.now() calls")
    
    # 3. Replace datetime.now() with now_ist() (but not in strings)
    # Be careful not to replace commented lines or strings
    naive_pattern = r'(?<![\'"#])datetime\.now\(\)(?!\))'
    naive_matches = re.findall(naive_pattern, content)
    if naive_matches:
        content = re.sub(naive_pattern, 'now_ist()', content)
        changes.append(f"Replaced {len(naive_matches)} naive datetime.now() calls")
    
    # Only write if changed
    if content != original_content:
        with open(path, 'w') as f:
            f.write(content)
        print(f"✅ {filepath}")
        for change in changes:
            print(f"   - {change}")
        return True
    else:
        print(f"⏭️  {filepath} (no changes needed)")
        return False

def main():
    print("=" * 70)
    print("STANDARDIZING ALL SERVICES TO IST (GMT+5:30)")
    print("=" * 70)
    print()
    
    fixed_count = 0
    for filepath in SERVICE_FILES:
        if fix_file(filepath):
            fixed_count += 1
        print()
    
    print("=" * 70)
    print(f"✅ COMPLETE: Fixed {fixed_count}/{len(SERVICE_FILES)} files")
    print("=" *70)
    print()
    print("Next steps:")
    print("1. Run: python3 -m py_compile backend/app/services/*.py")
    print("2. Test the changes")
    print("3. Commit: git add backend/app/services/ backend/app/utils/")
    print()

if __name__ == '__main__':
    main()
