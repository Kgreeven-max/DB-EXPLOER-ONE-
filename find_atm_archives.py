"""
Find where older ATM/PAN-07 transaction data is archived.
Looking for data from Jan 2024 - Nov 2024.
"""
from dwha_connection import get_dwha_connection

def main():
    print("=" * 70)
    print("Finding Older ATM Transaction Data")
    print("=" * 70)
    print()

    conn = get_dwha_connection()
    cursor = conn.cursor()

    # Search for tables with "ATM" or "Atm" in name
    print("TABLES WITH 'ATM' OR 'PAN' OR 'Card' OR 'Transaction' IN NAME:")
    print("-" * 60)
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME LIKE '%ATM%'
           OR TABLE_NAME LIKE '%PAN%'
           OR TABLE_NAME LIKE '%Card%Trans%'
           OR TABLE_NAME LIKE '%Debit%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}.{row[1]} ({row[2]})")
    print()

    # Check if there's a Production VIEW that might union multiple tables
    print("CHECKING AtmDialog.Production VIEW DEFINITION:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT OBJECT_DEFINITION(OBJECT_ID('AtmDialog.Production'))
        """)
        row = cursor.fetchone()
        if row and row[0]:
            print(row[0][:2000])
        else:
            print("  Could not get view definition")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check AtmDialog.Production view date range
    print("DATE RANGE IN AtmDialog.Production VIEW:")
    print("-" * 60)
    try:
        cursor.execute("SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate), COUNT(*) FROM AtmDialog.Production")
        row = cursor.fetchone()
        print(f"  Production view: {row[0]} to {row[1]} ({row[2]:,} rows)")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check PSCU tables (card processor)
    print("CHECKING History.PSCUTransactions:")
    print("-" * 60)
    try:
        cursor.execute("SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate), COUNT(*) FROM History.PSCUTransactions")
        row = cursor.fetchone()
        print(f"  PSCUTransactions: {row[0]} to {row[1]} ({row[2]:,} rows)")
    except Exception as e:
        print(f"  Error: {e}")

    # Check columns of PSCUTransactions
    try:
        cursor.execute("""
            SELECT TOP 1 *
            FROM History.PSCUTransactions
        """)
        columns = [desc[0] for desc in cursor.description]
        print(f"  Columns: {', '.join(columns[:15])}...")
    except Exception as e:
        print(f"  Columns error: {e}")
    print()

    # Look for any monthly archive tables for ATM
    print("SEARCHING FOR MONTHLY ATM ARCHIVE TABLES:")
    print("-" * 60)
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME LIKE '%Raw%2024%'
           OR TABLE_NAME LIKE '%ATM%2024%'
           OR TABLE_NAME LIKE '%202%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """)
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"  {row[0]}.{row[1]}")
    else:
        print("  No tables found with 2024 in name")
    print()

    # Check if AtmDialog has any archive/backup tables
    print("ALL TABLES IN AtmDialog SCHEMA WITH ROW COUNTS:")
    print("-" * 60)
    cursor.execute("""
        SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'AtmDialog'
        ORDER BY TABLE_NAME
    """)
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM AtmDialog.[{table}]")
            count = cursor.fetchone()[0]
            cursor.execute(f"SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate) FROM AtmDialog.[{table}]")
            dates = cursor.fetchone()
            print(f"  {table}: {count:,} rows ({dates[0]} to {dates[1]})")
        except:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM AtmDialog.[{table}]")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count:,} rows (no date column)")
            except Exception as e:
                print(f"  {table}: Error - {str(e)[:50]}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
