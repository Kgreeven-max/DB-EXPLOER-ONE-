"""
Explore card-related tables for historical transaction data.
"""
from dwha_connection import get_dwha_connection

def main():
    print("=" * 70)
    print("Exploring Card Transaction Tables")
    print("=" * 70)
    print()

    conn = get_dwha_connection()
    cursor = conn.cursor()

    # Check Operations.CardReportingTransactions
    print("Operations.CardReportingTransactions:")
    print("-" * 60)
    try:
        cursor.execute("SELECT TOP 1 * FROM Operations.CardReportingTransactions")
        columns = [desc[0] for desc in cursor.description]
        print(f"  Columns: {', '.join(columns)}")
        cursor.execute("SELECT COUNT(*) FROM Operations.CardReportingTransactions")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count:,}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check Mktg.DebitCardTransactions
    print("Mktg.DebitCardTransactions:")
    print("-" * 60)
    try:
        cursor.execute("SELECT TOP 1 * FROM Mktg.DebitCardTransactions")
        columns = [desc[0] for desc in cursor.description]
        print(f"  Columns: {', '.join(columns)}")
        cursor.execute("SELECT COUNT(*) FROM Mktg.DebitCardTransactions")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count:,}")
        # Check date range
        cursor.execute("SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate) FROM Mktg.DebitCardTransactions")
        dates = cursor.fetchone()
        print(f"  Date range: {dates[0]} to {dates[1]}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check MbrRewards.DebitCardTrans
    print("MbrRewards.DebitCardTrans:")
    print("-" * 60)
    try:
        cursor.execute("SELECT TOP 1 * FROM MbrRewards.DebitCardTrans")
        columns = [desc[0] for desc in cursor.description]
        print(f"  Columns: {', '.join(columns)}")
        cursor.execute("SELECT COUNT(*) FROM MbrRewards.DebitCardTrans")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count:,}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check if there's a view that might combine data
    print("CHECKING FOR COMBINED VIEWS IN dbo SCHEMA:")
    print("-" * 60)
    cursor.execute("""
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_SCHEMA = 'dbo'
          AND (TABLE_NAME LIKE '%Card%' OR TABLE_NAME LIKE '%ATM%' OR TABLE_NAME LIKE '%Raw%')
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}")
    print()

    # Check History.EFT table
    print("History.EFT:")
    print("-" * 60)
    try:
        cursor.execute("SELECT TOP 1 * FROM History.EFT")
        columns = [desc[0] for desc in cursor.description]
        print(f"  Columns: {', '.join(columns)}")
        cursor.execute("SELECT COUNT(*) FROM History.EFT")
        count = cursor.fetchone()[0]
        print(f"  Row count: {count:,}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    # Check if Mktg.DebitCardTransactions has PANEntryMode
    print("Checking Mktg.DebitCardTransactions for PANEntryMode:")
    print("-" * 60)
    try:
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'Mktg' AND TABLE_NAME = 'DebitCardTransactions'
            ORDER BY ORDINAL_POSITION
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]} ({row[1]})")
    except Exception as e:
        print(f"  Error: {e}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
