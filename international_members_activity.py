"""
International Address/Phone Members - Digital Banking Activity Check

Finds all Symitar members with international addresses OR international phone types
who are enrolled in digital banking, then checks their last activity in DBXDB.

Data Sources:
- DWHA SQL Server (symwarehouse) - Member info and digital banking enrollment
- DBXDB MySQL (infinity-9ix) - Digital banking activity from fraudmonitor

Output: Excel report with multiple sheets showing activity status.
"""
import pandas as pd
from datetime import datetime, timedelta
from dwha_connection import get_dwha_connection
from db_connection import get_connection as get_dbxdb_connection

# Output file
OUTPUT_FILE = r"C:\Users\kgreeven\Desktop\INTERNATIONAL_MEMBERS_ACTIVITY.xlsx"


def query_international_members(conn):
    """
    Query DWHA for active members with international address OR phone type
    who are enrolled in digital banking, excluding Warning Code 29.
    """
    query = """
    SELECT DISTINCT
        an.ParentAccount AS AccountNumber,
        a.Branch,
        RTRIM(an.First) AS FirstName,
        RTRIM(an.Last) AS LastName,
        RTRIM(an.Street) AS Street,
        RTRIM(an.City) AS City,
        RTRIM(an.State) AS State,
        RTRIM(an.ZipCode) AS ZipCode,
        RTRIM(an.Country) AS Country,
        RTRIM(an.CountryCode) AS CountryCode,
        an.AddressType,
        an.PhoneType,
        RTRIM(an.HomePhone) AS HomePhone,
        RTRIM(an.MobilePhone) AS MobilePhone,
        RTRIM(an.Email) AS Email,
        RTRIM(an.AltEmail) AS AltEmail,
        an.BirthDate,
        muids.Muid AS MemberMuid,
        CASE WHEN an.AddressType = 1 THEN 'Yes' ELSE 'No' END AS HasIntlAddress,
        CASE WHEN an.PhoneType = 1 THEN 'Yes' ELSE 'No' END AS HasIntlPhone
    FROM [SymCore].[dbo].[AccountName] an
    JOIN [SymCore].[dbo].[Account] a
        ON an.ParentAccount = a.AccountNumber
    JOIN [symwarehouse].[Digital].[vwAllMuidNameRecords] muids
        ON an.ParentAccount = muids.AccountNumber
        AND muids.RecordType = 'AccountName'
        AND an.SSN = muids.SSN
    JOIN [SymWarehouse].[TrackingAccount].[v64_OnlineBankingTracking] v64
        ON v64.MemberMuid = muids.Muid
    WHERE an.MbrStatus = 0  -- Active members only
      AND (an.AddressType = 1 OR an.PhoneType = 1)  -- International address OR phone
      AND an.AcctNameType = 0  -- Primary name record
      -- Exclude Warning Code 29
      AND an.ParentAccount NOT IN (
          SELECT AccountNumber
          FROM [SymWarehouse].[Account].[vWarnings]
          WHERE Warning_Code = 29
          AND (Warning_Exp_Date IS NULL OR Warning_Exp_Date > GETDATE())
      )
    ORDER BY an.ParentAccount
    """

    print("Querying DWHA for international members enrolled in digital banking...")
    return pd.read_sql(query, conn)


def query_dbxdb_activity(conn, account_numbers):
    """
    Query DBXDB fraudmonitor for last activity dates for given accounts.
    Returns last activity date and last login date.
    """
    if not account_numbers:
        return pd.DataFrame()

    # Build IN clause with account numbers
    in_clause = ",".join([f"'{acc}'" for acc in account_numbers])

    query = f"""
    SELECT
        masterMembership AS AccountNumber,
        MAX(activityDate) AS LastActivity,
        MAX(CASE WHEN eventCategory = 'LoginSuccessful' THEN activityDate END) AS LastLogin,
        COUNT(*) AS TotalActivityCount,
        COUNT(CASE WHEN eventCategory = 'LoginSuccessful' THEN 1 END) AS LoginCount
    FROM fraudmonitor
    WHERE masterMembership IN ({in_clause})
    GROUP BY masterMembership
    """

    print(f"Querying DBXDB for activity data on {len(account_numbers)} accounts...")
    cursor = conn.cursor()
    cursor.execute(query)

    # Fetch results
    columns = ['AccountNumber', 'LastActivity', 'LastLogin', 'TotalActivityCount', 'LoginCount']
    rows = cursor.fetchall()
    cursor.close()

    return pd.DataFrame(rows, columns=columns)


def categorize_activity(row, cutoff_90_days, cutoff_30_days):
    """Categorize member activity status."""
    if pd.isna(row['LastActivity']):
        return 'NEVER_LOGGED_IN'
    elif row['LastActivity'] >= cutoff_30_days:
        return 'ACTIVE_LAST_30_DAYS'
    elif row['LastActivity'] >= cutoff_90_days:
        return 'ACTIVE_31_90_DAYS'
    else:
        return 'INACTIVE_90_PLUS_DAYS'


def main():
    print("=" * 70)
    print("International Address/Phone Members - Digital Banking Activity Check")
    print("=" * 70)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Calculate date cutoffs
    today = datetime.now()
    cutoff_90_days = today - timedelta(days=90)
    cutoff_30_days = today - timedelta(days=30)

    # Step 1: Query DWHA for international members
    print("Step 1: Connecting to DWHA...")
    dwha_conn = get_dwha_connection()
    print("Connected to DWHA successfully!")

    intl_members_df = query_international_members(dwha_conn)
    dwha_conn.close()

    print(f"Found {len(intl_members_df)} international members enrolled in digital banking")
    print(f"  - With international address: {(intl_members_df['HasIntlAddress'] == 'Yes').sum()}")
    print(f"  - With international phone: {(intl_members_df['HasIntlPhone'] == 'Yes').sum()}")
    print()

    if len(intl_members_df) == 0:
        print("No international members found. Exiting.")
        return

    # Step 2: Query DBXDB for activity data
    print("Step 2: Connecting to DBXDB...")
    dbxdb_conn = get_dbxdb_connection()
    print("Connected to DBXDB successfully!")

    account_numbers = intl_members_df['AccountNumber'].tolist()
    activity_df = query_dbxdb_activity(dbxdb_conn, account_numbers)
    dbxdb_conn.close()

    print(f"Found activity data for {len(activity_df)} accounts")
    print()

    # Step 3: Merge data
    print("Step 3: Merging member and activity data...")
    merged_df = intl_members_df.merge(activity_df, on='AccountNumber', how='left')

    # Add activity status category
    merged_df['ActivityStatus'] = merged_df.apply(
        lambda row: categorize_activity(row, cutoff_90_days, cutoff_30_days),
        axis=1
    )

    # Add days since last activity
    merged_df['DaysSinceActivity'] = merged_df['LastActivity'].apply(
        lambda x: (today - x).days if pd.notna(x) else None
    )

    # Sort by last activity (most recent first), with nulls at end
    merged_df = merged_df.sort_values('LastActivity', ascending=False, na_position='last')

    # Step 4: Create summary statistics
    print("Step 4: Generating statistics...")
    activity_counts = merged_df['ActivityStatus'].value_counts()

    print("\nActivity Status Summary:")
    print("-" * 40)
    for status, count in activity_counts.items():
        print(f"  {status}: {count}")
    print()

    # Add International Type column to distinguish
    def get_intl_type(row):
        if row['HasIntlAddress'] == 'Yes' and row['HasIntlPhone'] == 'Yes':
            return 'Both'
        elif row['HasIntlAddress'] == 'Yes':
            return 'Address Only'
        else:
            return 'Phone Only'

    merged_df['InternationalType'] = merged_df.apply(get_intl_type, axis=1)

    # Define simplified column order
    export_columns = [
        'AccountNumber', 'FirstName', 'LastName',
        'InternationalType', 'HasIntlAddress', 'HasIntlPhone',
        'Email', 'HomePhone', 'MobilePhone',
        'Street', 'City', 'State', 'ZipCode', 'Country',
        'LastActivity', 'LastLogin', 'DaysSinceActivity', 'ActivityStatus',
        'TotalActivityCount', 'Branch'
    ]

    # Keep only columns that exist
    export_columns = [c for c in export_columns if c in merged_df.columns]
    merged_df = merged_df[export_columns]

    # Step 5: Export to Excel (single sheet)
    print(f"Step 5: Exporting to {OUTPUT_FILE}...")

    merged_df.to_excel(OUTPUT_FILE, sheet_name='INTERNATIONAL_MEMBERS', index=False, engine='openpyxl')

    print("Export complete!")
    print()

    # Print final summary
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"Total International Members (DB Enrolled): {len(merged_df)}")
    print()
    print("International Type Breakdown:")
    type_counts = merged_df['InternationalType'].value_counts()
    for itype, count in type_counts.items():
        print(f"  - {itype}: {count}")
    print()
    print("Activity Status:")
    status_counts = merged_df['ActivityStatus'].value_counts()
    for status, count in status_counts.items():
        print(f"  - {status}: {count}")
    print()
    print(f"Report saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
