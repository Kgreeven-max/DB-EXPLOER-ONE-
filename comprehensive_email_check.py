#!/usr/bin/env python3
"""
Comprehensive check for OTP emails vs profile emails
Links fraudmonitor -> customer -> customercommunication via userName
"""

from db_connection import get_connection
import re

conn = get_connection()
cursor = conn.cursor()

# Extract email from eventData
def extract_otp_email(event_data):
    match = re.search(r'"email",\s*"([^"]+)"', str(event_data))
    if match:
        return match.group(1)
    return None

# Step 1: Get OTPs to suspicious domains
print("STEP 1 - OTP events to suspicious domains (.xyz, .top, mailclone, ibande)")
print("=" * 70)
query = """
SELECT DISTINCT f.muid, f.userName, f.eventData, f.activityDate
FROM fraudmonitor f
WHERE f.eventCategory = 'OTP Authentication'
AND (f.eventData LIKE '%ibande%'
     OR f.eventData LIKE '%mailclone%'
     OR f.eventData LIKE '%zenmail.top%')
ORDER BY f.activityDate DESC
"""
cursor.execute(query)
otp_events = cursor.fetchall()
print(f"Found {len(otp_events)} OTP events\n")

# Step 2: For each, find the username and check profile
print("STEP 2 - Cross-reference with profiles")
print("=" * 70)

# Get unique muids and find their usernames
unique_muids = list(set([r[0] for r in otp_events]))
print(f"Unique members: {len(unique_muids)}\n")

for muid in unique_muids:
    print(f"\n{'='*70}")
    print(f"MUID: {muid}")

    # Get username for this muid
    cursor.execute("""
        SELECT DISTINCT userName FROM fraudmonitor
        WHERE muid = %s AND userName IS NOT NULL AND userName != ''
        LIMIT 5
    """, (muid,))
    usernames = [r[0] for r in cursor.fetchall()]
    print(f"Usernames in fraudmonitor: {usernames}")

    # Get OTP emails sent to this member
    cursor.execute("""
        SELECT eventData, activityDate FROM fraudmonitor
        WHERE muid = %s AND eventCategory = 'OTP Authentication'
        AND (eventData LIKE '%%ibande%%' OR eventData LIKE '%%mailclone%%' OR eventData LIKE '%%zenmail.top%%')
        ORDER BY activityDate DESC
        LIMIT 5
    """, (muid,))
    otp_records = cursor.fetchall()

    otp_emails = []
    for r in otp_records:
        email = extract_otp_email(r[0])
        if email:
            otp_emails.append((email, r[1]))

    print(f"OTP emails sent:")
    for email, date in otp_emails:
        print(f"  - {email} ({date})")

    # Get profile emails via customer table
    profile_emails = []
    for username in usernames:
        cursor.execute("""
            SELECT c.id, c.FirstName, c.LastName, cc.Value
            FROM customer c
            LEFT JOIN customercommunication cc ON c.id = cc.Customer_id AND cc.Value LIKE '%%%%@%%%%'
            WHERE c.UserName = %s
        """, (username,))
        results = cursor.fetchall()
        for r in results:
            if r[3]:  # has email
                profile_emails.append(r[3])
            if r[0]:
                print(f"Customer record: {r[1]} {r[2]} (id: {r[0]})")

    print(f"Profile emails:")
    if not profile_emails:
        print("  (none found in customercommunication)")
    for pe in profile_emails:
        print(f"  - {pe}")

    # Check match
    profile_emails_lower = [pe.lower() for pe in profile_emails]
    print(f"\nANALYSIS:")
    for email, date in otp_emails:
        if email.lower() in profile_emails_lower:
            print(f"  {email} -> IN PROFILE (expected)")
        else:
            print(f"  {email} -> *** NOT IN PROFILE ***")

    # Check for email change events
    cursor.execute("""
        SELECT eventCategory, COUNT(*) FROM fraudmonitor
        WHERE muid = %s
        AND eventCategory IN ('Change Primary email', 'Change Alternate email')
        GROUP BY eventCategory
    """, (muid,))
    email_changes = cursor.fetchall()
    print(f"Email change events in fraudmonitor:")
    if not email_changes:
        print("  (none)")
    for ec in email_changes:
        print(f"  - {ec[0]}: {ec[1]} events")

cursor.close()
conn.close()

print("\n")
print("=" * 70)
print("FINAL SUMMARY - Cases matching cgregory pattern")
print("(OTP to email NOT in profile + NO email change event logged)")
print("=" * 70)
