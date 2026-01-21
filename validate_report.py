"""
Validation script to verify wallet activity report numbers
"""
import pandas as pd
from dwha_connection import get_dwha_connection

START_DATE = '2024-01-01'

conn = get_dwha_connection()
print('Connected to DWHA')
print()

# 1. Verify Mobile Wallet Transactions Total
print('=' * 60)
print('VALIDATION: Mobile Wallet Transactions')
print('=' * 60)
query_mw = f"""
SELECT
    COUNT(*) AS TotalCount,
    SUM(TransactionAmount) AS TotalAmount
FROM History.DigitalWalletTransactions w
INNER JOIN History.Account a ON w.AccountNumber = a.AccountNumber
WHERE w.LocalTransactionDate >= '{START_DATE}'
  AND a.CloseDate IS NULL
"""
df_mw = pd.read_sql(query_mw, conn)
mw_count = int(df_mw['TotalCount'].iloc[0])
mw_amount = float(df_mw['TotalAmount'].iloc[0])
print(f'Mobile Wallet Count: {mw_count:,}')
print(f'Mobile Wallet Amount: ${mw_amount:,.2f}')
print()

# 2. Verify PAN-07 Transactions Total (Archive + Current)
print('=' * 60)
print('VALIDATION: PAN-07 Transactions')
print('=' * 60)

# Archive
query_p07_archive = f"""
SELECT COUNT(*) AS TotalCount, SUM(AmountIn1) AS TotalAmount
FROM ATMArchive.dbo.RAW_Production2024 p
INNER JOIN History.Account a ON p.AccountNumber = a.AccountNumber
WHERE p.PANEntryMode = '07' AND p.LocalTransactionDate >= '{START_DATE}'
  AND a.CloseDate IS NULL
"""
df_p07_archive = pd.read_sql(query_p07_archive, conn)
p07_archive_count = int(df_p07_archive['TotalCount'].iloc[0])
p07_archive_amount = float(df_p07_archive['TotalAmount'].iloc[0])
print(f'PAN-07 Archive Count: {p07_archive_count:,}')
print(f'PAN-07 Archive Amount: ${p07_archive_amount:,.2f}')

# Current
query_p07_current = f"""
SELECT COUNT(*) AS TotalCount, SUM(AmountIn1) AS TotalAmount
FROM AtmDialog.Raw_Production p
INNER JOIN History.Account a ON p.AccountNumber = a.AccountNumber
WHERE p.PANEntryMode = '07' AND p.LocalTransactionDate >= '{START_DATE}'
  AND a.CloseDate IS NULL
"""
df_p07_current = pd.read_sql(query_p07_current, conn)
p07_current_count = int(df_p07_current['TotalCount'].iloc[0])
p07_current_amount = float(df_p07_current['TotalAmount'].iloc[0])
print(f'PAN-07 Current Count: {p07_current_count:,}')
print(f'PAN-07 Current Amount: ${p07_current_amount:,.2f}')

total_p07_count = p07_archive_count + p07_current_count
total_p07_amount = p07_archive_amount + p07_current_amount
print(f'PAN-07 TOTAL Count: {total_p07_count:,}')
print(f'PAN-07 TOTAL Amount: ${total_p07_amount:,.2f}')
print()

# 3. Calculate expected Card Tap (PAN-07 - Mobile Wallet)
print('=' * 60)
print('CALCULATED VALUES')
print('=' * 60)
expected_ct_amount = total_p07_amount - mw_amount
print(f'Card Tap Amount (PAN-07 - MW): ${expected_ct_amount:,.2f}')
print()

# 4. Compare with report output
print('=' * 60)
print('REPORT VALUES (from last run)')
print('=' * 60)
print('Mobile Wallet Total: $7,614,768,073.61')
print('Card Tap Total: $17,583,098,174.13')
print()

print('=' * 60)
print('COMPARISON')
print('=' * 60)
print(f'Mobile Wallet - DB Total: ${mw_amount:,.2f}')
print(f'Mobile Wallet - Report:   $7,614,768,073.61')
print(f'Match: {abs(mw_amount - 7614768073.61) < 1}')
print()
print(f'Card Tap - Calculated: ${expected_ct_amount:,.2f}')
print(f'Card Tap - Report:     $17,583,098,174.13')
print(f'Match: {abs(expected_ct_amount - 17583098174.13) < 1}')

conn.close()
print()
print('Validation complete.')
