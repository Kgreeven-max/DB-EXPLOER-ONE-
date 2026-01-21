"""
Check Apple Pay / Google Pay / Samsung Pay usage for suspicious email members.

Reads member numbers from suspicious emails report and queries DWHA for:
- Digital wallet activations (enrollment)
- Digital wallet transactions (usage with merchant info)
- Member address/location information

Output: Updated suspicious email report with wallet data and individual member transaction breakouts.
"""
import pandas as pd
from datetime import datetime
from dwha_connection import get_dwha_connection

# Path to suspicious emails report
SUSPICIOUS_EMAILS_FILE = r"C:\Users\kgreeven\Desktop\SUSPICIOUS_EMAILS_REPORT_20260116.xlsx"

# Output file - comprehensive report
OUTPUT_FILE = r"C:\Users\kgreeven\Desktop\SUSPICIOUS_EMAILS_WITH_WALLET_DATA.xlsx"


def get_member_numbers():
    """Read member numbers from suspicious emails Excel file (ALL DATA sheet)."""
    print(f"Reading member numbers from: {SUSPICIOUS_EMAILS_FILE}")

    # Read from ALL DATA sheet which has the member details
    df = pd.read_excel(SUSPICIOUS_EMAILS_FILE, sheet_name='ALL DATA')
    print(f"Total rows: {len(df)}")

    # Use Member_Numbers column
    member_col = 'Member_Numbers'

    # Get unique member numbers, convert to string and pad to 10 digits
    members = df[member_col].dropna().unique()
    member_numbers = [str(int(m)).zfill(10) for m in members if pd.notna(m)]

    # Also add padded member number column to df for joining later
    df['AccountNumber'] = df[member_col].apply(lambda x: str(int(x)).zfill(10) if pd.notna(x) else None)

    print(f"Found {len(member_numbers)} unique member numbers")
    return member_numbers, df


def query_member_addresses(conn, member_numbers):
    """Query member address information from History.AccountName."""
    if not member_numbers:
        return pd.DataFrame()

    in_clause = ",".join([f"'{m}'" for m in member_numbers])

    query = f"""
    SELECT DISTINCT
        RTRIM(ParentAccount) AS AccountNumber,
        RTRIM(First) AS FirstName_DWHA,
        RTRIM(Last) AS LastName_DWHA,
        RTRIM(Street) AS Street,
        RTRIM(City) AS City,
        RTRIM(State) AS State,
        RTRIM(ZipCode) AS ZipCode,
        RTRIM(HomePhone) AS HomePhone,
        RTRIM(MobilePhone) AS MobilePhone,
        RTRIM(Email) AS Email_DWHA,
        BirthDate,
        OpenDate
    FROM History.AccountName an
    INNER JOIN History.Account a ON an.ParentAccount = a.AccountNumber
    WHERE an.ParentAccount IN ({in_clause})
      AND an.AcctNameType = 0  -- Primary name record
    """

    print("Querying member addresses...")
    return pd.read_sql(query, conn)


def query_wallet_activations(conn, member_numbers):
    """Query wallet activations for given member numbers."""
    if not member_numbers:
        return pd.DataFrame()

    in_clause = ",".join([f"'{m}'" for m in member_numbers])

    query = f"""
    SELECT
        RTRIM(AccountNumber) AS AccountNumber,
        WalletType,
        ActivationDate,
        CardNumber,
        LoanOrShareType,
        LoanOrShareIndicator,
        LoanOrShareID,
        FileTime,
        ImportDate
    FROM History.DigitalWalletActivations
    WHERE AccountNumber IN ({in_clause})
    ORDER BY AccountNumber, ActivationDate DESC
    """

    print("Querying wallet activations...")
    return pd.read_sql(query, conn)


def query_wallet_transactions(conn, member_numbers):
    """Query wallet transactions for given member numbers."""
    if not member_numbers:
        return pd.DataFrame()

    in_clause = ",".join([f"'{m}'" for m in member_numbers])

    query = f"""
    SELECT
        RTRIM(AccountNumber) AS AccountNumber,
        WalletType,
        LocalTransactionDate,
        TransactionAmount,
        MerchantDescription,
        CardNumber,
        LoanOrShareType,
        LoanOrShareIndicator,
        LoanOrShareID,
        FileTime,
        ImportDate
    FROM History.DigitalWalletTransactions
    WHERE AccountNumber IN ({in_clause})
    ORDER BY AccountNumber, LocalTransactionDate DESC
    """

    print("Querying wallet transactions...")
    return pd.read_sql(query, conn)


def create_wallet_summary_columns(activations_df, transactions_df, member):
    """Create wallet summary data for a single member."""
    member_activations = activations_df[activations_df['AccountNumber'] == member] if len(activations_df) > 0 else pd.DataFrame()
    member_transactions = transactions_df[transactions_df['AccountNumber'] == member] if len(transactions_df) > 0 else pd.DataFrame()

    # Wallet flags
    has_apple = 'Apple Pay' in member_activations['WalletType'].values if len(member_activations) > 0 else False
    has_google = 'Google Pay' in member_activations['WalletType'].values if len(member_activations) > 0 else False
    has_samsung = 'Samsung Pay' in member_activations['WalletType'].values if len(member_activations) > 0 else False

    # Transaction counts
    apple_txns = len(member_transactions[member_transactions['WalletType'] == 'Apple Pay']) if len(member_transactions) > 0 else 0
    google_txns = len(member_transactions[member_transactions['WalletType'] == 'Google Pay']) if len(member_transactions) > 0 else 0
    samsung_txns = len(member_transactions[member_transactions['WalletType'] == 'Samsung Pay']) if len(member_transactions) > 0 else 0
    total_amount = float(member_transactions['TransactionAmount'].sum()) if len(member_transactions) > 0 else 0.0

    # Dates
    first_activation = member_activations['ActivationDate'].min() if len(member_activations) > 0 else None
    last_transaction = member_transactions['LocalTransactionDate'].max() if len(member_transactions) > 0 else None

    # Top merchants
    top_merchants = ""
    if len(member_transactions) > 0:
        merchant_counts = member_transactions['MerchantDescription'].value_counts().head(5)
        top_merchants = "; ".join([f"{m} ({c})" for m, c in merchant_counts.items()])

    return {
        'Has_ApplePay': has_apple,
        'Has_GooglePay': has_google,
        'Has_SamsungPay': has_samsung,
        'ApplePay_Txns': apple_txns,
        'GooglePay_Txns': google_txns,
        'SamsungPay_Txns': samsung_txns,
        'Total_Wallet_Txns': apple_txns + google_txns + samsung_txns,
        'Total_Wallet_Amount': total_amount,
        'First_Wallet_Activation': first_activation,
        'Last_Wallet_Transaction': last_transaction,
        'Top_Merchants': top_merchants
    }


def main():
    print("=" * 60)
    print("Suspicious Email Members - Digital Wallet Usage Check")
    print("=" * 60)
    print()

    # Get member numbers from suspicious emails report
    member_numbers, suspicious_df = get_member_numbers()
    print()

    # Connect to DWHA
    print("Connecting to DWHA...")
    conn = get_dwha_connection()
    print("Connected successfully!")
    print()

    # Query member addresses
    address_df = query_member_addresses(conn, member_numbers)
    print(f"Found {len(address_df)} member address records")

    # Query wallet data
    activations_df = query_wallet_activations(conn, member_numbers)
    print(f"Found {len(activations_df)} wallet activations")

    transactions_df = query_wallet_transactions(conn, member_numbers)
    print(f"Found {len(transactions_df)} wallet transactions")
    print()

    # Close connection
    conn.close()

    # Merge address data into suspicious_df
    print("Enriching suspicious email data...")
    if len(address_df) > 0:
        # Drop duplicates keeping first
        address_df_dedup = address_df.drop_duplicates(subset=['AccountNumber'], keep='first')
        suspicious_df = suspicious_df.merge(address_df_dedup, on='AccountNumber', how='left')

    # Add wallet summary columns for each member
    print("Adding wallet summary data...")
    wallet_summaries = []
    for member in suspicious_df['AccountNumber']:
        if pd.notna(member):
            summary = create_wallet_summary_columns(activations_df, transactions_df, member)
        else:
            summary = {
                'Has_ApplePay': False, 'Has_GooglePay': False, 'Has_SamsungPay': False,
                'ApplePay_Txns': 0, 'GooglePay_Txns': 0, 'SamsungPay_Txns': 0,
                'Total_Wallet_Txns': 0, 'Total_Wallet_Amount': 0.0,
                'First_Wallet_Activation': None, 'Last_Wallet_Transaction': None,
                'Top_Merchants': ''
            }
        wallet_summaries.append(summary)

    wallet_df = pd.DataFrame(wallet_summaries)
    suspicious_df = pd.concat([suspicious_df.reset_index(drop=True), wallet_df], axis=1)

    # Count members with wallets
    members_with_wallets = suspicious_df[
        suspicious_df['Has_ApplePay'] |
        suspicious_df['Has_GooglePay'] |
        suspicious_df['Has_SamsungPay']
    ]

    print(f"\nMembers with digital wallets: {len(members_with_wallets)} of {len(member_numbers)}")
    print()

    # Export to Excel with individual member sheets
    print(f"Exporting to: {OUTPUT_FILE}")
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:

        # Sheet 1: All suspicious emails with wallet data (enriched master list)
        suspicious_df.to_excel(writer, sheet_name='ALL_SUSPICIOUS_ENRICHED', index=False)

        # Sheet 2: Summary - just members with wallets
        members_with_wallets.to_excel(writer, sheet_name='MEMBERS_WITH_WALLETS', index=False)

        # Sheet 3: All wallet activations
        if len(activations_df) > 0:
            # Enrich with member info
            act_enriched = activations_df.merge(
                suspicious_df[['AccountNumber', 'FirstName', 'LastName', 'Email', 'Domain_Type', 'City', 'State']],
                on='AccountNumber', how='left'
            )
            act_enriched.to_excel(writer, sheet_name='ALL_ACTIVATIONS', index=False)

        # Sheet 4: All wallet transactions
        if len(transactions_df) > 0:
            txn_enriched = transactions_df.merge(
                suspicious_df[['AccountNumber', 'FirstName', 'LastName', 'Email', 'Domain_Type', 'City', 'State']],
                on='AccountNumber', how='left'
            )
            txn_enriched.to_excel(writer, sheet_name='ALL_TRANSACTIONS', index=False)

        # Individual sheets for each member WITH wallet activity
        print("\nCreating individual member transaction sheets...")
        for _, row in members_with_wallets.iterrows():
            member = row['AccountNumber']
            first_name = str(row['FirstName'])[:10] if pd.notna(row['FirstName']) else 'UNK'
            last_name = str(row['LastName'])[:10] if pd.notna(row['LastName']) else 'UNK'

            # Create safe sheet name (max 31 chars, no special chars)
            sheet_name = f"{last_name}_{member[-4:]}"[:31]

            # Get this member's transactions
            member_txns = transactions_df[transactions_df['AccountNumber'] == member].copy()

            if len(member_txns) > 0:
                # Add member info header rows
                member_info = pd.DataFrame([
                    {'Info': 'MEMBER TRANSACTION DETAIL'},
                    {'Info': f'Account: {member}'},
                    {'Info': f'Name: {first_name} {last_name}'},
                    {'Info': f'Email: {row["Email"]}'},
                    {'Info': f'Domain Type: {row["Domain_Type"]}'},
                    {'Info': f'Location: {row["City"]}, {row["State"]} {row["ZipCode"]}'},
                    {'Info': f'Total Transactions: {len(member_txns)}'},
                    {'Info': f'Total Amount: ${row["Total_Wallet_Amount"]:,.2f}'},
                    {'Info': ''},  # Blank row
                ])

                # Create transaction summary by merchant
                merchant_summary = member_txns.groupby('MerchantDescription').agg({
                    'TransactionAmount': ['count', 'sum']
                }).reset_index()
                merchant_summary.columns = ['Merchant', 'Transaction_Count', 'Total_Amount']
                merchant_summary = merchant_summary.sort_values('Total_Amount', ascending=False)

                # Write member info
                member_info.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=0)

                # Write merchant summary
                pd.DataFrame([{'': 'MERCHANT SUMMARY'}]).to_excel(
                    writer, sheet_name=sheet_name, index=False, header=False, startrow=10
                )
                merchant_summary.to_excel(writer, sheet_name=sheet_name, index=False, startrow=11)

                # Write full transaction detail
                detail_start = 11 + len(merchant_summary) + 3
                pd.DataFrame([{'': 'FULL TRANSACTION DETAIL'}]).to_excel(
                    writer, sheet_name=sheet_name, index=False, header=False, startrow=detail_start
                )
                member_txns.to_excel(writer, sheet_name=sheet_name, index=False, startrow=detail_start + 1)

                print(f"  Created sheet: {sheet_name} ({len(member_txns)} transactions)")

    print("\nExport complete!")
    print()

    # Print quick stats
    print("=" * 60)
    print("QUICK STATS")
    print("=" * 60)
    print(f"Total suspicious members checked: {len(member_numbers)}")
    print(f"Members with ANY wallet: {len(members_with_wallets)}")
    print(f"  - Apple Pay: {suspicious_df['Has_ApplePay'].sum()}")
    print(f"  - Google Pay: {suspicious_df['Has_GooglePay'].sum()}")
    print(f"  - Samsung Pay: {suspicious_df['Has_SamsungPay'].sum()}")
    print(f"Total wallet transactions: {suspicious_df['Total_Wallet_Txns'].sum()}")
    print(f"Total transaction amount: ${suspicious_df['Total_Wallet_Amount'].sum():,.2f}")

    print()
    print("=" * 60)
    print("MEMBERS WITH DIGITAL WALLETS")
    print("=" * 60)
    for _, row in members_with_wallets.iterrows():
        wallets = []
        if row['Has_ApplePay']: wallets.append('Apple')
        if row['Has_GooglePay']: wallets.append('Google')
        if row['Has_SamsungPay']: wallets.append('Samsung')

        print(f"\n{row['AccountNumber']}: {row['FirstName']} {row['LastName']}")
        print(f"  Email: {row['Email']} ({row['Domain_Type']})")
        print(f"  Location: {row['City']}, {row['State']} {row['ZipCode']}")
        print(f"  Wallet: {', '.join(wallets)} Pay")
        print(f"  Transactions: {row['Total_Wallet_Txns']} (${row['Total_Wallet_Amount']:,.2f})")
        if row['Top_Merchants']:
            print(f"  Top Merchants: {row['Top_Merchants']}")


if __name__ == "__main__":
    main()
