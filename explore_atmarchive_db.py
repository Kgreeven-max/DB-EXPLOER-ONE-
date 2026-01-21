"""
Explore the ATMArchive database for historical ATM transaction data.
"""
from dwha_connection import get_dwha_connection

def main():
    print("=" * 70)
    print("Exploring ATMArchive Database")
    print("=" * 70)
    print()

    conn = get_dwha_connection()
    cursor = conn.cursor()

    # List all schemas in ATMArchive
    print("SCHEMAS IN ATMArchive DATABASE:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT DISTINCT TABLE_SCHEMA
            FROM ATMArchive.INFORMATION_SCHEMA.TABLES
            ORDER BY TABLE_SCHEMA
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # List all tables in ATMArchive
    print("ALL TABLES IN ATMArchive DATABASE:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
            FROM ATMArchive.INFORMATION_SCHEMA.TABLES
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}.{row[1]} ({row[2]})")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check for tables with PANEntryMode in ATMArchive
    print("TABLES WITH 'PANEntryMode' COLUMN IN ATMArchive:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM ATMArchive.INFORMATION_SCHEMA.COLUMNS
            WHERE COLUMN_NAME = 'PANEntryMode'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        tables = cursor.fetchall()
        for row in tables:
            print(f"  {row[0]}.{row[1]}")
            # Get date range
            try:
                cursor.execute(f"""
                    SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate), COUNT(*)
                    FROM ATMArchive.[{row[0]}].[{row[1]}]
                """)
                dates = cursor.fetchone()
                print(f"    Date range: {dates[0]} to {dates[1]} ({dates[2]:,} rows)")
            except Exception as e2:
                print(f"    Error getting dates: {str(e2)[:60]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Look at column structure of key tables
    print("CHECKING COLUMN STRUCTURE OF ATMArchive TABLES:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM ATMArchive.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        tables = cursor.fetchall()
        for row in tables[:5]:  # First 5 tables
            print(f"\n  {row[0]}.{row[1]}:")
            try:
                cursor.execute(f"""
                    SELECT TOP 5 COLUMN_NAME
                    FROM ATMArchive.INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = '{row[0]}' AND TABLE_NAME = '{row[1]}'
                    ORDER BY ORDINAL_POSITION
                """)
                cols = [c[0] for c in cursor.fetchall()]
                print(f"    First 5 columns: {', '.join(cols)}")
            except Exception as e2:
                print(f"    Error: {str(e2)[:60]}")
    except Exception as e:
        print(f"  Error: {e}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
