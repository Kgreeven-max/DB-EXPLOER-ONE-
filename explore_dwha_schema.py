"""
Explore DWHA database schema to find archive tables.
"""
from dwha_connection import get_dwha_connection

def main():
    print("=" * 70)
    print("DWHA Database Schema Explorer")
    print("=" * 70)
    print()

    conn = get_dwha_connection()
    cursor = conn.cursor()

    # List all schemas
    print("SCHEMAS IN DATABASE:")
    print("-" * 40)
    cursor.execute("""
        SELECT DISTINCT TABLE_SCHEMA
        FROM INFORMATION_SCHEMA.TABLES
        ORDER BY TABLE_SCHEMA
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}")
    print()

    # List tables in AtmDialog schema
    print("TABLES IN AtmDialog SCHEMA:")
    print("-" * 40)
    cursor.execute("""
        SELECT TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'AtmDialog'
        ORDER BY TABLE_NAME
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} ({row[1]})")
    print()

    # List tables in History schema
    print("TABLES IN History SCHEMA:")
    print("-" * 40)
    cursor.execute("""
        SELECT TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'History'
        ORDER BY TABLE_NAME
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} ({row[1]})")
    print()

    # Search for any tables with 'Archive', 'Wallet', or 'Raw' in the name
    print("TABLES WITH 'Archive' OR 'Wallet' OR 'Raw' IN NAME:")
    print("-" * 40)
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME LIKE '%Archive%'
           OR TABLE_NAME LIKE '%Wallet%'
           OR TABLE_NAME LIKE '%Raw%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}.{row[1]}")
    print()

    # Check columns of Raw_Production to understand structure
    print("COLUMNS IN AtmDialog.Raw_Production:")
    print("-" * 40)
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'AtmDialog' AND TABLE_NAME = 'Raw_Production'
        ORDER BY ORDINAL_POSITION
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} ({row[1]})")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
