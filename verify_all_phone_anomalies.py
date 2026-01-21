#!/usr/bin/env python3
"""
Manually verify ALL 429 phone anomalies
"""

from db_connection import get_connection
import re
import csv

conn = get_connection()
cursor = conn.cursor()

def normalize_phone(phone):
    """Extract just digits, return last 10"""
    if not phone:
        return None
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) >= 10:
        return digits[-10:]
    return digits if len(digits) > 0 else None

def format_phone(digits):
    """Format 10 digits as xxx-xxx-xxxx"""
    if digits and len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return digits

def phones_match(p1, p2):
    """Check if two phones match (normalized)"""
    n1 = normalize_phone(p1)
    n2 = normalize_phone(p2)
    if not n1 or not n2:
        return False
    return n1 == n2

def digits_different(p1, p2):
    """Count how many digits are different"""
    n1 = normalize_phone(p1)
    n2 = normalize_phone(p2)
    if not n1 or not n2 or len(n1) != len(n2):
        return 10
    return sum(1 for a, b in zip(n1, n2) if a != b)

# Get all anomalies from CSV
print("Loading anomalies from CSV...")
anomalies = []
with open(r'C:\Users\kgreeven\Desktop\DB Exploxer\PHONE_OTP_ANOMALIES.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    anomalies = list(reader)
print(f"Loaded {len(anomalies)} anomalies\n")

# Verify each one
results = {
    'TRUE_MISMATCH': [],      # OTP phone not in profile at all
    'CLOSE_MATCH': [],         # 1-2 digits different (typo?)
    'NO_PROFILE_PHONE': [],    # No phone in profile to compare
    'BAD_DATA': [],            # Profile has invalid phone data
    'ACTUALLY_MATCHES': [],    # False positive - phone IS in profile
}

print("Verifying each anomaly...")
for i, a in enumerate(anomalies):
    if (i + 1) % 50 == 0:
        print(f"  Processed {i+1}/{len(anomalies)}...")

    username = a['Username']
    otp_phone = a['OTP_Sent_To']
    muid = a['MUID']

    # Get customer ID
    cursor.execute("SELECT id FROM customer WHERE UserName = %s", (username,))
    cust = cursor.fetchone()

    if not cust:
        # Try case-insensitive
        cursor.execute("SELECT id FROM customer WHERE LOWER(UserName) = LOWER(%s)", (username,))
        cust = cursor.fetchone()

    profile_phones = []
    category = 'TRUE_MISMATCH'

    if cust:
        cust_id = cust[0]

        # Get ALL communication records
        cursor.execute("""
            SELECT Type_id, Value FROM customercommunication
            WHERE Customer_id = %s
        """, (cust_id,))
        comms = cursor.fetchall()

        for type_id, value in comms:
            if type_id and 'PHONE' in type_id.upper():
                # Check if value looks like a phone (has digits)
                digits = normalize_phone(value)
                if digits and len(digits) >= 7:
                    profile_phones.append(value)
                elif value and '@' in value:
                    # Email stored in phone field = bad data
                    category = 'BAD_DATA'

        # Check if OTP phone matches any profile phone
        for pp in profile_phones:
            if phones_match(otp_phone, pp):
                category = 'ACTUALLY_MATCHES'
                break
            diff = digits_different(otp_phone, pp)
            if diff <= 2:
                category = 'CLOSE_MATCH'

        if not profile_phones and category != 'BAD_DATA':
            category = 'NO_PROFILE_PHONE'
    else:
        category = 'NO_PROFILE_PHONE'

    # Store result
    a['Profile_Phones_Verified'] = '; '.join(profile_phones) if profile_phones else '(none)'
    a['Category'] = category
    results[category].append(a)

cursor.close()
conn.close()

# Print summary
print("\n" + "=" * 80)
print("VERIFICATION RESULTS")
print("=" * 80)
print(f"\nTRUE MISMATCH (OTP to phone NOT in profile):     {len(results['TRUE_MISMATCH'])}")
print(f"CLOSE MATCH (1-2 digits different):               {len(results['CLOSE_MATCH'])}")
print(f"NO PROFILE PHONE (can't verify):                  {len(results['NO_PROFILE_PHONE'])}")
print(f"BAD DATA (email in phone field):                  {len(results['BAD_DATA'])}")
print(f"ACTUALLY MATCHES (false positive):                {len(results['ACTUALLY_MATCHES'])}")

# Show TRUE MISMATCH details
print("\n" + "=" * 80)
print("TRUE MISMATCHES (OTP went to completely different phone):")
print("=" * 80)
for m in results['TRUE_MISMATCH'][:30]:
    print(f"\nUser: {m['Username']} | Member#: {m['Member_Number']}")
    print(f"  Name: {m['First_Name']} {m['Last_Name']}")
    print(f"  OTP Sent To: {m['OTP_Sent_To']}")
    print(f"  Profile Phones: {m['Profile_Phones_Verified']}")
    print(f"  Date: {m['OTP_Date']}")

# Export verified results
output_file = r'C:\Users\kgreeven\Desktop\DB Exploxer\PHONE_OTP_VERIFIED.csv'
all_verified = []
for cat, items in results.items():
    for item in items:
        all_verified.append(item)

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    if all_verified:
        fieldnames = ['Category', 'MUID', 'Member_Number', 'Username', 'First_Name', 'Last_Name',
                     'OTP_Sent_To', 'Profile_Phones_Verified', 'OTP_Date', 'IP_Address']
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_verified)

print(f"\n\nExported verified results to: {output_file}")
