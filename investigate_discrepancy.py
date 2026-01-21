"""
Investigate discrepancies between Mobile Wallet and PAN-07 data
"""
import pandas as pd
from dwha_connection import get_dwha_connection

conn = get_dwha_connection()
print('Connected to DWHA')
print()

# Pick specific accounts with discrepancies to investigate
# Try with LIKE to handle padding
test_accounts = ['%943289', '%217565', '%820377']  # From earlier analysis

for test_account in test_accounts:
    print(f'Investigating account: {test_account}')
    print('=' * 70)

    # Check Mobile Wallet Transactions
    print('\n--- MOBILE WALLET TRANSACTIONS ---')
    query_mw = f"""
    SELECT
        COUNT(*) AS TxnCount,
        SUM(TransactionAmount) AS TotalAmount,
        MIN(LocalTransactionDate) AS Earliest,
        MAX(LocalTransactionDate) AS Latest
    FROM History.DigitalWalletTransactions
    WHERE AccountNumber LIKE '{test_account}'
      AND LocalTransactionDate >= '2024-01-01'
    """
    df_mw = pd.read_sql(query_mw, conn)
    print(df_mw.to_string(index=False))

    # Check PAN-07 Archive
    print('\n--- PAN-07 ARCHIVE ---')
    query_p07_archive = f"""
    SELECT
        COUNT(*) AS TxnCount,
        SUM(AmountIn1) AS TotalAmount,
        MIN(LocalTransactionDate) AS Earliest,
        MAX(LocalTransactionDate) AS Latest
    FROM ATMArchive.dbo.RAW_Production2024
    WHERE AccountNumber LIKE '{test_account}'
      AND PANEntryMode = '07'
      AND LocalTransactionDate >= '2024-01-01'
    """
    df_p07_a = pd.read_sql(query_p07_archive, conn)
    print(df_p07_a.to_string(index=False))

    # Check PAN-07 Current
    print('\n--- PAN-07 CURRENT ---')
    query_p07_current = f"""
    SELECT
        COUNT(*) AS TxnCount,
        SUM(AmountIn1) AS TotalAmount,
        MIN(LocalTransactionDate) AS Earliest,
        MAX(LocalTransactionDate) AS Latest
    FROM AtmDialog.Raw_Production
    WHERE AccountNumber LIKE '{test_account}'
      AND PANEntryMode = '07'
      AND LocalTransactionDate >= '2024-01-01'
    """
    df_p07_c = pd.read_sql(query_p07_current, conn)
    print(df_p07_c.to_string(index=False))

    # Calculate
    mw_count = int(df_mw['TxnCount'].iloc[0])
    mw_amount = float(df_mw['TotalAmount'].iloc[0]) if df_mw['TotalAmount'].iloc[0] else 0
    p07_a_count = int(df_p07_a['TxnCount'].iloc[0])
    p07_a_amount = float(df_p07_a['TotalAmount'].iloc[0]) if df_p07_a['TotalAmount'].iloc[0] else 0
    p07_c_count = int(df_p07_c['TxnCount'].iloc[0])
    p07_c_amount = float(df_p07_c['TotalAmount'].iloc[0]) if df_p07_c['TotalAmount'].iloc[0] else 0

    p07_total_count = p07_a_count + p07_c_count
    p07_total_amount = p07_a_amount + p07_c_amount

    print('\n--- SUMMARY ---')
    print(f'Mobile Wallet:      {mw_count:>8,} txns    ${mw_amount:>15,.2f}')
    print(f'PAN-07 Archive:     {p07_a_count:>8,} txns    ${p07_a_amount:>15,.2f}')
    print(f'PAN-07 Current:     {p07_c_count:>8,} txns    ${p07_c_amount:>15,.2f}')
    print(f'PAN-07 TOTAL:       {p07_total_count:>8,} txns    ${p07_total_amount:>15,.2f}')
    print(f'')
    print(f'Card Tap Count (P07 - MW):  {p07_total_count - mw_count:,}')
    print(f'Card Tap Amount (P07 - MW): ${p07_total_amount - mw_amount:,.2f}')

    if p07_total_count < mw_count:
        print(f'\n** DISCREPANCY: Mobile Wallet count ({mw_count}) > PAN-07 count ({p07_total_count})')
        print(f'   This means {mw_count - p07_total_count} wallet txns are NOT in PAN-07 data')

    if p07_total_amount > mw_amount and p07_total_count <= mw_count:
        print(f'\n** DISCREPANCY: PAN-07 amount (${p07_total_amount:,.2f}) > MW amount (${mw_amount:,.2f})')
        print(f'   But PAN-07 count ({p07_total_count}) <= MW count ({mw_count})')
        print(f'   This suggests different transaction amounts between systems')

    print('\n' + '=' * 70 + '\n')

conn.close()
print('Investigation complete.')
