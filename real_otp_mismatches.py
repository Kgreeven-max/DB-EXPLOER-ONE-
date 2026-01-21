#!/usr/bin/env python3
"""
Find REAL OTP email mismatches - where domain is completely different
(Ignoring masked emails like axxx@gmail.com which match asmith@gmail.com)
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

    # Same email exactly
    if otp == profile:
        return True

    # Same domain and similar length (likely masked version)
    otp_domain = get_domain(otp)
    profile_domain = get_domain(profile)

    if otp_domain == profile_domain:
        # Same domain - likely a masked version
        otp_local = otp.split('@')[0]
        profile_local = profile.split('@')[0]
        # If OTP has x's and first/last chars match, it's masked
        if 'x' in otp_local:
            if len(otp_local) == len(profile_local):
                return True  # Same length, likely masked
            if otp_local[0] == profile_local[0]:
                return True  # Same first char, likely masked

    return False

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

# Check each against profile - find REAL mismatches
real_mismatches = []
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
        profile_emails = [r[0] for r in cursor.fetchall()]
    else:
        profile_emails = []

    # Check if OTP email could match ANY profile email
    could_match = False
    for pe in profile_emails:
        if emails_could_match(otp_email, pe):
            could_match = True
            break

    # Also check if profile emails is empty (no profile found)
    if not profile_emails:
        # No profile - check if OTP email has unusual domain
        otp_domain = get_domain(otp_email)
        if otp_domain and otp_domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'icloud.com', 'outlook.com', 'aol.com', 'me.com', 'att.net', 'cox.net', 'sbcglobal.net', 'msn.com', 'live.com', 'mail.com']:
            case['profile_emails'] = profile_emails
            case['reason'] = 'No profile found + unusual domain'
            real_mismatches.append(case)
    elif not could_match:
        # Has profile but OTP email doesn't match any
        case['profile_emails'] = profile_emails
        case['reason'] = 'OTP email domain differs from all profile emails'
        real_mismatches.append(case)

cursor.close()
conn.close()

# Output results
print("=" * 70)
print(f"REAL MISMATCHES FOUND: {len(real_mismatches)}")
print("(OTP sent to email that doesn't match any profile email)")
print("=" * 70)

for m in real_mismatches:
    print(f"\nMUID: {m['muid']}")
    print(f"Username: {m['username']}")
    print(f"OTP sent to: {m['otp_email']}")
    print(f"Profile emails: {m['profile_emails'] if m['profile_emails'] else '(none found)'}")
    print(f"Reason: {m['reason']}")
    print(f"Date: {m['date']}")
