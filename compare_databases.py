#!/usr/bin/env python3
"""
Database Comparison Tool
========================
Compares two PostgreSQL databases to verify they are identical.

Usage:
    python compare_databases.py

The script will:
1. Prompt for both database connection strings
2. Run comparison queries on both databases
3. Generate a detailed comparison report
4. Highlight any differences found
"""

import os
import sys
import psycopg2
import hashlib
from typing import Dict, List, Tuple, Any
from datetime import datetime


class DatabaseComparator:
    """Compares two PostgreSQL databases"""

    def __init__(self, db1_url: str, db2_url: str):
        self.db1_url = db1_url
        self.db2_url = db2_url
        self.differences = []

    def connect(self, db_url: str):
        """Create database connection"""
        return psycopg2.connect(db_url)

    def execute_query(self, conn, query: str) -> List[Tuple]:
        """Execute query and return results"""
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_tables(self, conn) -> List[str]:
        """Get all table names"""
        query = """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """
        results = self.execute_query(conn, query)
        return [row[0] for row in results]

    def get_table_row_count(self, conn, table_name: str) -> int:
        """Get row count for a table"""
        query = f"SELECT COUNT(*) FROM {table_name};"
        result = self.execute_query(conn, query)
        return result[0][0]

    def get_table_schema(self, conn, table_name: str) -> List[Tuple]:
        """Get table schema (columns)"""
        query = f"""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = '{table_name}'
            ORDER BY ordinal_position;
        """
        return self.execute_query(conn, query)

    def get_constraints(self, conn, constraint_type: str) -> List[Tuple]:
        """Get all constraints of a specific type"""
        query = f"""
            SELECT
                table_name,
                constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
            AND constraint_type = '{constraint_type}'
            ORDER BY table_name, constraint_name;
        """
        return self.execute_query(conn, query)

    def get_indexes(self, conn) -> List[Tuple]:
        """Get all indexes"""
        query = """
            SELECT
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """
        return self.execute_query(conn, query)

    def get_triggers(self, conn) -> List[Tuple]:
        """Get all triggers"""
        query = """
            SELECT
                event_object_table,
                trigger_name,
                action_statement
            FROM information_schema.triggers
            WHERE event_object_schema = 'public'
            ORDER BY event_object_table, trigger_name;
        """
        return self.execute_query(conn, query)

    def compare_lists(self, list1: List, list2: List, name: str) -> bool:
        """Compare two lists and report differences"""
        set1 = set(list1)
        set2 = set(list2)

        only_in_db1 = set1 - set2
        only_in_db2 = set2 - set1

        if only_in_db1 or only_in_db2:
            self.differences.append(f"\n❌ {name} MISMATCH:")
            if only_in_db1:
                self.differences.append(f"   Only in DB1 (farm2-app): {sorted(only_in_db1)}")
            if only_in_db2:
                self.differences.append(f"   Only in DB2 (marketplace): {sorted(only_in_db2)}")
            return False
        else:
            print(f"✅ {name} are identical")
            return True

    def compare_databases(self):
        """Main comparison function"""
        print("=" * 80)
        print("DATABASE COMPARISON REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        try:
            # Connect to both databases
            print("🔌 Connecting to databases...")
            conn1 = self.connect(self.db1_url)
            conn2 = self.connect(self.db2_url)
            print("✅ Connected to both databases\n")

            # Compare tables
            print("📊 Comparing tables...")
            tables1 = self.get_tables(conn1)
            tables2 = self.get_tables(conn2)
            tables_match = self.compare_lists(tables1, tables2, "Tables")

            if tables_match:
                print(f"   Found {len(tables1)} tables in both databases\n")

                # Compare row counts for each table
                print("📈 Comparing row counts...")
                row_count_match = True
                for table in sorted(tables1):
                    count1 = self.get_table_row_count(conn1, table)
                    count2 = self.get_table_row_count(conn2, table)

                    if count1 == count2:
                        print(f"   ✅ {table}: {count1} rows")
                    else:
                        print(f"   ❌ {table}: DB1={count1}, DB2={count2}")
                        self.differences.append(
                            f"\n❌ Row count mismatch in '{table}': DB1={count1}, DB2={count2}"
                        )
                        row_count_match = False

                if row_count_match:
                    print("\n✅ All row counts match\n")
                else:
                    print("\n⚠️  Row count mismatches found\n")

            # Compare constraints
            print("🔒 Comparing PRIMARY KEY constraints...")
            pk1 = self.get_constraints(conn1, "PRIMARY KEY")
            pk2 = self.get_constraints(conn2, "PRIMARY KEY")
            self.compare_lists(pk1, pk2, "Primary Keys")

            print("🔗 Comparing FOREIGN KEY constraints...")
            fk1 = self.get_constraints(conn1, "FOREIGN KEY")
            fk2 = self.get_constraints(conn2, "FOREIGN KEY")
            self.compare_lists(fk1, fk2, "Foreign Keys")

            print("🔑 Comparing UNIQUE constraints...")
            uq1 = self.get_constraints(conn1, "UNIQUE")
            uq2 = self.get_constraints(conn2, "UNIQUE")
            self.compare_lists(uq1, uq2, "Unique Constraints")

            print("✓ Comparing CHECK constraints...")
            chk1 = self.get_constraints(conn1, "CHECK")
            chk2 = self.get_constraints(conn2, "CHECK")
            self.compare_lists(chk1, chk2, "Check Constraints")

            # Compare indexes
            print("📇 Comparing indexes...")
            idx1 = self.get_indexes(conn1)
            idx2 = self.get_indexes(conn2)
            self.compare_lists(idx1, idx2, "Indexes")

            # Compare triggers
            print("⚡ Comparing triggers...")
            trg1 = self.get_triggers(conn1)
            trg2 = self.get_triggers(conn2)
            self.compare_lists(trg1, trg2, "Triggers")

            # Close connections
            conn1.close()
            conn2.close()

            # Print summary
            print("\n" + "=" * 80)
            print("COMPARISON SUMMARY")
            print("=" * 80)

            if not self.differences:
                print("✅ DATABASES ARE IDENTICAL!")
                print("\nBoth databases have:")
                print(f"  - Same tables ({len(tables1)})")
                print(f"  - Same row counts")
                print(f"  - Same constraints")
                print(f"  - Same indexes")
                print(f"  - Same triggers")
            else:
                print("⚠️  DIFFERENCES FOUND:")
                for diff in self.differences:
                    print(diff)

            print("=" * 80)

        except Exception as e:
            print(f"\n❌ Error during comparison: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point"""
    print("=" * 80)
    print("DATABASE COMPARISON TOOL")
    print("=" * 80)
    print("\nThis tool compares two PostgreSQL databases to verify they are identical.")
    print("\nYou will need the DATABASE_URL connection strings for both databases.")
    print("Format: postgresql://user:password@host:port/database\n")

    # Get database URLs
    print("Enter connection details:\n")

    db1_url = input("Database 1 URL (farm2-app-fast-api): ").strip()
    if not db1_url:
        print("❌ Database URL cannot be empty")
        sys.exit(1)

    db2_url = input("Database 2 URL (marketplace-tools-fast-api): ").strip()
    if not db2_url:
        print("❌ Database URL cannot be empty")
        sys.exit(1)

    print()

    # Run comparison
    comparator = DatabaseComparator(db1_url, db2_url)
    comparator.compare_databases()


if __name__ == "__main__":
    main()
