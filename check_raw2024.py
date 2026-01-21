"""Check Raw_Production_2024 in ATMArchive."""
from dwha_connection import get_dwha_connection

conn = get_dwha_connection()
cursor = conn.cursor()

print("Checking ATMArchive Raw_Production 2024...")

# Try different possible table names
tables_to_try = [
    "ATMArchive.dbo.Raw_Production_2024",
    "ATMArchive.dbo.Raw_Production2024",
    "ATMArchive.AtmDialog.Raw_Production_2024",
    "ATMArchive.AtmDialog.Raw_Production2024"
]

for table in tables_to_try:
    try:
        cursor.execute(f"SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate), COUNT(*) FROM {table}")
        dates = cursor.fetchone()
        print(f"{table}:")
        print(f"  Date range: {dates[0]} to {dates[1]}")
        print(f"  Rows: {dates[2]:,}")

        # Check PAN 07 count
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE PANEntryMode = '07'")
        pan07 = cursor.fetchone()[0]
        print(f"  PAN-07 rows: {pan07:,}")
        break
    except Exception as e:
        print(f"{table}: {str(e)[:60]}")

cursor.close()
conn.close()
