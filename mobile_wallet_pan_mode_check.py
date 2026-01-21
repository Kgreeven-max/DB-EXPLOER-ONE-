"""
Mobile Wallet Activity - PAN Entry Mode 07 Investigation

For members with "Mobile Wallet Activity" alerts (code 628), investigate:
1. Check if they have mobile wallet transactions with PAN entry mode 07
2. Get transaction details, location, and all subsequent transactions from DWHA
3. Cross-reference to verify they have digital wallet activations (enrollment)

Output: MOBILE_WALLET_PAN_MODE_CHECK.xlsx
"""
import pandas as pd
from datetime import datetime, timedelta
from dwha_connection import get_dwha_connection

# Output file
OUTPUT_FILE = r"C:\Users\kgreeven\Desktop\MOBILE_WALLET_PAN_MODE_CHECK.xlsx"

# Members to investigate with their alert dates
MEMBERS_TO_CHECK = [
    {"account": "1107074", "name": "Alec D Lies", "alert_date": "2025-12-02"},
    {"account": "1113991", "name": "Randy M Adamos", "alert_date": "2025-12-04"},
    {"account": "1130997", "name": "The Debra Sue Dowdall Family Liv Trst", "alert_date": "2025-12-04"},
    {"account": "1231439", "name": "Arkico Lashun Williams", "alert_date": "2025-12-04"},
    {"account": "1134671", "name": "Norlita T Watkins", "alert_date": "2025-12-05"},
    {"account": "1221670", "name": "Anna Rita Mejia", "alert_date": "2025-12-10"},
    {"account": "1046084", "name": "Evelyn Louise Hartley", "alert_date": "2025-12-15"},
    {"account": "1171684", "name": "Edson A Garfias", "alert_date": "2025-12-15"},
    {"account": "934508", "name": "Maria E Estrada-Venegas", "alert_date": "2025-12-16"},
    {"account": "1003410", "name": "Thomassina V Pilato", "alert_date": "2025-12-16"},
    {"account": "1053271", "name": "Krista Peterson", "alert_date": "2025-12-16"},
    {"account": "945408", "name": "Branden William Reed", "alert_date": "2025-12-17"},
    {"account": "1026675", "name": "Erris M King", "alert_date": "2025-12-18"},
    {"account": "1087441", "name": "Bryant Jordan Eloriaga", "alert_date": "2025-12-20"},
    {"account": "1100049", "name": "Lizbeth Salazar", "alert_date": "2025-12-26"},
    {"account": "1187514", "name": "Jassiah Shields", "alert_date": "2025-12-26"},
    {"account": "1195677", "name": "Sheaya M Rojas", "alert_date": "2025-12-26"},
    {"account": "1127380", "name": "Gabriel J Ponce", "alert_date": "2025-12-27"},
    {"account": "1141249", "name": "Janelle Sirena Cervantes", "alert_date": "2025-12-27"},
    {"account": "870769", "name": "Angelica Aguilar", "alert_date": "2025-12-01"},  # Partial - using Dec 1
]


def pad_account(account):
    """Pad account number to 10 digits."""
    return str(account).zfill(10)


def get_member_list():
    """Get list of padded account numbers."""
    return [pad_account(m["account"]) for m in MEMBERS_TO_CHECK]


def query_atm_pan_mode_07(conn, member_numbers):
    """
    Query ATM transactions with PAN Entry Mode 07 for given members.
    PAN Entry Mode 07 = Contactless chip (mobile wallet).
    """
    if not member_numbers:
        return pd.DataFrame()

    in_clause = ",".join([f"'{m}'" for m in member_numbers])

    query = f"""
    SELECT
        RTRIM(AccountNumber) AS AccountNumber,
        LocalTransactionDate,
        LocalTransactionTime,
        AmountIn1 AS TransactionAmount,
        PostAmount,
        PANEntryMode,
        PINEntryMode,
        PointOfSaleEntryMode,
        RTRIM(CardAcceptorName) AS MerchantName,
        RTRIM(CardAcceptorCity) AS MerchantCity,
        RTRIM(CardAcceptorState) AS MerchantState,
        RTRIM(CardAcceptorZIPCode) AS MerchantZIP,
        MerchantType,
        RTRIM(NetworkID) AS NetworkID,
        OurCardType,
        OurTransactionCode,
        ResponseCodeIn,
        ResponseCodeOut,
        PostSuccess,
        RTRIM(TerminalID) AS TerminalID,
        RTRIM(ProcessorAccount) AS ProcessorAccount
    FROM AtmDialog.Raw_Production
    WHERE AccountNumber IN ({in_clause})
      AND PANEntryMode = '07'
    ORDER BY AccountNumber, LocalTransactionDate DESC, LocalTransactionTime DESC
    """

    print("Querying ATM transactions with PAN Entry Mode 07...")
    return pd.read_sql(query, conn)


def query_all_atm_transactions(conn, member_numbers, since_date='2025-12-01'):
    """
    Query ALL ATM transactions for given members since the alert period.
    This helps see transaction patterns before and after wallet setup.
    """
    if not member_numbers:
        return pd.DataFrame()

    in_clause = ",".join([f"'{m}'" for m in member_numbers])

    query = f"""
    SELECT
        RTRIM(AccountNumber) AS AccountNumber,
        LocalTransactionDate,
        LocalTransactionTime,
        AmountIn1 AS TransactionAmount,
        PostAmount,
        PANEntryMode,
        PINEntryMode,
        PointOfSaleEntryMode,
        RTRIM(CardAcceptorName) AS MerchantName,
        RTRIM(CardAcceptorCity) AS MerchantCity,
        RTRIM(CardAcceptorState) AS MerchantState,
        MerchantType,
        RTRIM(NetworkID) AS NetworkID,
        OurCardType,
        PostSuccess,
        ResponseCodeIn
    FROM AtmDialog.Raw_Production
    WHERE AccountNumber IN ({in_clause})
      AND LocalTransactionDate >= '{since_date}'
    ORDER BY AccountNumber, LocalTransactionDate DESC, LocalTransactionTime DESC
    """

    print(f"Querying all ATM transactions since {since_date}...")
    return pd.read_sql(query, conn)


def query_wallet_activations(conn, member_numbers):
    """Query wallet activations (enrollment) for given member numbers."""
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


def query_member_addresses(conn, member_numbers):
    """Query member address information from History.AccountName."""
    if not member_numbers:
        return pd.DataFrame()

    in_clause = ",".join([f"'{m}'" for m in member_numbers])

    query = f"""
    SELECT DISTINCT
        RTRIM(an.ParentAccount) AS AccountNumber,
        RTRIM(an.First) AS FirstName,
        RTRIM(an.Last) AS LastName,
        RTRIM(an.Street) AS Street,
        RTRIM(an.City) AS City,
        RTRIM(an.State) AS State,
        RTRIM(an.ZipCode) AS ZipCode,
        RTRIM(an.HomePhone) AS HomePhone,
        RTRIM(an.MobilePhone) AS MobilePhone,
        RTRIM(an.Email) AS Email,
        an.BirthDate,
        a.OpenDate
    FROM History.AccountName an
    INNER JOIN History.Account a ON an.ParentAccount = a.AccountNumber
    WHERE an.ParentAccount IN ({in_clause})
      AND an.AcctNameType = 0  -- Primary name record
    """

    print("Querying member addresses...")
    return pd.read_sql(query, conn)


def create_summary(members_df, pan07_df, activations_df, wallet_txns_df, all_atm_df):
    """Create summary dataframe for all members."""
    summary_data = []

    for member_info in MEMBERS_TO_CHECK:
        acct = pad_account(member_info["account"])
        name = member_info["name"]
        alert_date = member_info["alert_date"]

        # Get member address info
        member_addr = members_df[members_df['AccountNumber'] == acct]
        city = member_addr['City'].iloc[0] if len(member_addr) > 0 else ""
        state = member_addr['State'].iloc[0] if len(member_addr) > 0 else ""
        email = member_addr['Email'].iloc[0] if len(member_addr) > 0 else ""

        # PAN Entry Mode 07 transactions (ALL)
        member_pan07 = pan07_df[pan07_df['AccountNumber'] == acct]
        has_pan07 = len(member_pan07) > 0
        pan07_count = len(member_pan07)
        pan07_amount = float(member_pan07['TransactionAmount'].sum()) if has_pan07 else 0.0
        pan07_first_date = member_pan07['LocalTransactionDate'].min() if has_pan07 else None
        pan07_last_date = member_pan07['LocalTransactionDate'].max() if has_pan07 else None

        # POST-ALERT PAN 07 transactions - filter to those AFTER the alert date
        alert_dt = pd.to_datetime(alert_date).date()
        if has_pan07:
            # Convert LocalTransactionDate to date for comparison
            txn_dates = pd.to_datetime(member_pan07['LocalTransactionDate']).dt.date
            post_alert_pan07 = member_pan07[txn_dates > alert_dt]
        else:
            post_alert_pan07 = pd.DataFrame()
        post_alert_count = len(post_alert_pan07)
        post_alert_amount = float(post_alert_pan07['TransactionAmount'].sum()) if post_alert_count > 0 else 0.0
        post_alert_first = post_alert_pan07['LocalTransactionDate'].min() if post_alert_count > 0 else None
        post_alert_last = post_alert_pan07['LocalTransactionDate'].max() if post_alert_count > 0 else None
        had_post_alert_activity = "Yes" if post_alert_count > 0 else "No"

        # Wallet activations
        member_activations = activations_df[activations_df['AccountNumber'] == acct]
        has_wallet = len(member_activations) > 0
        wallet_types = ", ".join(member_activations['WalletType'].unique()) if has_wallet else ""
        first_activation = member_activations['ActivationDate'].min() if has_wallet else None

        # Wallet transactions
        member_wallet_txns = wallet_txns_df[wallet_txns_df['AccountNumber'] == acct]
        wallet_txn_count = len(member_wallet_txns)
        wallet_txn_amount = float(member_wallet_txns['TransactionAmount'].sum()) if wallet_txn_count > 0 else 0.0

        # All ATM transactions
        member_all_atm = all_atm_df[all_atm_df['AccountNumber'] == acct]
        total_atm_txns = len(member_all_atm)

        # Top merchants from PAN 07 transactions
        top_merchants = ""
        if has_pan07:
            merchant_counts = member_pan07['MerchantName'].value_counts().head(3)
            top_merchants = "; ".join([f"{m} ({c})" for m, c in merchant_counts.items()])

        summary_data.append({
            'AccountNumber': acct,
            'MemberName': name,
            'AlertDate': alert_date,
            'City': city,
            'State': state,
            'Email': email,
            'Had_PostAlert_Activity': had_post_alert_activity,
            'PostAlert_PAN07_Count': post_alert_count,
            'PostAlert_PAN07_Amount': post_alert_amount,
            'PostAlert_FirstTxnDate': post_alert_first,
            'PostAlert_LastTxnDate': post_alert_last,
            'Has_PAN07_Txns': has_pan07,
            'PAN07_TxnCount': pan07_count,
            'PAN07_TotalAmount': pan07_amount,
            'PAN07_FirstDate': pan07_first_date,
            'PAN07_LastDate': pan07_last_date,
            'Has_WalletActivation': has_wallet,
            'WalletTypes': wallet_types,
            'FirstActivationDate': first_activation,
            'WalletTxn_Count': wallet_txn_count,
            'WalletTxn_TotalAmount': wallet_txn_amount,
            'Total_ATM_Txns_Since_Dec': total_atm_txns,
            'Top_PAN07_Merchants': top_merchants
        })

    return pd.DataFrame(summary_data)


def main():
    print("=" * 70)
    print("Mobile Wallet Activity - PAN Entry Mode 07 Investigation")
    print("=" * 70)
    print()

    # Get member list
    member_numbers = get_member_list()
    print(f"Investigating {len(member_numbers)} members")
    print()

    # Connect to DWHA
    print("Connecting to DWHA...")
    conn = get_dwha_connection()
    print("Connected successfully!")
    print()

    # Query all data
    pan07_df = query_atm_pan_mode_07(conn, member_numbers)
    print(f"Found {len(pan07_df)} PAN Entry Mode 07 transactions")

    all_atm_df = query_all_atm_transactions(conn, member_numbers)
    print(f"Found {len(all_atm_df)} total ATM transactions since Dec 2025")

    activations_df = query_wallet_activations(conn, member_numbers)
    print(f"Found {len(activations_df)} wallet activations")

    wallet_txns_df = query_wallet_transactions(conn, member_numbers)
    print(f"Found {len(wallet_txns_df)} wallet transactions")

    members_df = query_member_addresses(conn, member_numbers)
    print(f"Found {len(members_df)} member address records")
    print()

    # Close connection
    conn.close()

    # Create summary
    print("Creating summary...")
    summary_df = create_summary(members_df, pan07_df, activations_df, wallet_txns_df, all_atm_df)

    # Export to Excel - Executive-friendly format
    print(f"\nExporting to: {OUTPUT_FILE}")
    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:

        # Sheet 1: SUMMARY - All 20 members at a glance
        exec_summary = summary_df[[
            'AccountNumber',
            'MemberName',
            'AlertDate',
            'WalletTypes',
            'FirstActivationDate',
            'Has_PAN07_Txns',
            'Had_PostAlert_Activity',
            'PostAlert_PAN07_Count',
            'PostAlert_PAN07_Amount',
        ]].copy()
        # Add clear Yes/No columns
        exec_summary['Has_PAN07'] = exec_summary['Has_PAN07_Txns'].apply(lambda x: 'Yes' if x else 'No')
        exec_summary['PAN07_After_Alert'] = exec_summary['Had_PostAlert_Activity']
        # Select and rename columns for clarity
        exec_summary = exec_summary[[
            'AccountNumber',
            'MemberName',
            'AlertDate',
            'WalletTypes',
            'FirstActivationDate',
            'Has_PAN07',
            'PAN07_After_Alert',
            'PostAlert_PAN07_Count',
            'PostAlert_PAN07_Amount',
        ]]
        exec_summary.columns = [
            'Account',
            'Member Name',
            'Alert Date',
            'Wallet Type',
            'Wallet Activated',
            'Has PAN-07?',
            'PAN-07 After Alert?',
            'Transactions After Alert',
            'Amount After Alert ($)',
        ]
        exec_summary.to_excel(writer, sheet_name='SUMMARY', index=False)

        # Sheet 2: WALLET_DETAILS - Wallet activation info
        if len(activations_df) > 0:
            member_name_map = {pad_account(m['account']): m['name'] for m in MEMBERS_TO_CHECK}
            alert_date_map = {pad_account(m['account']): m['alert_date'] for m in MEMBERS_TO_CHECK}
            wallet_details = activations_df[['AccountNumber', 'WalletType', 'ActivationDate']].copy()
            wallet_details['Member Name'] = wallet_details['AccountNumber'].map(member_name_map)
            wallet_details['Alert Date'] = wallet_details['AccountNumber'].map(alert_date_map)
            wallet_details = wallet_details[['AccountNumber', 'Member Name', 'Alert Date', 'WalletType', 'ActivationDate']]
            wallet_details.columns = ['Account', 'Member Name', 'Alert Date', 'Wallet Type', 'Activation Date']
            wallet_details.to_excel(writer, sheet_name='WALLET_DETAILS', index=False)

        print("  Created SUMMARY sheet (all 20 members)")
        print("  Created WALLET_DETAILS sheet")

        # Individual member sheets - one per member
        print("\nCreating individual member sheets...")
        member_name_map = {pad_account(m['account']): m['name'] for m in MEMBERS_TO_CHECK}
        alert_date_map = {pad_account(m['account']): m['alert_date'] for m in MEMBERS_TO_CHECK}

        for member_info in MEMBERS_TO_CHECK:
            acct = pad_account(member_info["account"])
            name = member_info["name"]
            alert_date = member_info["alert_date"]
            alert_dt = pd.to_datetime(alert_date).date()

            # Create safe sheet name (max 31 chars) - use last name + last 4 of account
            name_parts = name.split()
            last_name = name_parts[-1][:12] if name_parts else "Member"
            sheet_name = f"{last_name}_{acct[-4:]}"[:31]

            # Get this member's data
            member_pan07 = pan07_df[pan07_df['AccountNumber'] == acct].copy() if len(pan07_df) > 0 else pd.DataFrame()
            member_wallet = activations_df[activations_df['AccountNumber'] == acct] if len(activations_df) > 0 else pd.DataFrame()

            # Build header info
            header_rows = [
                ['MEMBER SUMMARY'],
                [''],
                ['Account:', acct],
                ['Name:', name],
                ['Alert Date:', alert_date],
                [''],
            ]

            # Wallet info
            if len(member_wallet) > 0:
                wallet_type = ", ".join(member_wallet['WalletType'].unique())
                wallet_date = member_wallet['ActivationDate'].min()
                if pd.notna(wallet_date):
                    wallet_date_str = pd.to_datetime(wallet_date).strftime('%Y-%m-%d')
                else:
                    wallet_date_str = "Unknown"
                header_rows.append(['Wallet Type:', wallet_type])
                header_rows.append(['Wallet Activated:', wallet_date_str])
            else:
                header_rows.append(['Wallet Type:', 'None'])
                header_rows.append(['Wallet Activated:', 'N/A'])

            header_rows.append([''])

            # PAN 07 summary
            if len(member_pan07) > 0:
                total_count = len(member_pan07)
                total_amount = member_pan07['TransactionAmount'].sum()
                txn_dates = pd.to_datetime(member_pan07['LocalTransactionDate']).dt.date
                post_alert = member_pan07[txn_dates > alert_dt]
                post_count = len(post_alert)
                post_amount = post_alert['TransactionAmount'].sum() if post_count > 0 else 0

                header_rows.append(['TOTAL Mobile Wallet Transactions:', total_count])
                header_rows.append(['TOTAL Amount:', f"${total_amount:,.2f}"])
                header_rows.append([''])
                header_rows.append(['Transactions AFTER Alert:', post_count])
                header_rows.append(['Amount AFTER Alert:', f"${post_amount:,.2f}"])
            else:
                header_rows.append(['TOTAL Mobile Wallet Transactions:', 0])
                header_rows.append(['Transactions AFTER Alert:', 0])

            header_rows.append([''])
            header_rows.append([''])

            # Write header
            header_df = pd.DataFrame(header_rows)
            header_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)

            # Add transaction detail if they have PAN 07 transactions
            if len(member_pan07) > 0:
                start_row = len(header_rows) + 1

                # Add label
                pd.DataFrame([['TRANSACTION DETAIL']]).to_excel(
                    writer, sheet_name=sheet_name, index=False, header=False, startrow=start_row
                )

                # Simplify transaction columns for clarity
                txn_detail = member_pan07[[
                    'LocalTransactionDate',
                    'TransactionAmount',
                    'MerchantName',
                    'MerchantCity',
                    'MerchantState'
                ]].copy()
                txn_detail.columns = ['Date', 'Amount', 'Merchant', 'City', 'State']
                txn_detail = txn_detail.sort_values('Date', ascending=False)
                txn_detail.to_excel(writer, sheet_name=sheet_name, index=False, startrow=start_row + 1)

            print(f"  Created: {sheet_name}")

    print("\n" + "=" * 70)
    print("Export complete!")
    print("=" * 70)

    # Print summary for console
    print("\nSUMMARY")
    print("-" * 60)

    members_with_post_alert = summary_df[summary_df['Had_PostAlert_Activity'] == 'Yes']
    members_with_wallet = summary_df[summary_df['Has_WalletActivation']]

    print(f"Total members checked: {len(summary_df)}")
    print(f"Members with wallet activations: {len(members_with_wallet)}")
    print(f"Members with activity AFTER alert: {len(members_with_post_alert)}")
    print()

    # Simple table view
    print(f"{'Account':<12} {'Name':<30} {'Alert':<12} {'Wallet':<12} {'After Alert?'}")
    print("-" * 80)
    for _, row in summary_df.iterrows():
        wallet = row['WalletTypes'][:10] if row['WalletTypes'] else "None"
        after_alert = f"Yes ({row['PostAlert_PAN07_Count']})" if row['Had_PostAlert_Activity'] == 'Yes' else "No"
        name = row['MemberName'][:28] if len(row['MemberName']) > 28 else row['MemberName']
        print(f"{row['AccountNumber']:<12} {name:<30} {row['AlertDate']:<12} {wallet:<12} {after_alert}")

    print("\n" + "=" * 70)
    print(f"Full report saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
