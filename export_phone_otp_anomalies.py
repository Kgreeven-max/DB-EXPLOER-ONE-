#!/usr/bin/env python3
"""
Export all phone OTP anomalies to CSV
"""

from db_connection import get_connection
import re
import csv

conn = get_connection()
cursor = conn.cursor()

def extract_phone_from_text_otp(event_data):
    match = re.search(r'\["text",\s*"([^"]+)",\s*[^,]+,\s*"(\d{3}-\d{3}-\d{4})"', str(event_data))
    if match:
        return match.group(1), match.group(2)  # masked, full
    return None, None

def normalize_phone(phone):
    if not phone:
        return None
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) >= 10:
        return digits[-10:]
    return digits

print("QUERY 1: Pulling OTP text events (1 year)...")
cursor.execute("""
    SELECT f.muid, f.userName, f.eventData, f.activityDate, f.ipAddress, f.masterMembership
    FROM fraudmonitor f
    WHERE f.eventCategory = 'OTP Authentication'
    AND f.eventData LIKE '%"text"%'
    AND f.activityDate > DATE_SUB(NOW(), INTERVAL 365 DAY)
""")
otp_events = cursor.fetchall()
print(f"  Got {len(otp_events)} text OTP events\n")

print("QUERY 2: Pulling profile phone numbers...")
cursor.execute("""
    SELECT c.UserName, cc.Value, c.id
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

print("QUERY 4: Pulling customer names...")
cursor.execute("""
    SELECT UserName, FirstName, LastName, id
    FROM customer
""")
customer_names = {row[0].lower(): (row[1], row[2], row[3]) for row in cursor.fetchall() if row[0]}
print(f"  Got {len(customer_names)} customer records\n")

cursor.close()
conn.close()

# Build profile phone lookup
profile_phones = {}
for username, phone, cust_id in profile_rows:
    if username and phone:
        key = username.lower()
        if key not in profile_phones:
            profile_phones[key] = []
        normalized = normalize_phone(phone)
        if normalized and len(normalized) == 10:
            formatted = f"{normalized[:3]}-{normalized[3:6]}-{normalized[6:]}"
            if formatted not in profile_phones[key]:
                profile_phones[key].append(formatted)

# Process OTP events and find anomalies
print("Processing and finding anomalies...")
anomalies = []

otp_cases = {}
for muid, username, event_data, activity_date, ip_address, member_num in otp_events:
    masked_phone, full_phone = extract_phone_from_text_otp(event_data)
    if full_phone and muid:
        key = (muid, full_phone)
        if key not in otp_cases:
            otp_cases[key] = {
                'muid': muid,
                'username': username,
                'member_number': member_num,
                'otp_phone_masked': masked_phone,
                'otp_phone_full': full_phone,
                'date': activity_date,
                'ip_address': ip_address,
                'event_data': event_data
            }

for (muid, otp_phone), case in otp_cases.items():
    username = case['username']
    otp_normalized = normalize_phone(otp_phone)

    # Get profile phones
    user_phones = []
    if username:
        user_phones = profile_phones.get(username.lower(), [])

    # Normalize for comparison
    user_phones_normalized = [normalize_phone(p) for p in user_phones]

    # Check if OTP phone matches any profile phone
    if otp_normalized not in user_phones_normalized:
        # Check if has phone change event
        if muid not in phone_change_muids:
            # Get customer name
            first_name, last_name, cust_id = '', '', ''
            if username and username.lower() in customer_names:
                first_name, last_name, cust_id = customer_names[username.lower()]

            anomalies.append({
                'MUID': case['muid'],
                'Member_Number': case['member_number'] or '',
                'Username': case['username'] or '',
                'First_Name': first_name or '',
                'Last_Name': last_name or '',
                'OTP_Sent_To': case['otp_phone_full'],
                'OTP_Masked': case['otp_phone_masked'],
                'Profile_Phones': '; '.join(user_phones) if user_phones else '(none in profile)',
                'Phone_Change_Event': 'NO',
                'OTP_Date': str(case['date']),
                'IP_Address': case['ip_address'] or '',
                'Raw_Event_Data': str(case['event_data'])[:200]
            })

print(f"\nFound {len(anomalies)} anomalies\n")

# Export to CSV
output_file = r'C:\Users\kgreeven\Desktop\DB Exploxer\PHONE_OTP_ANOMALIES.csv'
print(f"Exporting to {output_file}...")

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    if anomalies:
        writer = csv.DictWriter(f, fieldnames=anomalies[0].keys())
        writer.writeheader()
        writer.writerows(anomalies)

print(f"\nDONE! Exported {len(anomalies)} records to:")
print(f"  {output_file}")
