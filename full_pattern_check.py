#!/usr/bin/env python3
"""
Full cgregory pattern check:
1. No email change event category
2. Check eventData for any email update hints
3. Check customer.lastmodifiedts
"""

from db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# The 5 mismatched cases from previous query
cases = [
    ('00638243027726942559', 'agrplasterinc', 'gerardo@agrlathplasterinc.com'),
    ('00638243041658497345', 'jmhogarth', 'mxke@hogarth.org'),
    ('00638243622648358080', 'JTorres', 'Josephrt2019@gmail.com'),
    ('00638242923564062860', 'cgregory', 'joeynaj@ibande.xyz'),
    ('00638242916469024726', 'faustinechambers', 'w2faustine@yahoo.com'),
]

print("FULL PATTERN CHECK FOR 5 MISMATCH CASES")
print("=" * 80)

for muid, username, otp_email in cases:
    print(f"\n{'='*80}")
    print(f"MEMBER: {username} (MUID: {muid})")
    print(f"OTP sent to: {otp_email}")
    print("-" * 80)

    # 1. Check for email change event CATEGORY
    print("\n1. Email change events (by category):")
    cursor.execute("""
        SELECT eventCategory, COUNT(*) as cnt
        FROM fraudmonitor
        WHERE muid = %s
        AND eventCategory IN ('Change Primary email', 'Change Alternate email',
                              'Change Phone Number', 'Change of Address')
        GROUP BY eventCategory
    """, (muid,))
    changes = cursor.fetchall()
    if not changes:
        print("   NONE - No email/phone/address change events logged")
    for c in changes:
        print(f"   {c[0]}: {c[1]} events")

    # 2. Check eventData for any mention of the OTP email or email updates
    print(f"\n2. Search eventData for '{otp_email}':")
    cursor.execute("""
        SELECT eventCategory, eventData, activityDate
        FROM fraudmonitor
        WHERE muid = %s
        AND eventData LIKE %s
        ORDER BY activityDate DESC
        LIMIT 5
    """, (muid, f'%{otp_email}%'))
    mentions = cursor.fetchall()
    if not mentions:
        print(f"   NOT FOUND in any eventData")
    for m in mentions:
        print(f"   {m[2]} | {m[0]} | {str(m[1])[:80]}...")

    # 3. Check customer table lastmodifiedts
    print(f"\n3. Customer table (lastmodifiedts):")
    cursor.execute("""
        SELECT id, UserName, FirstName, LastName, lastmodifiedts, createdts
        FROM customer
        WHERE UserName = %s
    """, (username,))
    cust = cursor.fetchone()
    if cust:
        print(f"   Customer ID: {cust[0]}")
        print(f"   Name: {cust[2]} {cust[3]}")
        print(f"   Created: {cust[5]}")
        print(f"   Last Modified: {cust[4]}")

        # Check customercommunication for this customer
        print(f"\n4. Profile emails (customercommunication):")
        cursor.execute("""
            SELECT Value, lastmodifiedts, createdts
            FROM customercommunication
            WHERE Customer_id = %s AND Value LIKE '%%@%%'
        """, (cust[0],))
        emails = cursor.fetchall()
        if not emails:
            print("   (none found)")
        for e in emails:
            print(f"   {e[0]} | created: {e[2]} | modified: {e[1]}")
    else:
        print(f"   NO CUSTOMER RECORD FOUND for username '{username}'")

cursor.close()
conn.close()

print("\n")
print("=" * 80)
print("SUMMARY: Cases matching cgregory pattern")
print("(OTP to unknown email + NO email change event + NO profile update)")
print("=" * 80)
