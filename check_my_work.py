#!/usr/bin/env python3
"""
Verify my work - spot check several cases
"""

from db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# Pick cases from each category to verify
test_cases = [
    # TRUE_MISMATCH cases
    ('Katrine', '619-218-5471', 'TRUE_MISMATCH'),
    ('pdthomps', '760-419-9435', 'TRUE_MISMATCH'),
    ('LouisA100X', '760-291-7861', 'TRUE_MISMATCH'),
    # CLOSE_MATCH case (should be 1-2 digits off)
    ('Reyes760', '760-822-0861', 'CLOSE_MATCH'),
    # NO_PROFILE_PHONE case
    ('florest1', '619-249-3212', 'NO_PROFILE_PHONE'),
]

print("CHECKING MY WORK - SPOT VERIFICATION")
print("=" * 80)

for username, otp_phone, expected_category in test_cases:
    print(f"\n{'='*80}")
    print(f"CASE: {username} | OTP to: {otp_phone}")
    print(f"EXPECTED CATEGORY: {expected_category}")
    print("-" * 80)

    # Get customer
    cursor.execute("""
        SELECT id, FirstName, LastName FROM customer
        WHERE UserName = %s OR LOWER(UserName) = LOWER(%s)
    """, (username, username))
    cust = cursor.fetchone()

    if cust:
        print(f"Customer: {cust[1]} {cust[2]} (ID: {cust[0]})")

        # Get ALL phone records
        cursor.execute("""
            SELECT Type_id, Value, Description
            FROM customercommunication
            WHERE Customer_id = %s AND Type_id LIKE '%%PHONE%%'
        """, (cust[0],))
        phones = cursor.fetchall()

        print(f"\nProfile phone records:")
        if not phones:
            print("  (NONE FOUND)")
        for p in phones:
            print(f"  Type: {p[0]}")
            print(f"  Value: {p[1]}")
            print(f"  Desc: {p[2]}")

            # Check if it matches OTP phone
            otp_digits = ''.join(c for c in otp_phone if c.isdigit())
            val_digits = ''.join(c for c in str(p[1]) if c.isdigit())[-10:] if p[1] else ''

            if otp_digits == val_digits:
                print(f"  *** MATCHES OTP! ***")
            elif len(otp_digits) == 10 and len(val_digits) == 10:
                diff = sum(1 for a,b in zip(otp_digits, val_digits) if a != b)
                print(f"  Digits different from OTP: {diff}")
    else:
        print("  NO CUSTOMER FOUND")

    # Check for phone change events
    cursor.execute("""
        SELECT eventCategory, eventData, activityDate
        FROM fraudmonitor
        WHERE userName = %s AND eventCategory = 'Change Phone Number'
        ORDER BY activityDate DESC LIMIT 3
    """, (username,))
    changes = cursor.fetchall()
    print(f"\nPhone change events in fraudmonitor:")
    if not changes:
        print("  (NONE)")
    for ch in changes:
        print(f"  {ch[2]}: {ch[1][:80]}...")

    # Verify the OTP event exists
    cursor.execute("""
        SELECT eventData, activityDate, ipAddress
        FROM fraudmonitor
        WHERE userName = %s AND eventCategory = 'OTP Authentication'
        AND eventData LIKE %s
        ORDER BY activityDate DESC LIMIT 1
    """, (username, f'%{otp_phone}%'))
    otp = cursor.fetchone()
    print(f"\nOTP event found:")
    if otp:
        print(f"  Date: {otp[1]}")
        print(f"  IP: {otp[2]}")
        print(f"  Data: {otp[0][:100]}...")
    else:
        print("  (NOT FOUND - checking by phone only)")
        cursor.execute("""
            SELECT userName, eventData, activityDate
            FROM fraudmonitor
            WHERE eventCategory = 'OTP Authentication'
            AND eventData LIKE %s
            ORDER BY activityDate DESC LIMIT 1
        """, (f'%{otp_phone}%',))
        otp2 = cursor.fetchone()
        if otp2:
            print(f"  Found under username: {otp2[0]}")
            print(f"  Date: {otp2[2]}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
