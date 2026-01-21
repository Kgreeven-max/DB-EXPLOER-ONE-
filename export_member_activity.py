#!/usr/bin/env python3
"""
Export all member activity for COLGIN, KATHERINE (0001008737)
Creates multi-tab Excel spreadsheet with:
- Member Profile
- Fraud Monitor Activity (all time)
- Alert History (all time)
- Registered Devices
- Contact Information
"""

import pandas as pd
from db_connection import get_connection
from datetime import datetime, timedelta
import requests
import time

# Member info
MEMBER_NAME = "COLGIN_KATHERINE"
ACCOUNT_NUMBER = "0001008737"
OUTPUT_FILE = f"C:\\Users\\kgreeven\\Desktop\\{MEMBER_NAME}_{ACCOUNT_NUMBER}_activity.xlsx"

# IP Geolocation cache
IP_CACHE = {}

def get_ip_geolocation(ip_address):
    """Get geographic information for IP address with caching"""
    if not ip_address or pd.isna(ip_address):
        return {'city': '', 'region': '', 'isp': ''}

    # Check cache first
    if ip_address in IP_CACHE:
        return IP_CACHE[ip_address]

    try:
        # Using ip-api.com (free, no key needed, 45 req/min limit)
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=3
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                result = {
                    'city': data.get('city', ''),
                    'region': data.get('regionName', ''),
                    'isp': data.get('isp', '')
                }
                IP_CACHE[ip_address] = result
                return result

        # Rate limit - wait a bit
        time.sleep(0.5)
    except Exception:
        pass

    # Default if lookup fails
    default = {'city': '', 'region': '', 'isp': ''}
    IP_CACHE[ip_address] = default
    return default

def main():
    print(f"Exporting all activity for {MEMBER_NAME} ({ACCOUNT_NUMBER})")
    print("=" * 60)

    conn = get_connection()

    try:
        # Step 1: Find ALL userNames from fraudmonitor using account number
        print("\n[1/6] Finding associated userName(s)...")
        username_query = """
            SELECT DISTINCT userName
            FROM fraudmonitor
            WHERE masterMembership = %s AND userName IS NOT NULL
        """
        df_users = pd.read_sql(username_query, conn, params=[ACCOUNT_NUMBER])

        usernames = df_users['userName'].tolist() if not df_users.empty else []
        print(f"    Found usernames from fraudmonitor: {usernames}")

        # Step 2: Get Customer_Id from customer table (search by name too)
        print("\n[2/6] Getting Customer_Id from customer table...")
        customer_id = None

        # Search by name since usernames may have changed
        customer_query = """
            SELECT id, UserName, FirstName, LastName, Status_id, createdts
            FROM customer
            WHERE LastName LIKE %s
        """
        df_customer = pd.read_sql(customer_query, conn, params=['%COLGIN%'])

        if not df_customer.empty:
            customer_id = df_customer['id'].iloc[0]
            current_username = df_customer['UserName'].iloc[0]
            print(f"    Found Customer_Id: {customer_id}")
            print(f"    Current username: {current_username}")

            # Add current username to list if not already there
            if current_username and current_username not in usernames:
                usernames.append(current_username)
                print(f"    All usernames: {usernames}")
        else:
            df_customer = pd.DataFrame()
            print("    No customer record found")

        # Step 3: Query fraudmonitor - ALL activity using both account# and userName
        print("\n[3/6] Querying fraudmonitor table (all time)...")
        if usernames:
            fraud_query = """
                SELECT id, sessionid, activityDate, eventCategory, eventData,
                       ipAddress, platform, platformOS, browser, muid, masterMembership, userName
                FROM fraudmonitor
                WHERE masterMembership = %s
                   OR userName IN ({})
                ORDER BY activityDate DESC
            """.format(','.join(['%s'] * len(usernames)))
            fraud_params = [ACCOUNT_NUMBER] + usernames
        else:
            fraud_query = """
                SELECT id, sessionid, activityDate, eventCategory, eventData,
                       ipAddress, platform, platformOS, browser, muid, masterMembership, userName
                FROM fraudmonitor
                WHERE masterMembership = %s
                ORDER BY activityDate DESC
            """
            fraud_params = [ACCOUNT_NUMBER]

        df_fraud = pd.read_sql(fraud_query, conn, params=fraud_params)
        print(f"    Found {len(df_fraud)} fraud monitor records")

        # Add PST time column (UTC - 8 hours)
        if not df_fraud.empty and 'activityDate' in df_fraud.columns:
            print("    Adding PST time column...")
            df_fraud['activityDate_PST'] = df_fraud['activityDate'] - timedelta(hours=8)

            # Reorder columns to put PST right after UTC
            cols = df_fraud.columns.tolist()
            utc_idx = cols.index('activityDate')
            cols.remove('activityDate_PST')
            cols.insert(utc_idx + 1, 'activityDate_PST')
            df_fraud = df_fraud[cols]

        # Add IP geolocation columns
        if not df_fraud.empty and 'ipAddress' in df_fraud.columns:
            unique_ips = df_fraud['ipAddress'].dropna().unique()
            print(f"    Looking up {len(unique_ips)} unique IP addresses...")

            # Lookup all unique IPs first (for progress display)
            for i, ip in enumerate(unique_ips):
                if i > 0 and i % 10 == 0:
                    print(f"      Processed {i}/{len(unique_ips)} IPs...")
                get_ip_geolocation(ip)

            # Now map to dataframe
            df_fraud['IP_City'] = df_fraud['ipAddress'].apply(
                lambda ip: get_ip_geolocation(ip)['city'] if ip else '')
            df_fraud['IP_State'] = df_fraud['ipAddress'].apply(
                lambda ip: get_ip_geolocation(ip)['region'] if ip else '')
            df_fraud['IP_ISP'] = df_fraud['ipAddress'].apply(
                lambda ip: get_ip_geolocation(ip)['isp'] if ip else '')
            print(f"    IP geolocation complete!")

        # Step 4: Query alerthistory
        print("\n[4/6] Querying alerthistory table (all time)...")
        if customer_id:
            alert_query = """
                SELECT id, createdts, AlertSubTypeId, AlertCategoryId, ChannelId,
                       Status, Subject, DispatchDate, ErrorMessage, ReferenceNumber
                FROM alerthistory
                WHERE Customer_Id = %s
                ORDER BY createdts DESC
            """
            df_alerts = pd.read_sql(alert_query, conn, params=[customer_id])
        else:
            df_alerts = pd.DataFrame()
        print(f"    Found {len(df_alerts)} alert history records")

        # Add PST time column to alerts (UTC - 8 hours)
        if not df_alerts.empty and 'createdts' in df_alerts.columns:
            print("    Adding PST time column to alerts...")
            df_alerts['createdts_PST'] = df_alerts['createdts'] - timedelta(hours=8)

            # Reorder columns to put PST right after UTC
            cols = df_alerts.columns.tolist()
            utc_idx = cols.index('createdts')
            cols.remove('createdts_PST')
            cols.insert(utc_idx + 1, 'createdts_PST')
            df_alerts = df_alerts[cols]

        # Step 5: Query customerdevice
        print("\n[5/6] Querying customerdevice table...")
        if customer_id:
            device_query = """
                SELECT DeviceName, OperatingSystem, Status_id, createdts
                FROM customerdevice
                WHERE Customer_id = %s
                ORDER BY createdts DESC
            """
            df_devices = pd.read_sql(device_query, conn, params=[customer_id])
        else:
            df_devices = pd.DataFrame()
        print(f"    Found {len(df_devices)} device records")

        # Step 6: Query customercommunication
        print("\n[6/6] Querying customercommunication table...")
        if customer_id:
            comm_query = """
                SELECT Type_id, Value, isPrimary, createdts
                FROM customercommunication
                WHERE Customer_id = %s
            """
            df_comms = pd.read_sql(comm_query, conn, params=[customer_id])
        else:
            df_comms = pd.DataFrame()
        print(f"    Found {len(df_comms)} contact records")

        # Write to Excel with multiple tabs
        print("\n" + "=" * 60)
        print(f"Writing to Excel: {OUTPUT_FILE}")

        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            # Tab 1: Member Profile
            if not df_customer.empty:
                df_customer.to_excel(writer, sheet_name='Member Profile', index=False)
            else:
                pd.DataFrame({'Info': ['No customer record found']}).to_excel(
                    writer, sheet_name='Member Profile', index=False)

            # Tab 2: Fraud Monitor Activity
            if not df_fraud.empty:
                df_fraud.to_excel(writer, sheet_name='Fraud Monitor', index=False)
            else:
                pd.DataFrame({'Info': ['No fraud monitor records found']}).to_excel(
                    writer, sheet_name='Fraud Monitor', index=False)

            # Tab 3: Alert History
            if not df_alerts.empty:
                df_alerts.to_excel(writer, sheet_name='Alert History', index=False)
            else:
                pd.DataFrame({'Info': ['No alert history found']}).to_excel(
                    writer, sheet_name='Alert History', index=False)

            # Tab 4: Registered Devices
            if not df_devices.empty:
                df_devices.to_excel(writer, sheet_name='Devices', index=False)
            else:
                pd.DataFrame({'Info': ['No device records found']}).to_excel(
                    writer, sheet_name='Devices', index=False)

            # Tab 5: Contact Information
            if not df_comms.empty:
                df_comms.to_excel(writer, sheet_name='Contact Info', index=False)
            else:
                pd.DataFrame({'Info': ['No contact records found']}).to_excel(
                    writer, sheet_name='Contact Info', index=False)

        print("\n" + "=" * 60)
        print("EXPORT COMPLETE!")
        print(f"File saved to: {OUTPUT_FILE}")
        print("\nSummary:")
        print(f"  - Member Profile: {len(df_customer)} record(s)")
        print(f"  - Fraud Monitor:  {len(df_fraud)} record(s)")
        print(f"  - Alert History:  {len(df_alerts)} record(s)")
        print(f"  - Devices:        {len(df_devices)} record(s)")
        print(f"  - Contact Info:   {len(df_comms)} record(s)")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
