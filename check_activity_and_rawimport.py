"""
Check SymArchive.dbo.Activity2024 and Copy.RawImport7Day for ATM data.
"""
from dwha_connection import get_dwha_connection

def main():
    print("=" * 70)
    print("Checking Activity2024 and RawImport7Day")
    print("=" * 70)
    print()

    conn = get_dwha_connection()
    cursor = conn.cursor()

    # Check SymArchive.dbo.Activity2024
    print("SymArchive.dbo.Activity2024:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM SymArchive.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'Activity2024'
            ORDER BY ORDINAL_POSITION
        """)
        cols = cursor.fetchall()
        print("  Columns:")
        for col in cols:
            print(f"    {col[0]} ({col[1]})")
    except Exception as e:
        print(f"  Error getting columns: {e}")

    try:
        cursor.execute("SELECT COUNT(*) FROM SymArchive.dbo.Activity2024")
        count = cursor.fetchone()[0]
        print(f"\n  Row count: {count:,}")
    except Exception as e:
        print(f"  Error getting count: {e}")
    print()

    # Check Copy.RawImport7Day structure and date range
    print("Copy.RawImport7Day:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'Copy' AND TABLE_NAME = 'RawImport7Day'
            ORDER BY ORDINAL_POSITION
        """)
        cols = cursor.fetchall()
        print("  Columns (first 20):")
        for col in cols[:20]:
            print(f"    {col[0]} ({col[1]})")
        print(f"  ... (total {len(cols)} columns)")
    except Exception as e:
        print(f"  Error getting columns: {e}")
    print()

    # Check if RawImport7Day has PANEntryMode-like column
    print("Checking for PAN Entry Mode column in RawImport7Day:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'Copy' AND TABLE_NAME = 'RawImport7Day'
              AND (COLUMN_NAME LIKE '%PAN%' OR COLUMN_NAME LIKE '%Entry%' OR COLUMN_NAME LIKE '%Mode%')
        """)
        cols = cursor.fetchall()
        if cols:
            for col in cols:
                print(f"  {col[0]}")
        else:
            print("  No PAN/Entry/Mode columns found")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check AtmDialog.RawImport structure
    print("AtmDialog.RawImport:")
    print("-" * 60)
    try:
        cursor.execute("SELECT COUNT(*) FROM AtmDialog.RawImport")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count:,}")

        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'AtmDialog' AND TABLE_NAME = 'RawImport'
              AND (COLUMN_NAME LIKE '%PAN%' OR COLUMN_NAME LIKE '%Entry%' OR COLUMN_NAME LIKE '%Date%')
            ORDER BY ORDINAL_POSITION
        """)
        cols = cursor.fetchall()
        print("  PAN/Entry/Date columns:")
        for col in cols:
            print(f"    {col[0]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check if there's Raw_Production data earlier in linked servers
    print("CHECKING LINKED SERVER LVDCDWH01V:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT name
            FROM [LVDCDWH01V].master.sys.databases
            ORDER BY name
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}")
    except Exception as e:
        print(f"  Error: {str(e)[:100]}")
    print()

    # Check FMHistory2024 for activity data
    print("SymArchive.dbo.FMHistory2024:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM SymArchive.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'FMHistory2024'
            ORDER BY ORDINAL_POSITION
        """)
        cols = cursor.fetchall()
        print("  Columns (first 10):")
        for col in cols[:10]:
            print(f"    {col[0]} ({col[1]})")
        print(f"  ... (total {len(cols)} columns)")
    except Exception as e:
        print(f"  Error: {e}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
