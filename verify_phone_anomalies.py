#!/usr/bin/env python3
"""
Verify phone anomalies - check a sample manually
"""

from db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# Sample cases to verify
test_cases = [
    ('florest1', '619-249-3212'),
    ('Katrine', '619-218-5471'),
    ('Reyes760', '760-822-0861'),
    ('pdthomps', '760-419-9435'),
    ('LouisA100X', '760-291-7861'),
]

print("VERIFYING SAMPLE CASES")
print("=" * 80)

for username, otp_phone in test_cases:
    print(f"\n{'='*80}")
    print(f"USERNAME: {username}")
    print(f"OTP SENT TO: {otp_phone}")
    print("-" * 80)

    # Get customer record
    cursor.execute("""
        SELECT id, FirstName, LastName, UserName
        FROM customer
        WHERE UserName = %s
    """, (username,))
    cust = cursor.fetchone()

    if cust:
        cust_id = cust[0]
        print(f"Customer: {cust[1]} {cust[2]} (ID: {cust_id})")

        # Get ALL communication records for this customer
        cursor.execute("""
            SELECT Type_id, Value, Description, isPrimary
            FROM customercommunication
            WHERE Customer_id = %s
        """, (cust_id,))
        comms = cursor.fetchall()

        print(f"\nALL customercommunication records:")
        for c in comms:
            print(f"  Type: {c[0]:<30} Value: {c[1]:<25} Desc: {c[2]} Primary: {c[3]}")

        # Check if OTP phone is anywhere in the records
        otp_digits = ''.join(c for c in otp_phone if c.isdigit())
        found = False
        for c in comms:
            if c[1]:
                val_digits = ''.join(ch for ch in str(c[1]) if ch.isdigit())
                if otp_digits in val_digits or val_digits in otp_digits:
                    found = True
                    print(f"\n  *** FOUND MATCH: {c[1]} ***")

        if not found:
            print(f"\n  *** OTP PHONE {otp_phone} NOT FOUND IN ANY RECORD ***")
    else:
        print(f"  NO CUSTOMER RECORD FOUND")

    # Check for phone change events
    cursor.execute("""
        SELECT eventCategory, eventData, activityDate
        FROM fraudmonitor
        WHERE userName = %s
        AND eventCategory = 'Change Phone Number'
        ORDER BY activityDate DESC
        LIMIT 3
    """, (username,))
    changes = cursor.fetchall()
    print(f"\nPhone change events:")
    if not changes:
        print("  (none)")
    for ch in changes:
        print(f"  {ch[2]} | {ch[1][:100]}...")

cursor.close()
conn.close()
