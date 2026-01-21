#!/usr/bin/env python3
"""
Check if OTP phone anomaly exists - OTP sent to phone NOT in profile with no change event
"""

from db_connection import get_connection
import re

conn = get_connection()
cursor = conn.cursor()

def extract_phone(event_data):
    # Look for phone patterns in OTP events: ["sms", "xxx-xxx-1234", ...] or phone numbers
    # Unmasked phones look like: 619-555-1234
    match = re.search(r'"sms",\s*"([^"]+)"', str(event_data))
    if match:
        return match.group(1)
    return None

print("QUERY 1: Pulling OTP SMS events (1 year)...")
cursor.execute("""
    SELECT muid, userName, eventData, activityDate
    FROM fraudmonitor
    WHERE eventCategory = 'OTP Authentication'
    AND eventData LIKE '%"sms"%'
    AND activityDate > DATE_SUB(NOW(), INTERVAL 365 DAY)
""")
otp_events = cursor.fetchall()
print(f"  Got {len(otp_events)} SMS OTP events\n")

print("QUERY 2: Pulling profile phone numbers...")
cursor.execute("""
    SELECT c.UserName, cc.Value
    FROM customer c
    JOIN customercommunication cc ON c.id = cc.Customer_id
    WHERE cc.Type_id LIKE '%PHONE%' OR cc.Value LIKE '%-%-%'
""")
profile_rows = cursor.fetchall()
print(f"  Got {len(profile_rows)} profile phone records\n")

print("QUERY 3: Pulling phone change events...")
cursor.execute("""
    SELECT muid FROM fraudmonitor
    WHERE eventCategory = 'Change Phone Number'
""")
phone_change_muids = {row[0] for row in cursor.fetchall()}
print(f"  Got {len(phone_change_muids)} members with phone changes\n")

cursor.close()
conn.close()

# Build profile lookup (normalize phone numbers)
def normalize_phone(phone):
    if not phone:
        return None
    # Remove all non-digits
    digits = re.sub(r'\D', '', str(phone))
    # Return last 10 digits
    if len(digits) >= 10:
        return digits[-10:]
    return digits

profile_phones = {}
for username, phone in profile_rows:
    if username and phone:
        key = username.lower()
        if key not in profile_phones:
            profile_phones[key] = set()
        normalized = normalize_phone(phone)
        if normalized:
            profile_phones[key].add(normalized)

# Process OTP events
print("Processing OTP SMS events...")
otp_cases = {}
for muid, username, event_data, activity_date in otp_events:
    otp_phone = extract_phone(event_data)
    if otp_phone and muid:
        key = (muid, otp_phone)
        if key not in otp_cases:
            otp_cases[key] = {
                'muid': muid,
                'username': username,
                'otp_phone': otp_phone,
                'date': activity_date
            }

print(f"  {len(otp_cases)} unique muid/phone combinations\n")

# Find mismatches
mismatches = []
for (muid, otp_phone), case in otp_cases.items():
    username = case['username']

    # Get profile phones for this user
    user_phones = set()
    if username:
        user_phones = profile_phones.get(username.lower(), set())

    # Normalize OTP phone
    otp_normalized = normalize_phone(otp_phone)

    # Check if OTP phone matches any profile phone
    # Note: OTP phones are masked like xxx-xxx-1234, so we can only compare last 4 digits
    otp_last4 = otp_normalized[-4:] if otp_normalized and len(otp_normalized) >= 4 else None

    matches_profile = False
    for profile_phone in user_phones:
        if profile_phone and otp_last4 and profile_phone.endswith(otp_last4):
            matches_profile = True
            break

    if not matches_profile and otp_last4:
        case['profile_phones'] = list(user_phones)
        case['has_phone_change'] = muid in phone_change_muids
        case['otp_last4'] = otp_last4
        mismatches.append(case)

# Filter for anomalies (no phone change event)
anomalies = [m for m in mismatches if not m['has_phone_change']]

print(f"{'='*70}")
print(f"TOTAL PHONE MISMATCHES: {len(mismatches)}")
print(f"WITHOUT PHONE CHANGE EVENT (anomaly): {len(anomalies)}")
print("=" * 70)

# Show first 20 anomalies
print("\nFirst 20 anomalies (OTP to phone NOT in profile + NO phone change event):\n")
for m in anomalies[:20]:
    print(f"MUID: {m['muid']}")
    print(f"Username: {m['username']}")
    print(f"OTP to: {m['otp_phone']} (last 4: {m['otp_last4']})")
    print(f"Profile phones: {m['profile_phones'][:3] if m['profile_phones'] else '(none)'}")
    print(f"Date: {m['date']}")
    print("-" * 50)
