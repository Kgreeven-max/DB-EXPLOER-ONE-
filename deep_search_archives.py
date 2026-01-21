"""
Deep search for ATM/card transaction archive data.
"""
from dwha_connection import get_dwha_connection

def main():
    print("=" * 70)
    print("Deep Search for ATM/Card Transaction Archives")
    print("=" * 70)
    print()

    conn = get_dwha_connection()
    cursor = conn.cursor()

    # Search for ALL tables that might have transaction-level card data
    # Looking for tables with certain column patterns
    print("SEARCHING FOR TABLES WITH 'PANEntryMode' COLUMN:")
    print("-" * 60)
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE COLUMN_NAME = 'PANEntryMode'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    tables_with_pan = cursor.fetchall()
    for row in tables_with_pan:
        print(f"  {row[0]}.{row[1]}")
        try:
            cursor.execute(f"SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate), COUNT(*) FROM [{row[0]}].[{row[1]}]")
            dates = cursor.fetchone()
            print(f"    Date range: {dates[0]} to {dates[1]} ({dates[2]:,} rows)")
        except Exception as e:
            print(f"    Error getting dates: {str(e)[:60]}")
    print()

    # Check for tables with 'PointOfSaleEntryMode' column (alternative naming)
    print("SEARCHING FOR TABLES WITH 'PointOfSaleEntryMode' COLUMN:")
    print("-" * 60)
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE COLUMN_NAME = 'PointOfSaleEntryMode'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}.{row[1]}")
    print()

    # Check Copy schema (often used for backups)
    print("TABLES IN Copy SCHEMA:")
    print("-" * 60)
    cursor.execute("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'Copy'
        ORDER BY TABLE_NAME
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}")
    print()

    # Check Stage/Staging schema
    print("TABLES IN Stage AND Staging SCHEMAS:")
    print("-" * 60)
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA IN ('Stage', 'Staging')
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}.{row[1]}")
    print()

    # Look at dbo schema for possible backup tables
    print("TABLES IN dbo SCHEMA THAT MIGHT BE ATM-RELATED:")
    print("-" * 60)
    cursor.execute("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'dbo'
          AND (TABLE_NAME LIKE '%ATM%'
               OR TABLE_NAME LIKE '%Raw%'
               OR TABLE_NAME LIKE '%Dialog%'
               OR TABLE_NAME LIKE '%Card%'
               OR TABLE_NAME LIKE '%Trans%')
        ORDER BY TABLE_NAME
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}")
    print()

    # Check if there are any linked servers or external databases
    print("LINKED SERVERS:")
    print("-" * 60)
    try:
        cursor.execute("EXEC sp_linkedservers")
        for row in cursor.fetchall():
            print(f"  {row[0]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check all databases on this server
    print("ALL DATABASES ON THIS SERVER:")
    print("-" * 60)
    try:
        cursor.execute("SELECT name FROM sys.databases ORDER BY name")
        for row in cursor.fetchall():
            print(f"  {row[0]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check HistoryArchiveLog for information about archived data
    print("CONTENTS OF dbo.HistoryArchiveLog:")
    print("-" * 60)
    try:
        cursor.execute("SELECT TOP 20 * FROM dbo.HistoryArchiveLog ORDER BY 1 DESC")
        columns = [desc[0] for desc in cursor.description]
        print(f"  Columns: {columns}")
        for row in cursor.fetchall():
            print(f"  {row}")
    except Exception as e:
        print(f"  Error: {e}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
