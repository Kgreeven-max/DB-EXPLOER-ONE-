#!/usr/bin/env python3
"""
Verify phone anomalies - BULK SQL pulls, Python analysis
"""

from db_connection import get_connection
import re
import csv

conn = get_connection()
cursor = conn.cursor()

def normalize_phone(phone):
    if not phone:
        return None
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) >= 10:
        return digits[-10:]
    return digits if len(digits) >= 7 else None

def format_phone(digits):
    if digits and len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return digits

def digits_different(p1, p2):
    n1 = normalize_phone(p1)
    n2 = normalize_phone(p2)
    if not n1 or not n2 or len(n1) != len(n2):
        return 10
    return sum(1 for a, b in zip(n1, n2) if a != b)

# BULK QUERY 1: All customers
print("QUERY 1: Pulling all customers...")
cursor.execute("SELECT id, UserName, FirstName, LastName FROM customer")
customer_rows = cursor.fetchall()
print(f"  Got {len(customer_rows)} customers")

# Build lookup
customers = {}
for cid, uname, fname, lname in customer_rows:
    if uname:
        customers[uname.lower()] = {'id': cid, 'first': fname, 'last': lname}

# BULK QUERY 2: All phone records from customercommunication
print("QUERY 2: Pulling all phone records...")
cursor.execute("""
    SELECT Customer_id, Type_id, Value
    FROM customercommunication
    WHERE Type_id LIKE '%PHONE%'
""")
phone_rows = cursor.fetchall()
print(f"  Got {len(phone_rows)} phone records")

# Build lookup by customer_id
profile_phones = {}
for cust_id, type_id, value in phone_rows:
    if cust_id not in profile_phones:
        profile_phones[cust_id] = []
    profile_phones[cust_id].append({'type': type_id, 'value': value})

cursor.close()
conn.close()

print("\nLoading anomalies from CSV...")
anomalies = []
with open(r'C:\Users\kgreeven\Desktop\DB Exploxer\PHONE_OTP_ANOMALIES.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    anomalies = list(reader)
print(f"Loaded {len(anomalies)} anomalies\n")

# PYTHON ANALYSIS
print("Analyzing in Python...")
results = {
    'TRUE_MISMATCH': [],
    'CLOSE_MATCH': [],
    'NO_PROFILE_PHONE': [],
    'BAD_DATA': [],
    'ACTUALLY_MATCHES': [],
}

for a in anomalies:
    username = a['Username']
    otp_phone = a['OTP_Sent_To']
    otp_norm = normalize_phone(otp_phone)

    # Find customer
    cust = customers.get(username.lower()) if username else None

    category = 'TRUE_MISMATCH'
    verified_phones = []

    if cust:
        cust_id = cust['id']
        phones = profile_phones.get(cust_id, [])

        for p in phones:
            val = p['value']
            if val and '@' in val:
                category = 'BAD_DATA'
                continue

            norm = normalize_phone(val)
            if norm and len(norm) >= 7:
                verified_phones.append(format_phone(norm) if len(norm) == 10 else norm)

                # Check match
                if otp_norm and norm == otp_norm:
                    category = 'ACTUALLY_MATCHES'
                elif otp_norm and digits_different(otp_phone, val) <= 2:
                    if category not in ['ACTUALLY_MATCHES']:
                        category = 'CLOSE_MATCH'

        if not verified_phones and category not in ['BAD_DATA']:
            category = 'NO_PROFILE_PHONE'
    else:
        category = 'NO_PROFILE_PHONE'

    a['Profile_Phones_Verified'] = '; '.join(verified_phones) if verified_phones else '(none)'
    a['Category'] = category
    results[category].append(a)

# RESULTS
print("\n" + "=" * 80)
print("VERIFICATION RESULTS")
print("=" * 80)
print(f"\nTRUE MISMATCH (completely different phone):  {len(results['TRUE_MISMATCH'])}")
print(f"CLOSE MATCH (1-2 digits off):                {len(results['CLOSE_MATCH'])}")
print(f"NO PROFILE PHONE (can't verify):             {len(results['NO_PROFILE_PHONE'])}")
print(f"BAD DATA (email in phone field):             {len(results['BAD_DATA'])}")
print(f"ACTUALLY MATCHES (false positive):           {len(results['ACTUALLY_MATCHES'])}")

# Show TRUE MISMATCHES
print("\n" + "=" * 80)
print("TRUE MISMATCHES (first 30):")
print("=" * 80)
for m in results['TRUE_MISMATCH'][:30]:
    print(f"\nUser: {m['Username']} | {m['First_Name']} {m['Last_Name']}")
    print(f"  OTP To: {m['OTP_Sent_To']}")
    print(f"  Profile: {m['Profile_Phones_Verified']}")
    print(f"  Date: {m['OTP_Date']}")

# Export
output = r'C:\Users\kgreeven\Desktop\DB Exploxer\PHONE_OTP_VERIFIED.csv'
all_items = []
for cat, items in results.items():
    all_items.extend(items)

with open(output, 'w', newline='', encoding='utf-8') as f:
    fields = ['Category', 'MUID', 'Member_Number', 'Username', 'First_Name', 'Last_Name',
              'OTP_Sent_To', 'OTP_Masked', 'Profile_Phones_Verified', 'Phone_Change_Event',
              'OTP_Date', 'IP_Address', 'Raw_Event_Data']
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(all_items)

print(f"\n\nExported to: {output}")
