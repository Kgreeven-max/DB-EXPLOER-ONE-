"""
Check RawImport7Day date range and try accessing ATMArchive via linked server.
"""
from dwha_connection import get_dwha_connection

def main():
    print("=" * 70)
    print("Checking RawImport7Day Dates and ATMArchive via Linked Server")
    print("=" * 70)
    print()

    conn = get_dwha_connection()
    cursor = conn.cursor()

    # Check Copy.RawImport7Day date range
    print("Copy.RawImport7Day Date Range:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT
                MIN([Local Transaction Date]) as MinDate,
                MAX([Local Transaction Date]) as MaxDate,
                COUNT(*) as TotalRows
            FROM Copy.RawImport7Day
        """)
        row = cursor.fetchone()
        print(f"  Date range: {row[0]} to {row[1]}")
        print(f"  Total rows: {row[2]:,}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check PAN Entry Mode values
    print("PAN Entry Mode Values in RawImport7Day:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT [PAN Entry Mode], COUNT(*) as cnt
            FROM Copy.RawImport7Day
            GROUP BY [PAN Entry Mode]
            ORDER BY cnt DESC
        """)
        for row in cursor.fetchall():
            print(f"  '{row[0]}': {row[1]:,}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Try accessing ATMArchive via linked server LVDCDWH01V
    print("Trying ATMArchive via LVDCDWH01V:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM [LVDCDWH01V].ATMArchive.INFORMATION_SCHEMA.TABLES
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]}.{row[1]}")
    except Exception as e:
        print(f"  Error: {str(e)[:200]}")
    print()

    # Check AtmDialog.RawImport date range
    print("AtmDialog.RawImport Date Range:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT
                MIN([Local Transaction Date]) as MinDate,
                MAX([Local Transaction Date]) as MaxDate,
                COUNT(*) as TotalRows
            FROM AtmDialog.RawImport
        """)
        row = cursor.fetchone()
        print(f"  Date range: {row[0]} to {row[1]}")
        print(f"  Total rows: {row[2]:,}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check if there's data before December 2024 in any accessible table
    print("Searching for any table with ATM data before Dec 2024:")
    print("-" * 60)

    # Check Mktg.TMP_RAWPRODUCTION_ETL
    try:
        cursor.execute("SELECT COUNT(*) FROM Mktg.TMP_RAWPRODUCTION_ETL")
        count = cursor.fetchone()[0]
        print(f"  Mktg.TMP_RAWPRODUCTION_ETL: {count:,} rows")
        if count > 0:
            cursor.execute("""
                SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate)
                FROM Mktg.TMP_RAWPRODUCTION_ETL
            """)
            dates = cursor.fetchone()
            print(f"    Date range: {dates[0]} to {dates[1]}")
    except Exception as e:
        print(f"  Mktg.TMP_RAWPRODUCTION_ETL: {str(e)[:60]}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
