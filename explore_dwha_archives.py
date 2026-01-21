"""
Explore DWHA archive data locations and date ranges.
"""
from dwha_connection import get_dwha_connection

def main():
    print("=" * 70)
    print("DWHA Archive Data Explorer")
    print("=" * 70)
    print()

    conn = get_dwha_connection()
    cursor = conn.cursor()

    # Check tables in Archive schema
    print("TABLES IN Archive SCHEMA:")
    print("-" * 40)
    cursor.execute("""
        SELECT TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'Archive'
        ORDER BY TABLE_NAME
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} ({row[1]})")
    print()

    # Check date ranges in AtmDialog.Raw vs Raw_Production
    print("DATE RANGES IN AtmDialog TABLES:")
    print("-" * 40)

    try:
        cursor.execute("SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate), COUNT(*) FROM AtmDialog.Raw_Production")
        row = cursor.fetchone()
        print(f"  Raw_Production: {row[0]} to {row[1]} ({row[2]:,} rows)")
    except Exception as e:
        print(f"  Raw_Production: Error - {e}")

    try:
        cursor.execute("SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate), COUNT(*) FROM AtmDialog.Raw")
        row = cursor.fetchone()
        print(f"  Raw: {row[0]} to {row[1]} ({row[2]:,} rows)")
    except Exception as e:
        print(f"  Raw: Error - {e}")

    print()

    # Check date ranges in wallet tables
    print("DATE RANGES IN History.DigitalWallet TABLES:")
    print("-" * 40)

    try:
        cursor.execute("SELECT MIN(ActivationDate), MAX(ActivationDate), COUNT(*) FROM History.DigitalWalletActivations")
        row = cursor.fetchone()
        print(f"  DigitalWalletActivations: {row[0]} to {row[1]} ({row[2]:,} rows)")
    except Exception as e:
        print(f"  DigitalWalletActivations: Error - {e}")

    try:
        cursor.execute("SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate), COUNT(*) FROM History.DigitalWalletTransactions")
        row = cursor.fetchone()
        print(f"  DigitalWalletTransactions: {row[0]} to {row[1]} ({row[2]:,} rows)")
    except Exception as e:
        print(f"  DigitalWalletTransactions: Error - {e}")

    print()

    # Check Staging tables
    print("DATE RANGES IN Staging TABLES:")
    print("-" * 40)

    try:
        cursor.execute("SELECT MIN(ActivationDate), MAX(ActivationDate), COUNT(*) FROM Staging.DigitalWalletActivations")
        row = cursor.fetchone()
        print(f"  Staging.DigitalWalletActivations: {row[0]} to {row[1]} ({row[2]:,} rows)")
    except Exception as e:
        print(f"  Staging.DigitalWalletActivations: Error - {e}")

    try:
        cursor.execute("SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate), COUNT(*) FROM Staging.DigitalWalletTransactions")
        row = cursor.fetchone()
        print(f"  Staging.DigitalWalletTransactions: {row[0]} to {row[1]} ({row[2]:,} rows)")
    except Exception as e:
        print(f"  Staging.DigitalWalletTransactions: Error - {e}")

    print()

    # Check what's in the Archive schema in detail
    print("COLUMNS IN ARCHIVE TABLES:")
    print("-" * 40)
    cursor.execute("""
        SELECT t.TABLE_NAME, STRING_AGG(c.COLUMN_NAME, ', ') AS Columns
        FROM INFORMATION_SCHEMA.TABLES t
        JOIN INFORMATION_SCHEMA.COLUMNS c
          ON t.TABLE_SCHEMA = c.TABLE_SCHEMA AND t.TABLE_NAME = c.TABLE_NAME
        WHERE t.TABLE_SCHEMA = 'Archive'
        GROUP BY t.TABLE_NAME
        ORDER BY t.TABLE_NAME
    """)
    for row in cursor.fetchall():
        print(f"\n  {row[0]}:")
        print(f"    {row[1][:200]}...")

    print()

    # Look at Lookup.MonthlyArchiveTableList
    print("CONTENTS OF Lookup.MonthlyArchiveTableList:")
    print("-" * 40)
    try:
        cursor.execute("SELECT * FROM Lookup.MonthlyArchiveTableList")
        for row in cursor.fetchall():
            print(f"  {row}")
    except Exception as e:
        print(f"  Error: {e}")

    print()

    # Check for any wallet-related views
    print("WALLET-RELATED VIEWS:")
    print("-" * 40)
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_NAME LIKE '%Wallet%' OR TABLE_NAME LIKE '%wallet%'
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}.{row[1]}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
