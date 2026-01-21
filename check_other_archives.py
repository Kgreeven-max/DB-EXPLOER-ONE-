"""
Check other possible archive sources for ATM data.
"""
from dwha_connection import get_dwha_connection

def main():
    print("=" * 70)
    print("Checking Other Archive Sources")
    print("=" * 70)
    print()

    conn = get_dwha_connection()
    cursor = conn.cursor()

    # Try SymArchive database
    print("CHECKING SymArchive DATABASE:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM SymArchive.INFORMATION_SCHEMA.TABLES
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}.{row[1]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check Copy.RawImport7Day
    print("CHECKING Copy.RawImport7Day:")
    print("-" * 60)
    try:
        cursor.execute("SELECT TOP 1 * FROM Copy.RawImport7Day")
        columns = [desc[0] for desc in cursor.description]
        print(f"  Columns: {', '.join(columns[:10])}...")
        cursor.execute("SELECT COUNT(*) FROM Copy.RawImport7Day")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count:,}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check dbo.PayPassTransactions (might be contactless)
    print("CHECKING dbo.PayPassTransactions:")
    print("-" * 60)
    try:
        cursor.execute("SELECT TOP 1 * FROM dbo.PayPassTransactions")
        columns = [desc[0] for desc in cursor.description]
        print(f"  Columns: {', '.join(columns)}")
        cursor.execute("SELECT COUNT(*) FROM dbo.PayPassTransactions")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count:,}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check personeticstransactions
    print("CHECKING dbo.personeticstransactions:")
    print("-" * 60)
    try:
        cursor.execute("SELECT TOP 1 * FROM dbo.personeticstransactions")
        columns = [desc[0] for desc in cursor.description]
        print(f"  Columns: {', '.join(columns[:15])}...")
        cursor.execute("SELECT COUNT(*) FROM dbo.personeticstransactions")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count:,}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Try linked server DWHADEV
    print("CHECKING LINKED SERVER DWHADEV:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM [DWHADEV].SymWarehouse.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME LIKE '%Raw%'
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}.{row[1]}")
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")
    print()

    # Check DataWarehouse database
    print("CHECKING DataWarehouse DATABASE:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM DataWarehouse.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME LIKE '%ATM%' OR TABLE_NAME LIKE '%Raw%' OR TABLE_NAME LIKE '%Card%Trans%'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}.{row[1]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check for any quarterly/monthly ATM tables
    print("SEARCHING FOR QUARTERLY/MONTHLY ATM TABLES:")
    print("-" * 60)
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME LIKE '%Raw%202%'
           OR TABLE_NAME LIKE '%ATM%202%'
           OR TABLE_NAME LIKE '%Dialog%202%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"  {row[0]}.{row[1]}")
    else:
        print("  No quarterly/monthly ATM tables found")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
