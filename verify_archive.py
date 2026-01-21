"""Verify ATMArchive.dbo.RAW_Production2024."""
from dwha_connection import get_dwha_connection
conn = get_dwha_connection()
cursor = conn.cursor()

cursor.execute("SELECT MIN(LocalTransactionDate), MAX(LocalTransactionDate), COUNT(*) FROM ATMArchive.dbo.RAW_Production2024")
dates = cursor.fetchone()
print(f"Date range: {dates[0]} to {dates[1]}")
print(f"Rows: {dates[2]:,}")

cursor.execute("SELECT COUNT(*) FROM ATMArchive.dbo.RAW_Production2024 WHERE PANEntryMode = '07'")
print(f"PAN-07 rows: {cursor.fetchone()[0]:,}")

conn.close()
