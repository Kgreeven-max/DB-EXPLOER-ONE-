#!/usr/bin/env python3
"""
Fast pattern search - bulk SQL pulls, Python processing
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

# QUERY 1: Get ALL OTP email events (last 1 year)
print("QUERY 1: Pulling OTP email events (1 year)...")
cursor.execute("""
    SELECT muid, userName, eventData, activityDate
    FROM fraudmonitor
    WHERE eventCategory = 'OTP Authentication'
    AND eventData LIKE '%"email"%'
    AND activityDate > DATE_SUB(NOW(), INTERVAL 365 DAY)
""")
otp_events = cursor.fetchall()
print(f"  Got {len(otp_events)} rows\n")

# QUERY 2: Get ALL profile emails (customer + customercommunication)
print("QUERY 2: Pulling all profile emails...")
cursor.execute("""
    SELECT c.UserName, cc.Value
    FROM customer c
    JOIN customercommunication cc ON c.id = cc.Customer_id
    WHERE cc.Value LIKE '%@%'
""")
profile_rows = cursor.fetchall()
print(f"  Got {len(profile_rows)} rows\n")

# QUERY 3: Get all email change events
print("QUERY 3: Pulling email change events...")
cursor.execute("""
    SELECT muid, eventCategory, activityDate
    FROM fraudmonitor
    WHERE eventCategory IN ('Change Primary email', 'Change Alternate email')
""")
email_change_rows = cursor.fetchall()
print(f"  Got {len(email_change_rows)} rows\n")

cursor.close()
conn.close()

# BUILD LOOKUP DICTIONARIES IN PYTHON
print("Building lookup tables...")

# Profile emails by username (lowercase)
profile_emails = {}
for username, email in profile_rows:
    if username:
        key = username.lower()
        if key not in profile_emails:
            profile_emails[key] = set()
        profile_emails[key].add(email.lower())

# Email change events by muid
has_email_change = set()
for muid, cat, date in email_change_rows:
    has_email_change.add(muid)

print(f"  {len(profile_emails)} users with profile emails")
print(f"  {len(has_email_change)} members with email change events\n")

# PROCESS OTP EVENTS
print("Processing OTP events...")

# Build unique cases
otp_cases = {}
for muid, username, event_data, activity_date in otp_events:
    otp_email = extract_otp_email(event_data)
    if otp_email and muid:
        key = (muid, otp_email.lower())
        if key not in otp_cases:
            otp_cases[key] = {
                'muid': muid,
                'username': username,
                'otp_email': otp_email,
                'date': activity_date
            }

print(f"  {len(otp_cases)} unique muid/email combinations\n")

# FIND MISMATCHES
print("Finding mismatches...")
mismatches = []

for (muid, otp_email_lower), case in otp_cases.items():
    username = case['username']
    otp_email = case['otp_email']
    otp_domain = get_domain(otp_email)

    # Get profile emails for this user
    user_profile_emails = set()
    if username:
        user_profile_emails = profile_emails.get(username.lower(), set())

    # Check if OTP email domain matches any profile email domain
    profile_domains = {get_domain(pe) for pe in user_profile_emails}

    # MISMATCH if: OTP domain not in profile domains
    if otp_domain and otp_domain not in profile_domains:
        # Skip common domains if no profile found (could be new user)
        common = ['gmail.com', 'yahoo.com', 'hotmail.com', 'icloud.com',
                  'outlook.com', 'aol.com', 'me.com', 'att.net', 'cox.net']

        if not user_profile_emails and otp_domain in common:
            continue  # Skip - probably new user with common email

        case['profile_emails'] = list(user_profile_emails)
        case['has_email_change'] = muid in has_email_change
        mismatches.append(case)

# FILTER: Only show cases with NO email change event (cgregory pattern)
cgregory_pattern = [m for m in mismatches if not m['has_email_change']]

print(f"\n{'='*70}")
print(f"TOTAL DOMAIN MISMATCHES: {len(mismatches)}")
print(f"CGREGORY PATTERN (no email change event): {len(cgregory_pattern)}")
print("=" * 70)

for m in cgregory_pattern:
    print(f"\nMUID: {m['muid']}")
    print(f"Username: {m['username']}")
    print(f"OTP to: {m['otp_email']}")
    print(f"Profile emails: {m['profile_emails'] if m['profile_emails'] else '(none)'}")
    print(f"Date: {m['date']}")
