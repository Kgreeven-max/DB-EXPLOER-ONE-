#!/usr/bin/env python3
"""
Check ALL OTP email events vs profile emails (not just suspicious domains)
"""

from db_connection import get_connection
import re

conn = get_connection()
cursor = conn.cursor()

def extract_otp_email(event_data):
    match = re.search(r'"email",\s*"([^"]+)"', str(event_data))
    if match:
        return match.group(1)
    return None

# Get recent OTP events to email (last 60 days)
print("Finding OTP events sent to email (last 60 days)...")
print("=" * 70)

cursor.execute("""
    SELECT muid, userName, eventData, activityDate
    FROM fraudmonitor
    WHERE eventCategory = 'OTP Authentication'
    AND eventData LIKE '%%"email"%%'
    AND activityDate > DATE_SUB(NOW(), INTERVAL 60 DAY)
    ORDER BY activityDate DESC
    LIMIT 500
""")
otp_events = cursor.fetchall()
print(f"Found {len(otp_events)} OTP email events\n")

# Build list of unique muid/email combinations
otp_cases = {}
for muid, username, event_data, activity_date in otp_events:
    otp_email = extract_otp_email(event_data)
    if otp_email and muid:
        key = (muid, otp_email)
        if key not in otp_cases:
            otp_cases[key] = {
                'muid': muid,
                'username': username,
                'otp_email': otp_email,
                'date': activity_date
            }

print(f"Unique muid/email combinations: {len(otp_cases)}\n")

# Check each against profile
mismatches = []
for key, case in otp_cases.items():
    muid = case['muid']
    otp_email = case['otp_email']

    # Get username for this muid
    if not case['username']:
        cursor.execute("""
            SELECT DISTINCT userName FROM fraudmonitor
            WHERE muid = %s AND userName IS NOT NULL AND userName != ''
            LIMIT 1
        """, (muid,))
        row = cursor.fetchone()
        if row:
            case['username'] = row[0]

    # Get profile emails via customer table
    if case['username']:
        cursor.execute("""
            SELECT cc.Value
            FROM customer c
            JOIN customercommunication cc ON c.id = cc.Customer_id
            WHERE c.UserName = %s AND cc.Value LIKE '%%%%@%%%%'
        """, (case['username'],))
        profile_emails = [r[0].lower() for r in cursor.fetchall()]
    else:
        profile_emails = []

    # Check if OTP email is in profile
    if otp_email.lower() not in profile_emails:
        case['profile_emails'] = profile_emails
        mismatches.append(case)

cursor.close()
conn.close()

# Output results
print("=" * 70)
print(f"MISMATCHES FOUND: {len(mismatches)}")
print("(OTP sent to email NOT in member profile)")
print("=" * 70)

for m in mismatches:
    print(f"\nMUID: {m['muid']}")
    print(f"Username: {m['username']}")
    print(f"OTP sent to: {m['otp_email']}")
    print(f"Profile emails: {m['profile_emails'] if m['profile_emails'] else '(none found)'}")
    print(f"Date: {m['date']}")
