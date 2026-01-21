"""Quick scan of ATMArchive database."""
from dwha_connection import get_dwha_connection

conn = get_dwha_connection()
cursor = conn.cursor()

# List tables
print("TABLES IN ATMArchive:")
cursor.execute("""
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM ATMArchive.INFORMATION_SCHEMA.TABLES
    ORDER BY TABLE_SCHEMA, TABLE_NAME
""")
for row in cursor.fetchall():
    print(f"  {row[0]}.{row[1]}")

# Check for tables with PANEntryMode
print("\nTABLES WITH PANEntryMode COLUMN:")
cursor.execute("""
    SELECT TABLE_SCHEMA, TABLE_NAME
    FROM ATMArchive.INFORMATION_SCHEMA.COLUMNS
    WHERE COLUMN_NAME = 'PANEntryMode'
""")
for row in cursor.fetchall():
    print(f"  {row[0]}.{row[1]}")
    # Get date range
    try:
        cursor.execute(f"SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate), COUNT(*) FROM ATMArchive.[{row[0]}].[{row[1]}]")
        dates = cursor.fetchone()
        print(f"    {dates[0]} to {dates[1]} ({dates[2]:,} rows)")
    except Exception as e:
        print(f"    Error: {str(e)[:50]}")

cursor.close()
conn.close()
