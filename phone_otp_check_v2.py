#!/usr/bin/env python3
"""
Check phone OTP anomalies - using correct format ["text", ...]
"""

from db_connection import get_connection
import re

conn = get_connection()
cursor = conn.cursor()

def extract_phone_from_text_otp(event_data):
    # Format: ["text", "xxx-xxx-1234", null, "619-555-1234", "success"]
    # The 4th element is the full phone number
    match = re.search(r'\["text",\s*"[^"]+",\s*[^,]+,\s*"(\d{3}-\d{3}-\d{4})"', str(event_data))
    if match:
        return match.group(1)
    return None

def normalize_phone(phone):
    if not phone:
        return None
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) >= 10:
        return digits[-10:]
    return digits

print("QUERY 1: Pulling OTP text events (1 year)...")
cursor.execute("""
    SELECT muid, userName, eventData, activityDate
    FROM fraudmonitor
    WHERE eventCategory = 'OTP Authentication'
    AND eventData LIKE '%"text"%'
    AND activityDate > DATE_SUB(NOW(), INTERVAL 365 DAY)
""")
otp_events = cursor.fetchall()
print(f"  Got {len(otp_events)} text OTP events\n")

print("QUERY 2: Pulling profile phone numbers...")
cursor.execute("""
    SELECT c.UserName, cc.Value
    FROM customer c
    JOIN customercommunication cc ON c.id = cc.Customer_id
    WHERE cc.Type_id LIKE '%PHONE%' OR cc.Value REGEXP '^[0-9]{3}-[0-9]{3}-[0-9]{4}$'
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

# Build profile phone lookup
profile_phones = {}
for username, phone in profile_rows:
    if username and phone:
        key = username.lower()
        if key not in profile_phones:
            profile_phones[key] = set()
        normalized = normalize_phone(phone)
        if normalized and len(normalized) == 10:
            profile_phones[key].add(normalized)

# Process OTP events
print("Processing text OTP events...")
otp_cases = {}
for muid, username, event_data, activity_date in otp_events:
    otp_phone = extract_phone_from_text_otp(event_data)
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
    otp_normalized = normalize_phone(otp_phone)

    # Get profile phones
    user_phones = set()
    if username:
        user_phones = profile_phones.get(username.lower(), set())

    # Check if OTP phone matches any profile phone
    if otp_normalized not in user_phones:
        case['profile_phones'] = [f"{p[:3]}-{p[3:6]}-{p[6:]}" for p in list(user_phones)[:5]]
        case['has_phone_change'] = muid in phone_change_muids
        mismatches.append(case)

# Filter for anomalies (no phone change event)
anomalies = [m for m in mismatches if not m['has_phone_change']]

print(f"{'='*70}")
print(f"TOTAL PHONE MISMATCHES: {len(mismatches)}")
print(f"WITH PHONE CHANGE EVENT: {len(mismatches) - len(anomalies)}")
print(f"WITHOUT PHONE CHANGE EVENT (anomaly): {len(anomalies)}")
print("=" * 70)

print("\nFirst 20 anomalies:\n")
for m in anomalies[:20]:
    print(f"MUID: {m['muid']}")
    print(f"Username: {m['username']}")
    print(f"OTP to: {m['otp_phone']}")
    print(f"Profile phones: {m['profile_phones'] if m['profile_phones'] else '(none)'}")
    print(f"Date: {m['date']}")
    print("-" * 50)
