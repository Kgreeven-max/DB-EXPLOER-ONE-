#!/usr/bin/env python3
"""
Filter for truly suspicious domains only
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

# Suspicious TLDs and domains
SUSPICIOUS_TLDS = ['.xyz', '.top', '.ru', '.online', '.click', '.link', '.win', '.bid']
SUSPICIOUS_DOMAINS = ['yandex', 'mailclone', 'ibande', 'zenmail', 'protonmail']

def is_suspicious_domain(email):
    if not email:
        return False
    email_lower = email.lower()
    for tld in SUSPICIOUS_TLDS:
        if email_lower.endswith(tld):
            return True
    for domain in SUSPICIOUS_DOMAINS:
        if domain in email_lower:
            return True
    return False

# QUERY 1: Get OTP events (1 year)
print("Pulling OTP email events...")
cursor.execute("""
    SELECT muid, userName, eventData, activityDate
    FROM fraudmonitor
    WHERE eventCategory = 'OTP Authentication'
    AND eventData LIKE '%"email"%'
    AND activityDate > DATE_SUB(NOW(), INTERVAL 365 DAY)
""")
otp_events = cursor.fetchall()
print(f"  Got {len(otp_events)} rows\n")

# QUERY 2: Get profile emails
print("Pulling profile emails...")
cursor.execute("""
    SELECT c.UserName, cc.Value
    FROM customer c
    JOIN customercommunication cc ON c.id = cc.Customer_id
    WHERE cc.Value LIKE '%@%'
""")
profile_rows = cursor.fetchall()
print(f"  Got {len(profile_rows)} rows\n")

# QUERY 3: Get email change events
print("Pulling email change events...")
cursor.execute("""
    SELECT muid FROM fraudmonitor
    WHERE eventCategory IN ('Change Primary email', 'Change Alternate email')
""")
email_change_muids = {row[0] for row in cursor.fetchall()}
print(f"  Got {len(email_change_muids)} members with email changes\n")

cursor.close()
conn.close()

# Build profile lookup
profile_emails = {}
for username, email in profile_rows:
    if username:
        key = username.lower()
        if key not in profile_emails:
            profile_emails[key] = set()
        profile_emails[key].add(email.lower())

# Find suspicious OTP cases
print("Finding suspicious OTP events...")
suspicious_cases = []

seen = set()
for muid, username, event_data, activity_date in otp_events:
    otp_email = extract_otp_email(event_data)
    if not otp_email or not is_suspicious_domain(otp_email):
        continue

    key = (muid, otp_email.lower())
    if key in seen:
        continue
    seen.add(key)

    # Check if in profile
    user_emails = profile_emails.get(username.lower(), set()) if username else set()
    in_profile = otp_email.lower() in user_emails

    # Check if has email change
    has_change = muid in email_change_muids

    suspicious_cases.append({
        'muid': muid,
        'username': username,
        'otp_email': otp_email,
        'date': activity_date,
        'in_profile': in_profile,
        'has_email_change': has_change,
        'profile_emails': list(user_emails)
    })

print(f"\n{'='*70}")
print(f"SUSPICIOUS DOMAIN OTPs FOUND: {len(suspicious_cases)}")
print("=" * 70)

# Categorize
not_in_profile_no_change = []
not_in_profile_has_change = []
in_profile = []

for c in suspicious_cases:
    if c['in_profile']:
        in_profile.append(c)
    elif c['has_email_change']:
        not_in_profile_has_change.append(c)
    else:
        not_in_profile_no_change.append(c)

print(f"\nIn profile (probably legitimate): {len(in_profile)}")
print(f"Not in profile BUT has email change event: {len(not_in_profile_has_change)}")
print(f"*** NOT IN PROFILE + NO EMAIL CHANGE (cgregory pattern): {len(not_in_profile_no_change)} ***")

print(f"\n{'='*70}")
print("CGREGORY PATTERN MATCHES (suspicious domain + not in profile + no email change):")
print("=" * 70)

for c in not_in_profile_no_change:
    print(f"\nMUID: {c['muid']}")
    print(f"Username: {c['username']}")
    print(f"OTP to: {c['otp_email']}")
    print(f"Profile: {c['profile_emails'] if c['profile_emails'] else '(none found)'}")
    print(f"Date: {c['date']}")
