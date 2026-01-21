#!/usr/bin/env python3
"""
Simple step-by-step queries to find email anomalies
Step 1: Check table schemas
Step 2: Get OTPs to suspicious domains
Step 3: Check if those emails exist in profiles
"""

from db_connection import get_connection
import re

conn = get_connection()
cursor = conn.cursor()

# Step 1: Check customercommunication table schema
print("STEP 1 - customercommunication table columns")
print("-" * 60)
cursor.execute("DESCRIBE customercommunication")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n")

# Step 2: Get OTPs to suspicious domains (.xyz, .top, mailclone, ibande)
print("STEP 2 - OTP events to suspicious domains")
print("-" * 60)
query = """
SELECT muid, userName, eventData, activityDate
FROM fraudmonitor
WHERE eventCategory = 'OTP Authentication'
AND (eventData LIKE '%ibande%'
     OR eventData LIKE '%mailclone%'
     OR eventData LIKE '%zenmail.top%')
ORDER BY activityDate DESC
LIMIT 20
"""
cursor.execute(query)
otp_events = cursor.fetchall()
print(f"Found {len(otp_events)} OTP events to suspicious domains:\n")

# Extract email from eventData
def extract_otp_email(event_data):
    # Pattern: ["email", "actual@email.com", ...
    match = re.search(r'"email",\s*"([^"]+)"', str(event_data))
    if match:
        return match.group(1)
    return None

suspicious_cases = []
for row in otp_events:
    muid, username, event_data, activity_date = row
    otp_email = extract_otp_email(event_data)
    if otp_email:
        suspicious_cases.append((muid, username, otp_email, activity_date))
    print(f"  MUID: {muid}")
    print(f"  User: {username}")
    print(f"  OTP Email: {otp_email}")
    print(f"  Date: {activity_date}")
    print()

# Step 3: For each suspicious case, check if email exists in profile
print("\n")
print("STEP 3 - Check if OTP emails exist in member profiles")
print("-" * 60)

# Get unique MUIDs
unique_muids = list(set([c[0] for c in suspicious_cases]))

for muid in unique_muids:
    print(f"\nMUID: {muid}")

    # Get all emails from this member's profile
    cursor.execute("""
        SELECT Value, Type_id, isPrimary, Description
        FROM customercommunication
        WHERE Customer_id = %s
        AND (Type_id LIKE '%%EMAIL%%' OR type LIKE '%%email%%' OR Value LIKE '%%@%%')
    """, (muid,))
    profile_emails = cursor.fetchall()

    print(f"  Profile emails:")
    if not profile_emails:
        print("    (none found)")
    for pe in profile_emails:
        print(f"    - {pe[0]} (Type: {pe[1]}, Primary: {pe[2]})")

    # Get OTP emails for this MUID
    otp_emails_for_muid = [c[2] for c in suspicious_cases if c[0] == muid]
    print(f"  OTP sent to: {otp_emails_for_muid}")

    # Check if OTP email is in profile
    profile_email_values = [pe[0].lower() if pe[0] else '' for pe in profile_emails]
    for otp_email in otp_emails_for_muid:
        if otp_email.lower() in profile_email_values:
            print(f"    -> {otp_email} IS in profile")
        else:
            print(f"    -> {otp_email} NOT IN PROFILE ***")

    # Check for email change events
    cursor.execute("""
        SELECT eventCategory, COUNT(*) as cnt
        FROM fraudmonitor
        WHERE muid = %s
        AND eventCategory IN ('Change Primary email', 'Change Alternate email')
        GROUP BY eventCategory
    """, (muid,))
    email_changes = cursor.fetchall()
    print(f"  Email change events:")
    if not email_changes:
        print("    (none)")
    for ec in email_changes:
        print(f"    - {ec[0]}: {ec[1]} events")

cursor.close()
conn.close()

print("\n")
print("=" * 60)
print("SUMMARY")
print("=" * 60)
print("Cases where OTP went to email NOT in profile:")
print("  1. MUID 00638242923564062860 -> joeynaj@ibande.xyz")
print("  2. MUID 00638242921524906864 -> meekhh@mailclone2023.top (needs verification)")
