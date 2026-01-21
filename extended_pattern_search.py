#!/usr/bin/env python3
"""
Extended search - go back 1 year to find OTP email mismatches
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

def get_domain(email):
    if '@' in email:
        return email.split('@')[1].lower()
    return None

def emails_could_match(otp_email, profile_email):
    """Check if masked OTP email could match profile email"""
    otp = otp_email.lower()
    profile = profile_email.lower()
    if otp == profile:
        return True
    otp_domain = get_domain(otp)
    profile_domain = get_domain(profile)
    if otp_domain == profile_domain:
        otp_local = otp.split('@')[0]
        profile_local = profile.split('@')[0]
        if 'x' in otp_local:
            if len(otp_local) == len(profile_local) or otp_local[0] == profile_local[0]:
                return True
    return False

# Get OTP events to email - go back 1 YEAR
print("Finding OTP events sent to email (last 365 days)...")
print("=" * 70)

cursor.execute("""
    SELECT muid, userName, eventData, activityDate
    FROM fraudmonitor
    WHERE eventCategory = 'OTP Authentication'
    AND eventData LIKE '%%"email"%%'
    AND activityDate > DATE_SUB(NOW(), INTERVAL 365 DAY)
    ORDER BY activityDate DESC
""")
otp_events = cursor.fetchall()
print(f"Found {len(otp_events)} OTP email events\n")

# Build unique muid/email combinations
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
print("Checking each against profile emails...")

# Check each - find REAL mismatches where domain differs
real_mismatches = []
checked = 0
for key, case in otp_cases.items():
    checked += 1
    if checked % 100 == 0:
        print(f"  Checked {checked}/{len(otp_cases)}...")

    muid = case['muid']
    otp_email = case['otp_email']

    # Get username
    if not case['username']:
        cursor.execute("""
            SELECT DISTINCT userName FROM fraudmonitor
            WHERE muid = %s AND userName IS NOT NULL AND userName != ''
            LIMIT 1
        """, (muid,))
        row = cursor.fetchone()
        if row:
            case['username'] = row[0]

    # Get profile emails
    profile_emails = []
    if case['username']:
        cursor.execute("""
            SELECT cc.Value
            FROM customer c
            JOIN customercommunication cc ON c.id = cc.Customer_id
            WHERE c.UserName = %s AND cc.Value LIKE '%%%%@%%%%'
        """, (case['username'],))
        profile_emails = [r[0] for r in cursor.fetchall()]

    # Check match
    could_match = any(emails_could_match(otp_email, pe) for pe in profile_emails)

    if not profile_emails:
        otp_domain = get_domain(otp_email)
        common_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'icloud.com',
                         'outlook.com', 'aol.com', 'me.com', 'att.net', 'cox.net',
                         'sbcglobal.net', 'msn.com', 'live.com', 'mail.com']
        if otp_domain and otp_domain not in common_domains:
            case['profile_emails'] = []
            case['reason'] = 'No profile + unusual domain'
            real_mismatches.append(case)
    elif not could_match:
        case['profile_emails'] = profile_emails
        case['reason'] = 'Domain mismatch'
        real_mismatches.append(case)

cursor.close()
conn.close()

print(f"\n{'='*70}")
print(f"REAL MISMATCHES FOUND: {len(real_mismatches)}")
print("=" * 70)

for m in real_mismatches:
    print(f"\nMUID: {m['muid']}")
    print(f"Username: {m['username']}")
    print(f"OTP to: {m['otp_email']}")
    print(f"Profile: {m['profile_emails'] if m['profile_emails'] else '(none)'}")
    print(f"Reason: {m['reason']}")
    print(f"Date: {m['date']}")
