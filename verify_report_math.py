"""
Verify report math against database totals
"""
import pandas as pd
from dwha_connection import get_dwha_connection

START_DATE = '2024-01-01'

conn = get_dwha_connection()
print("Connected to DWHA")
print()

# 1. Get PAN-07 totals from database
print("=" * 70)
print("VERIFYING PAN-07 TOTALS FROM DATABASE")
print("=" * 70)

# Archive
query_archive = f"""
SELECT
    COUNT(*) AS TxnCount,
    SUM(AmountIn1) AS TotalAmount
FROM ATMArchive.dbo.RAW_Production2024 p
INNER JOIN History.Account a ON p.AccountNumber = a.AccountNumber
WHERE p.PANEntryMode = '07'
  AND p.LocalTransactionDate >= '{START_DATE}'
  AND a.CloseDate IS NULL
"""
df_archive = pd.read_sql(query_archive, conn)
archive_count = int(df_archive['TxnCount'].iloc[0])
archive_amount = float(df_archive['TotalAmount'].iloc[0])
print(f"PAN-07 Archive: {archive_count:,} txns, ${archive_amount:,.2f}")

# Current
query_current = f"""
SELECT
    COUNT(*) AS TxnCount,
    SUM(AmountIn1) AS TotalAmount
FROM AtmDialog.Raw_Production p
INNER JOIN History.Account a ON p.AccountNumber = a.AccountNumber
WHERE p.PANEntryMode = '07'
  AND p.LocalTransactionDate >= '{START_DATE}'
  AND a.CloseDate IS NULL
"""
df_current = pd.read_sql(query_current, conn)
current_count = int(df_current['TxnCount'].iloc[0])
current_amount = float(df_current['TotalAmount'].iloc[0])
print(f"PAN-07 Current: {current_count:,} txns, ${current_amount:,.2f}")

db_total_count = archive_count + current_count
db_total_amount = archive_amount + current_amount
print(f"\nDATABASE TOTAL PAN-07: {db_total_count:,} txns, ${db_total_amount:,.2f}")

conn.close()

# 2. Compare with report
print()
print("=" * 70)
print("REPORT VALUES")
print("=" * 70)
report_mw_count = 217873761
report_mw_amount = 6235435887.30
report_ct_count = 416171193
report_ct_amount = 27362113062.66

print(f"Mobile Wallet Taps: {report_mw_count:,} txns, ${report_mw_amount:,.2f}")
print(f"Physical Card Taps: {report_ct_count:,} txns, ${report_ct_amount:,.2f}")

report_total_count = report_mw_count + report_ct_count
report_total_amount = report_mw_amount + report_ct_amount
print(f"\nREPORT TOTAL: {report_total_count:,} txns, ${report_total_amount:,.2f}")

# 3. Comparison
print()
print("=" * 70)
print("COMPARISON")
print("=" * 70)
print(f"Database Total:  {db_total_count:,} txns, ${db_total_amount:,.2f}")
print(f"Report Total:    {report_total_count:,} txns, ${report_total_amount:,.2f}")
print()

count_diff = db_total_count - report_total_count
amount_diff = db_total_amount - report_total_amount

print(f"Count Difference: {count_diff:,}")
print(f"Amount Difference: ${amount_diff:,.2f}")

if count_diff == 0 and abs(amount_diff) < 1:
    print("\n✓ MATH VERIFIED - Totals match!")
else:
    print("\n⚠ DISCREPANCY FOUND")
