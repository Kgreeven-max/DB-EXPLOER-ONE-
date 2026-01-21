#!/usr/bin/env python3
"""
Export all customers with suspicious email domains
Includes: Russian, Privacy (Proton, Tuta), Throwaway, and other risky TLDs
"""

import pandas as pd
from db_connection import get_connection
from datetime import datetime

OUTPUT_FILE = f"C:\\Users\\kgreeven\\Desktop\\SUSPICIOUS_EMAILS_REPORT_{datetime.now().strftime('%Y%m%d')}.xlsx"

def classify_email(email):
    """Classify email by domain type"""
    if not email:
        return "UNKNOWN"

    email = email.lower()

    # Russian domains
    if any(d in email for d in ['@mail.ru', '@yandex.', '@inbox.ru', '@bk.ru', '@list.ru', '@rambler.', '.ru']):
        return "RUSSIAN"

    # Ukrainian
    if '.ua' in email or '@ukr.net' in email:
        return "UKRAINIAN"

    # Belarus
    if '.by' in email:
        return "BELARUS"

    # Soviet legacy
    if '.su' in email:
        return "SOVIET"

    # Proton - REMOVED FROM SUSPICIOUS LIST
    # if any(d in email for d in ['@proton.me', '@protonmail.', '@pm.me']):
    #     return "PROTON"

    # Tuta
    if any(d in email for d in ['@tuta.', '@tutanota.', '@tuta.io']):
        return "TUTA"

    # Guerrilla/Temp mail
    if any(d in email for d in ['guerrilla', 'tempmail', 'temp-mail', '10minute', 'throwaway',
                                 'mailinator', 'sharklasers', 'maildrop', 'yopmail']):
        return "THROWAWAY"

    # Suspicious TLDs
    if any(email.endswith(tld) for tld in ['.xyz', '.tk', '.ml', '.ga', '.cf', '.click', '.top', '.buzz']):
        return "SUSPICIOUS_TLD"

    # Other privacy
    if any(d in email for d in ['@cock.li', '@airmail.cc', '@dnmx.', '@onionmail.']):
        return "DARK_WEB"

    return "OTHER"


def is_gibberish(email):
    """Check if email looks like random gibberish (fraud indicator)"""
    if not email or '@' not in email:
        return False

    local_part = email.split('@')[0].lower()

    # Check for patterns that look like random characters
    vowels = sum(1 for c in local_part if c in 'aeiou')
    consonants = sum(1 for c in local_part if c.isalpha() and c not in 'aeiou')

    # Very low vowel ratio suggests gibberish
    if len(local_part) > 6 and vowels > 0:
        ratio = consonants / vowels if vowels > 0 else 10
        if ratio > 4:  # Too many consonants
            return True

    # Check for repeated patterns
    if len(set(local_part)) < len(local_part) / 3 and len(local_part) > 8:
        return True

    return False


def main():
    print("=" * 70)
    print("SUSPICIOUS EMAIL DOMAIN SCANNER")
    print("=" * 70)

    conn = get_connection()

    try:
        # Query for all suspicious emails with member details
        print("\n[1/4] Querying suspicious emails from customercommunication...")

        query = """
            SELECT
                c.id as Customer_Id,
                c.UserName,
                c.FirstName,
                c.LastName,
                c.Status_id,
                c.createdts as Account_Created,
                cc.Value as Email,
                cc.Type_id as Email_Type,
                cc.isPrimary,
                cc.createdts as Email_Created,
                cc.lastmodifiedts as Email_Last_Modified
            FROM customercommunication cc
            JOIN customer c ON cc.Customer_id = c.id
            WHERE cc.Type_id LIKE '%EMAIL%'
            AND (
                -- Russian/Eastern European
                LOWER(cc.Value) LIKE '%@%.ru'
                OR LOWER(cc.Value) LIKE '%@mail.ru'
                OR LOWER(cc.Value) LIKE '%@yandex.%'
                OR LOWER(cc.Value) LIKE '%@inbox.ru'
                OR LOWER(cc.Value) LIKE '%@bk.ru'
                OR LOWER(cc.Value) LIKE '%@list.ru'
                OR LOWER(cc.Value) LIKE '%@rambler.%'
                OR LOWER(cc.Value) LIKE '%@%.ua'
                OR LOWER(cc.Value) LIKE '%@ukr.net'
                OR LOWER(cc.Value) LIKE '%@%.by'
                OR LOWER(cc.Value) LIKE '%@%.su'
                -- Privacy emails (Proton removed - too many legitimate users)
                OR LOWER(cc.Value) LIKE '%@tuta.%'
                OR LOWER(cc.Value) LIKE '%@tutanota.%'
                -- Throwaway
                OR LOWER(cc.Value) LIKE '%guerrilla%'
                OR LOWER(cc.Value) LIKE '%tempmail%'
                OR LOWER(cc.Value) LIKE '%mailinator%'
                OR LOWER(cc.Value) LIKE '%sharklasers%'
                -- Suspicious TLDs
                OR LOWER(cc.Value) LIKE '%@%.xyz'
                OR LOWER(cc.Value) LIKE '%@%.tk'
                OR LOWER(cc.Value) LIKE '%@%.ml'
                OR LOWER(cc.Value) LIKE '%@%.ga'
                OR LOWER(cc.Value) LIKE '%@%.cf'
                OR LOWER(cc.Value) LIKE '%@%.click'
                OR LOWER(cc.Value) LIKE '%@%.top'
                -- Dark web
                OR LOWER(cc.Value) LIKE '%@cock.li'
                OR LOWER(cc.Value) LIKE '%@airmail.cc'
            )
            ORDER BY c.LastName, c.FirstName
        """

        df = pd.read_sql(query, conn)
        print(f"    Found {len(df)} suspicious email records")

        # Add classification columns
        print("\n[2/4] Classifying emails...")
        df['Domain_Type'] = df['Email'].apply(classify_email)
        df['Looks_Gibberish'] = df['Email'].apply(is_gibberish)
        df['Is_Active'] = df['Status_id'] == 'SID_CUS_ACTIVE'

        # Get member numbers and all usernames from fraudmonitor
        print("\n[3/4] Looking up member numbers and all usernames from fraudmonitor...")

        cursor = conn.cursor()

        # Get unique customer IDs
        customer_ids = df['Customer_Id'].unique().tolist()

        # Query fraudmonitor for member numbers - get ALL associated data
        member_data = {}  # username -> {member_numbers: set, all_usernames: set, muid: str}

        # Batch query - get all usernames and their member numbers
        username_list = df['UserName'].unique().tolist()

        if username_list:
            placeholders = ','.join(['%s'] * len(username_list))

            # Get member numbers, muid, first seen, and last active for each username
            member_query = f"""
                SELECT userName, masterMembership, muid,
                       MIN(activityDate) as first_seen,
                       MAX(activityDate) as last_active
                FROM fraudmonitor
                WHERE userName IN ({placeholders})
                GROUP BY userName, masterMembership, muid
            """
            cursor.execute(member_query, username_list)
            results = cursor.fetchall()

            for row in results:
                username, member_num, muid, first_seen, last_active = row
                if username:
                    if username not in member_data:
                        member_data[username] = {
                            'member_numbers': set(),
                            'muid': None,
                            'first_seen': None,
                            'last_active': None
                        }
                    if member_num:
                        member_data[username]['member_numbers'].add(member_num)
                    if muid:
                        member_data[username]['muid'] = muid
                    # Track earliest first_seen and latest last_active
                    if first_seen:
                        if member_data[username]['first_seen'] is None or first_seen < member_data[username]['first_seen']:
                            member_data[username]['first_seen'] = first_seen
                    if last_active:
                        if member_data[username]['last_active'] is None or last_active > member_data[username]['last_active']:
                            member_data[username]['last_active'] = last_active

            # Now for each MUID, find ALL usernames ever used
            muids = set()
            for data in member_data.values():
                if data['muid']:
                    muids.add(data['muid'])

            all_usernames_by_muid = {}
            if muids:
                muid_placeholders = ','.join(['%s'] * len(muids))
                all_users_query = f"""
                    SELECT DISTINCT muid, userName
                    FROM fraudmonitor
                    WHERE muid IN ({muid_placeholders})
                    AND userName IS NOT NULL
                """
                cursor.execute(all_users_query, list(muids))
                muid_results = cursor.fetchall()

                for muid, uname in muid_results:
                    if muid not in all_usernames_by_muid:
                        all_usernames_by_muid[muid] = set()
                    all_usernames_by_muid[muid].add(uname)

            # Map all usernames back to each username
            for username, data in member_data.items():
                if data['muid'] and data['muid'] in all_usernames_by_muid:
                    data['all_usernames'] = all_usernames_by_muid[data['muid']]
                else:
                    data['all_usernames'] = {username}

        # Get email change dates for each user
        print("    Looking up email change dates...")
        email_change_data = {}
        if username_list:
            cursor2 = conn.cursor()
            placeholders2 = ','.join(['%s'] * len(username_list))
            email_change_query = f"""
                SELECT userName, activityDate, eventData
                FROM fraudmonitor
                WHERE userName IN ({placeholders2})
                AND (eventCategory LIKE '%%email%%' OR eventCategory LIKE '%%Email%%')
                ORDER BY activityDate DESC
            """
            cursor2.execute(email_change_query, username_list)
            email_results = cursor2.fetchall()

            for username, change_date, event_data in email_results:
                if username:
                    if username not in email_change_data:
                        email_change_data[username] = {
                            'last_email_change': change_date,
                            'email_change_details': event_data
                        }
                    # Keep the most recent (first one due to ORDER BY DESC)
            cursor2.close()

        cursor.close()
        print(f"    Found email change data for {len(email_change_data)} users")

        # Add columns
        df['Member_Numbers'] = df['UserName'].apply(
            lambda u: ', '.join(sorted(member_data.get(u, {}).get('member_numbers', set()))) if u in member_data else '')
        df['MUID'] = df['UserName'].apply(
            lambda u: member_data.get(u, {}).get('muid', '') if u in member_data else '')
        df['All_Usernames'] = df['UserName'].apply(
            lambda u: ', '.join(sorted(member_data.get(u, {}).get('all_usernames', set()))) if u in member_data else u)
        df['First_Seen'] = df['UserName'].apply(
            lambda u: member_data.get(u, {}).get('first_seen', '') if u in member_data else '')
        df['Last_Active'] = df['UserName'].apply(
            lambda u: member_data.get(u, {}).get('last_active', '') if u in member_data else '')
        df['Email_Changed_Date'] = df['UserName'].apply(
            lambda u: email_change_data.get(u, {}).get('last_email_change', '') if u in email_change_data else '')
        df['Email_Change_Details'] = df['UserName'].apply(
            lambda u: email_change_data.get(u, {}).get('email_change_details', '') if u in email_change_data else '')

        print(f"    Found member data for {len(member_data)} users")

        # Reorder columns
        df = df[['Domain_Type', 'Is_Active', 'Looks_Gibberish', 'Member_Numbers', 'MUID',
                 'UserName', 'All_Usernames', 'FirstName', 'LastName', 'Email',
                 'Email_Created', 'Email_Last_Modified',
                 'First_Seen', 'Last_Active', 'Email_Type',
                 'isPrimary', 'Status_id', 'Account_Created', 'Customer_Id']]

        # Create separate dataframes by category
        print("\n[4/4] Writing Excel report...")

        df_russian = df[df['Domain_Type'].isin(['RUSSIAN', 'UKRAINIAN', 'BELARUS', 'SOVIET'])].copy()
        df_tuta = df[df['Domain_Type'] == 'TUTA'].copy()
        df_throwaway = df[df['Domain_Type'] == 'THROWAWAY'].copy()
        df_suspicious_tld = df[df['Domain_Type'] == 'SUSPICIOUS_TLD'].copy()
        df_other = df[df['Domain_Type'].isin(['DARK_WEB', 'OTHER'])].copy()

        # Filter active only for summary
        df_active = df[df['Is_Active'] == True].copy()
        df_gibberish = df[(df['Looks_Gibberish'] == True) & (df['Is_Active'] == True)].copy()

        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
            # Summary tab
            summary_data = {
                'Category': ['RUSSIAN/EASTERN EUROPEAN', 'TUTA', 'THROWAWAY',
                            'SUSPICIOUS TLD (.xyz, .tk, etc)', 'OTHER/DARK WEB',
                            '', 'TOTAL ALL', 'TOTAL ACTIVE', 'GIBBERISH EMAILS (ACTIVE)'],
                'Total': [len(df_russian), len(df_tuta), len(df_throwaway),
                         len(df_suspicious_tld), len(df_other), '',
                         len(df), len(df_active), len(df_gibberish)],
                'Active': [len(df_russian[df_russian['Is_Active']]),
                          len(df_tuta[df_tuta['Is_Active']]),
                          len(df_throwaway[df_throwaway['Is_Active']]),
                          len(df_suspicious_tld[df_suspicious_tld['Is_Active']]),
                          len(df_other[df_other['Is_Active']]),
                          '', '', '', '']
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='SUMMARY', index=False)

            # Individual tabs
            if not df_russian.empty:
                df_russian.to_excel(writer, sheet_name='Russian-Eastern Euro', index=False)

            if not df_tuta.empty:
                df_tuta.to_excel(writer, sheet_name='Tuta', index=False)

            if not df_throwaway.empty:
                df_throwaway.to_excel(writer, sheet_name='Throwaway', index=False)

            if not df_suspicious_tld.empty:
                df_suspicious_tld.to_excel(writer, sheet_name='Suspicious TLD', index=False)

            if not df_other.empty:
                df_other.to_excel(writer, sheet_name='Other', index=False)

            # High risk - gibberish emails that are active
            if not df_gibberish.empty:
                df_gibberish.to_excel(writer, sheet_name='HIGH RISK - Gibberish', index=False)

            # All data
            df.to_excel(writer, sheet_name='ALL DATA', index=False)

        print("\n" + "=" * 70)
        print("EXPORT COMPLETE!")
        print("=" * 70)
        print(f"\nFile saved to: {OUTPUT_FILE}")
        print("\nSUMMARY:")
        print(f"  - Russian/Eastern European: {len(df_russian)} ({len(df_russian[df_russian['Is_Active']])} active)")
        print(f"  - Tuta/Tutanota:            {len(df_tuta)} ({len(df_tuta[df_tuta['Is_Active']])} active)")
        print(f"  - Throwaway:                {len(df_throwaway)} ({len(df_throwaway[df_throwaway['Is_Active']])} active)")
        print(f"  - Suspicious TLD:           {len(df_suspicious_tld)} ({len(df_suspicious_tld[df_suspicious_tld['Is_Active']])} active)")
        print(f"  - Other/Dark Web:           {len(df_other)} ({len(df_other[df_other['Is_Active']])} active)")
        print(f"\n  TOTAL: {len(df)} ({len(df_active)} active)")
        print(f"  HIGH RISK (Gibberish + Active): {len(df_gibberish)}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
