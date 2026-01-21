#!/usr/bin/env python3
"""
WAF User Lookup Script
Looks up customer information (customer_id, MUID, account number) for usernames/MUIDs
and exports to Excel.

Strategy:
1. Try customer table first (has id, UserName, Token/MUID)
2. If not found, fall back to fraudmonitor (has userName, muid, masterMembership)
"""

import pandas as pd
from db_connection import get_connection

def is_muid(entry):
    """Check if entry is a MUID (numeric, 15+ digits)"""
    return entry.isdigit() and len(entry) >= 15

def lookup_customer_by_username(cursor, username):
    """Look up customer info by username - returns (id, UserName, Token/MUID)"""
    query = """
        SELECT id, UserName, Token
        FROM customer
        WHERE LOWER(UserName) = LOWER(%s)
        LIMIT 1
    """
    cursor.execute(query, (username,))
    return cursor.fetchone()

def lookup_account_number(cursor, username):
    """Look up account number from fraudmonitor by username"""
    query = """
        SELECT masterMembership
        FROM fraudmonitor
        WHERE LOWER(userName) = LOWER(%s)
        AND masterMembership IS NOT NULL AND masterMembership != ''
        LIMIT 1
    """
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    return result[0] if result else None

def lookup_fraudmonitor_by_username(cursor, username):
    """Look up user info from fraudmonitor - returns (userName, muid, masterMembership)"""
    # First try to get a record with both muid and masterMembership
    query = """
        SELECT userName, muid, masterMembership
        FROM fraudmonitor
        WHERE LOWER(userName) = LOWER(%s)
        AND muid IS NOT NULL AND muid != ''
        AND masterMembership IS NOT NULL AND masterMembership != ''
        LIMIT 1
    """
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    if result:
        return result
    # Fall back to just muid if no masterMembership found
    query = """
        SELECT userName, muid, masterMembership
        FROM fraudmonitor
        WHERE LOWER(userName) = LOWER(%s)
        AND muid IS NOT NULL AND muid != ''
        LIMIT 1
    """
    cursor.execute(query, (username,))
    return cursor.fetchone()

def lookup_fraudmonitor_by_muid(cursor, muid):
    """Look up by MUID from fraudmonitor - returns (userName, muid, masterMembership)"""
    query = """
        SELECT userName, muid, masterMembership
        FROM fraudmonitor
        WHERE muid = %s
        LIMIT 1
    """
    cursor.execute(query, (muid,))
    return cursor.fetchone()

def lookup_customer_by_token(cursor, token):
    """Look up customer by Token (MUID) - returns (id, UserName, Token)"""
    query = """
        SELECT id, UserName, Token
        FROM customer
        WHERE Token = %s
        LIMIT 1
    """
    cursor.execute(query, (token,))
    return cursor.fetchone()

def main():
    # Read input file
    input_file = "ABZ4435_Successful_WAF_users_20260109.txt"
    with open(input_file, 'r') as f:
        entries = [line.strip() for line in f if line.strip()]

    print(f"Read {len(entries)} entries from {input_file}")

    # Connect to database
    conn = get_connection()
    cursor = conn.cursor()
    print("Connected to database")

    # Process each entry
    results = []
    for i, entry in enumerate(entries, 1):
        print(f"Processing {i}/{len(entries)}: {entry}", end=" ")

        customer_id = None
        username = None
        muid = None
        account_number = None
        source = None

        if is_muid(entry):
            # Entry is a MUID - try customer.Token first
            cust_row = lookup_customer_by_token(cursor, entry)
            if cust_row:
                customer_id = cust_row[0]
                username = cust_row[1]
                muid = cust_row[2]
                account_number = lookup_account_number(cursor, username)
                source = "customer"
            else:
                # Try fraudmonitor by muid
                fm_row = lookup_fraudmonitor_by_muid(cursor, entry)
                if fm_row:
                    username = fm_row[0]
                    muid = fm_row[1]
                    account_number = fm_row[2]
                    source = "fraudmonitor"
                    # Try to get customer_id if username exists
                    if username:
                        cust_row = lookup_customer_by_username(cursor, username)
                        if cust_row:
                            customer_id = cust_row[0]
                else:
                    muid = entry
        else:
            # Entry is a username - try customer table first
            cust_row = lookup_customer_by_username(cursor, entry)
            if cust_row:
                customer_id = cust_row[0]
                username = cust_row[1]
                muid = cust_row[2]
                account_number = lookup_account_number(cursor, entry)
                source = "customer"
            else:
                # Fall back to fraudmonitor
                fm_row = lookup_fraudmonitor_by_username(cursor, entry)
                if fm_row:
                    username = fm_row[0]
                    muid = fm_row[1]
                    account_number = fm_row[2]
                    source = "fraudmonitor"
                else:
                    username = entry

        if customer_id:
            print(f"-> OK (customer)")
        elif muid:
            print(f"-> OK (fraudmonitor only)")
        else:
            print(f"-> NOT FOUND")

        # Convert to strings to preserve full values in Excel
        results.append({
            'Input': entry,
            'UserName': username if username else '',
            'Customer_ID': str(customer_id) if customer_id else '',
            'MUID': str(muid) if muid else '',
            'Account_Number': str(int(float(account_number))) if account_number else ''
        })

    # Close database connection
    cursor.close()
    conn.close()
    print("\nDatabase connection closed")

    # Create DataFrame and export to Excel
    df = pd.DataFrame(results)
    output_file = "WAF_Users_Account_Info_v2.xlsx"
    df.to_excel(output_file, index=False, sheet_name='User Info')

    print(f"\nExported {len(results)} records to {output_file}")

    # Count results
    has_customer = len([r for r in results if r['Customer_ID']])
    has_muid_only = len([r for r in results if r['MUID'] and not r['Customer_ID']])
    not_found = len([r for r in results if not r['MUID']])

    print(f"Found in customer table: {has_customer}")
    print(f"Found in fraudmonitor only: {has_muid_only}")
    print(f"Not found anywhere: {not_found}")

if __name__ == "__main__":
    main()
