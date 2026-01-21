"""
Mobile Wallet & Card Tap Activity Report - AUDIT VERSION

PAN-07 = All contactless tap transactions (point-of-sale only, no in-app)
- Mobile Wallet Taps: Wallet transactions capped at PAN-07 (excludes in-app)
- Physical Card Taps: PAN-07 minus Mobile Wallet Taps

Data Sources:
- History.DigitalWalletActivations - wallet activation records
- History.DigitalWalletTransactions - mobile wallet transactions
- ATMArchive.dbo.RAW_Production2024 + AtmDialog.Raw_Production - PAN-07 (contactless)
- SymWarehouse.TrackingAccount.v64_OnlineBankingTracking - digital banking enrollment

Output: WALLET_ACTIVITY_FULL_REPORT.xlsx with 3 tabs:
  - SUMMARY: All members with combined data
  - MOBILE WALLET TAPS: Wallet tap transactions only
  - PHYSICAL CARD TAPS: Physical card tap transactions only
"""
import pandas as pd
import numpy as np
from dwha_connection import get_dwha_connection

OUTPUT_FILE = r"C:\Users\kgreeven\Desktop\WALLET_ACTIVITY_FULL_REPORT.xlsx"
START_DATE = '2024-01-01'


def query_wallet_activations(conn):
    """Get wallet activations aggregated by account (open accounts only)."""
    query = f"""
    SELECT DISTINCT
        RTRIM(w.AccountNumber) AS AccountNumber,
        w.WalletType,
        w.ActivationDate
    FROM History.DigitalWalletActivations w
    INNER JOIN History.Account a ON w.AccountNumber = a.AccountNumber
    WHERE w.ActivationDate >= '{START_DATE}'
      AND a.CloseDate IS NULL
    """
    print("Querying wallet activations...")
    df = pd.read_sql(query, conn)
    print(f"  {len(df):,} activation records")

    if len(df) == 0:
        return pd.DataFrame(columns=['AccountNumber', 'WalletTypes', 'FirstActivation'])

    result = df.groupby('AccountNumber').agg({
        'WalletType': lambda x: ', '.join(sorted(set(x))),
        'ActivationDate': 'min'
    }).reset_index()
    result.columns = ['AccountNumber', 'WalletTypes', 'FirstActivation']
    print(f"  {len(result):,} members with activations")
    return result


def query_wallet_transactions(conn):
    """Get wallet transactions aggregated by account (open accounts only)."""
    query = f"""
    SELECT
        RTRIM(w.AccountNumber) AS AccountNumber,
        MIN(w.LocalTransactionDate) AS MW_Earliest,
        MAX(w.LocalTransactionDate) AS MW_Latest,
        COUNT(*) AS MW_Count,
        SUM(w.TransactionAmount) AS MW_Amount
    FROM History.DigitalWalletTransactions w
    INNER JOIN History.Account a ON w.AccountNumber = a.AccountNumber
    WHERE w.LocalTransactionDate >= '{START_DATE}'
      AND a.CloseDate IS NULL
    GROUP BY w.AccountNumber
    """
    print("Querying wallet transactions...")
    df = pd.read_sql(query, conn)
    print(f"  {len(df):,} members with wallet transactions")
    return df


def query_pan07(conn):
    """Get PAN-07 transactions aggregated by account (open accounts only)."""
    print("Querying PAN-07 transactions...")

    # Archive 2024
    query_archive = f"""
    SELECT
        RTRIM(p.AccountNumber) AS AccountNumber,
        MIN(p.LocalTransactionDate) AS P07_Earliest,
        MAX(p.LocalTransactionDate) AS P07_Latest,
        COUNT(*) AS P07_Count,
        SUM(p.AmountIn1) AS P07_Amount
    FROM ATMArchive.dbo.RAW_Production2024 p
    INNER JOIN History.Account a ON p.AccountNumber = a.AccountNumber
    WHERE p.PANEntryMode = '07' AND p.LocalTransactionDate >= '{START_DATE}'
      AND a.CloseDate IS NULL
    GROUP BY p.AccountNumber
    """
    print("  Querying archive...")
    df_archive = pd.read_sql(query_archive, conn)
    print(f"    {len(df_archive):,} members in archive")

    # Current
    query_current = f"""
    SELECT
        RTRIM(p.AccountNumber) AS AccountNumber,
        MIN(p.LocalTransactionDate) AS P07_Earliest,
        MAX(p.LocalTransactionDate) AS P07_Latest,
        COUNT(*) AS P07_Count,
        SUM(p.AmountIn1) AS P07_Amount
    FROM AtmDialog.Raw_Production p
    INNER JOIN History.Account a ON p.AccountNumber = a.AccountNumber
    WHERE p.PANEntryMode = '07' AND p.LocalTransactionDate >= '{START_DATE}'
      AND a.CloseDate IS NULL
    GROUP BY p.AccountNumber
    """
    print("  Querying current...")
    df_current = pd.read_sql(query_current, conn)
    print(f"    {len(df_current):,} members in current")

    # Combine
    df_all = pd.concat([df_archive, df_current], ignore_index=True)

    if len(df_all) == 0:
        return pd.DataFrame(columns=['AccountNumber', 'P07_Earliest', 'P07_Latest', 'P07_Count', 'P07_Amount'])

    df_combined = df_all.groupby('AccountNumber').agg({
        'P07_Earliest': 'min',
        'P07_Latest': 'max',
        'P07_Count': 'sum',
        'P07_Amount': 'sum'
    }).reset_index()

    print(f"  Total: {len(df_combined):,} unique members with PAN-07")
    return df_combined


def query_digital_banking_enrollment(conn):
    """Get digital banking enrollment date by account."""
    query = """
    SELECT
        RTRIM(ParentAccount) AS AccountNumber,
        MIN(CREATIONDATE) AS DB_Activated
    FROM SymWarehouse.TrackingAccount.v64_OnlineBankingTracking WITH (NOLOCK)
    WHERE CREATIONDATE IS NOT NULL
    GROUP BY ParentAccount
    """
    print("Querying digital banking enrollment dates...")
    df = pd.read_sql(query, conn)
    print(f"  {len(df):,} members with digital banking")
    return df


def query_member_names_batch(conn, accounts):
    """Query member names in batches."""
    if not accounts:
        return pd.DataFrame(columns=['AccountNumber', 'MemberName'])

    print(f"Querying member names for {len(accounts):,} accounts...")
    batch_size = 2000
    results = []

    for i in range(0, len(accounts), batch_size):
        batch = accounts[i:i+batch_size]
        in_clause = ",".join([f"'{a}'" for a in batch])
        query = f"""
        SELECT DISTINCT
            RTRIM(ParentAccount) AS AccountNumber,
            RTRIM(First) + ' ' + RTRIM(Last) AS MemberName
        FROM History.AccountName
        WHERE ParentAccount IN ({in_clause}) AND AcctNameType = 0
        """
        df = pd.read_sql(query, conn)
        results.append(df)
        if (i // batch_size + 1) % 10 == 0:
            print(f"  Batch {i // batch_size + 1}...")

    if results:
        return pd.concat(results, ignore_index=True).drop_duplicates('AccountNumber')
    return pd.DataFrame(columns=['AccountNumber', 'MemberName'])


def main():
    print("=" * 70)
    print("MOBILE WALLET & CARD TAP REPORT - AUDIT VERSION")
    print("=" * 70)
    print(f"Date Range: {START_DATE} to present")
    print(f"Filter: Open accounts only, PAN-07 tap transactions only")
    print()

    conn = get_dwha_connection()
    print("Connected to DWHA\n")

    # Get data
    activations = query_wallet_activations(conn)
    wallet_txns = query_wallet_transactions(conn)
    pan07 = query_pan07(conn)
    db_enrollment = query_digital_banking_enrollment(conn)

    # Include members with PAN-07 activity (tap transactions)
    all_accounts = set()
    all_accounts.update(pan07['AccountNumber'].tolist())
    all_accounts = list(all_accounts)
    print(f"\nTotal unique accounts with PAN-07 taps: {len(all_accounts):,}")

    # Get names
    names = query_member_names_batch(conn, all_accounts)
    conn.close()

    print("\nBuilding summary...")

    # Build summary
    summary = pd.DataFrame({'AccountNumber': all_accounts})
    summary = summary.merge(names, on='AccountNumber', how='left')
    summary = summary.merge(activations, on='AccountNumber', how='left')
    summary = summary.merge(db_enrollment, on='AccountNumber', how='left')
    summary = summary.merge(wallet_txns, on='AccountNumber', how='left')
    summary = summary.merge(pan07, on='AccountNumber', how='left')

    # Fill NaN
    summary['WalletTypes'] = summary['WalletTypes'].fillna('')
    summary['MW_Count'] = summary['MW_Count'].fillna(0).astype(int)
    summary['MW_Amount'] = summary['MW_Amount'].fillna(0)
    summary['P07_Count'] = summary['P07_Count'].fillna(0).astype(int)
    summary['P07_Amount'] = summary['P07_Amount'].fillna(0)

    # =========================================================================
    # KEY CALCULATION: Mobile Wallet Taps = MIN(MW, PAN-07)
    # This excludes in-app purchases (MW that exceeds PAN-07)
    # =========================================================================
    summary['MWT_Count'] = summary[['MW_Count', 'P07_Count']].min(axis=1).astype(int)
    summary['MWT_Amount'] = summary[['MW_Amount', 'P07_Amount']].min(axis=1)

    # Physical Card Taps = PAN-07 minus Mobile Wallet Taps
    summary['CT_Count'] = (summary['P07_Count'] - summary['MWT_Count']).astype(int)
    summary['CT_Amount'] = summary['P07_Amount'] - summary['MWT_Amount']

    # Use MW dates for Mobile Wallet Taps (if they have MW transactions)
    # Use P07 dates for Card Taps
    summary['MWT_Earliest'] = summary['MW_Earliest']
    summary['MWT_Latest'] = summary['MW_Latest']
    summary['CT_Earliest'] = summary['P07_Earliest']
    summary['CT_Latest'] = summary['P07_Latest']

    # Blank out dates if no transactions
    summary.loc[summary['MWT_Count'] == 0, 'MWT_Earliest'] = None
    summary.loc[summary['MWT_Count'] == 0, 'MWT_Latest'] = None
    summary.loc[summary['CT_Count'] == 0, 'CT_Earliest'] = None
    summary.loc[summary['CT_Count'] == 0, 'CT_Latest'] = None

    # Add PAN-07 Yes/No flags
    summary['Has_MWT'] = summary['MWT_Count'].apply(lambda x: 'Yes' if x > 0 else 'No')
    summary['Has_CT'] = summary['CT_Count'].apply(lambda x: 'Yes' if x > 0 else 'No')

    # Wallet activated before digital banking?
    # Convert both to Timestamp for comparison
    summary['Wallet_Before_DB'] = summary.apply(
        lambda row: 'Yes' if pd.notna(row['FirstActivation']) and pd.notna(row['DB_Activated'])
                    and pd.Timestamp(row['FirstActivation']) < pd.Timestamp(row['DB_Activated']) else 'No', axis=1
    )

    # =========================================================================
    # TAB 1: SUMMARY - All members
    # =========================================================================
    tab1 = summary[[
        'AccountNumber', 'MemberName', 'WalletTypes', 'FirstActivation',
        'DB_Activated', 'Wallet_Before_DB',
        'Has_MWT', 'MWT_Earliest', 'MWT_Latest', 'MWT_Count', 'MWT_Amount',
        'Has_CT', 'CT_Earliest', 'CT_Latest', 'CT_Count', 'CT_Amount'
    ]].copy()

    tab1.columns = [
        'Account Number',
        'Member Name',
        'Wallet Type(s)',
        'Wallet First Activated',
        'Digital Banking Activated',
        'Wallet Before Digital Banking?',
        'PAN-07 Mobile Wallet Tap?',
        'PAN-07 Mobile Wallet - First',
        'PAN-07 Mobile Wallet - Last',
        'PAN-07 Mobile Wallet - Count',
        'PAN-07 Mobile Wallet - Amount ($)',
        'PAN-07 Physical Card Tap?',
        'PAN-07 Physical Card - First',
        'PAN-07 Physical Card - Last',
        'PAN-07 Physical Card - Count',
        'PAN-07 Physical Card - Amount ($)'
    ]

    tab1 = tab1.sort_values('Account Number').reset_index(drop=True)

    # =========================================================================
    # TAB 2: MOBILE WALLET TAPS ONLY
    # =========================================================================
    mwt_data = summary[summary['MWT_Count'] > 0][[
        'AccountNumber', 'MemberName', 'WalletTypes',
        'MWT_Earliest', 'MWT_Latest', 'MWT_Count', 'MWT_Amount'
    ]].copy()

    mwt_data.columns = [
        'Account Number',
        'Member Name',
        'Wallet Type(s)',
        'First Transaction',
        'Last Transaction',
        'Transaction Count',
        'Transaction Amount ($)'
    ]

    mwt_data = mwt_data.sort_values('Account Number').reset_index(drop=True)

    # =========================================================================
    # TAB 3: PHYSICAL CARD TAPS ONLY
    # =========================================================================
    ct_data = summary[summary['CT_Count'] > 0][[
        'AccountNumber', 'MemberName',
        'CT_Earliest', 'CT_Latest', 'CT_Count', 'CT_Amount'
    ]].copy()

    ct_data.columns = [
        'Account Number',
        'Member Name',
        'First Transaction',
        'Last Transaction',
        'Transaction Count',
        'Transaction Amount ($)'
    ]

    ct_data = ct_data.sort_values('Account Number').reset_index(drop=True)

    # =========================================================================
    # EXPORT
    # =========================================================================
    print(f"\nExporting to: {OUTPUT_FILE}")
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        tab1.to_excel(writer, sheet_name='SUMMARY', index=False)
        mwt_data.to_excel(writer, sheet_name='MOBILE WALLET TAPS', index=False)
        ct_data.to_excel(writer, sheet_name='PHYSICAL CARD TAPS', index=False)

    # =========================================================================
    # AUDIT STATS (from SUMMARY tab - source of truth)
    # =========================================================================
    print("\n" + "=" * 70)
    print("AUDIT REPORT COMPLETE")
    print("=" * 70)

    print("\n--- SUMMARY TAB (Source of Truth) ---")
    print(f"Total Members with PAN-07 Taps: {len(tab1):,}")

    # Calculate totals from SUMMARY tab
    mwt_total_count = tab1['PAN-07 Mobile Wallet - Count'].sum()
    mwt_total_amount = tab1['PAN-07 Mobile Wallet - Amount ($)'].sum()
    ct_total_count = tab1['PAN-07 Physical Card - Count'].sum()
    ct_total_amount = tab1['PAN-07 Physical Card - Amount ($)'].sum()

    print(f"\nMobile Wallet Taps:")
    print(f"  Members with activity: {(tab1['PAN-07 Mobile Wallet Tap?'] == 'Yes').sum():,}")
    print(f"  Transaction Count: {mwt_total_count:,}")
    print(f"  Transaction Amount: ${mwt_total_amount:,.2f}")

    print(f"\nPhysical Card Taps:")
    print(f"  Members with activity: {(tab1['PAN-07 Physical Card Tap?'] == 'Yes').sum():,}")
    print(f"  Transaction Count: {ct_total_count:,}")
    print(f"  Transaction Amount: ${ct_total_amount:,.2f}")

    print("\n--- TOTAL PAN-07 ---")
    total_count = mwt_total_count + ct_total_count
    total_amount = mwt_total_amount + ct_total_amount
    print(f"Total Transaction Count: {total_count:,}")
    print(f"Total Transaction Amount: ${total_amount:,.2f}")

    print("\n--- DETAIL TABS (for reference) ---")
    print(f"Mobile Wallet Taps Tab: {len(mwt_data):,} members")
    print(f"Physical Card Taps Tab: {len(ct_data):,} members")

    print("\n" + "=" * 70)
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
