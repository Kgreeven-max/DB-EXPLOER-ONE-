#!/usr/bin/env python3
"""
OTP Impact Analysis - December 2025
Analyzes OTP delivery methods (email vs SMS) to assess impact of removing email OTP

Data formats:
- OLD FORMAT: ["user_email", "xxx-xxx-phone", "status"] - OTP sent to PHONE (text)
- NEW FORMAT: ["method", "contact", "fallback", "full_contact", "status"]
"""

from db_connection import get_connection
import json

def determine_delivery_method(event_data_str):
    """Determine delivery method from eventData JSON string"""
    if not event_data_str:
        return 'unknown'

    try:
        data = json.loads(event_data_str)
        if not data or len(data) == 0:
            return 'unknown'

        first_elem = data[0]

        # New format: first element is delivery method
        if first_elem in ('text', 'email', 'call', 'voice'):
            return first_elem

        # Old format: check if first element is email and second is phone
        if first_elem and '@' in str(first_elem):
            # Email in position 0, check if phone in position 1
            if len(data) > 1 and data[1] and 'xxx-xxx-' in str(data[1]):
                return 'text'  # OTP was sent to the phone, not email
            return 'unknown'

        # Old format: null in position 0, phone in position 1
        if first_elem is None and len(data) > 1:
            if data[1] and 'xxx-xxx-' in str(data[1]):
                return 'text'
            return 'unknown'

        return 'other'
    except (json.JSONDecodeError, TypeError, IndexError):
        return 'unknown'


def analyze_otp_december():
    conn = get_connection()
    cursor = conn.cursor()

    print("Fetching OTP data for December 2025...")

    # Fetch all OTP events with eventData and userName
    sql = """
    SELECT eventData, userName
    FROM fraudmonitor
    WHERE eventCategory = 'OTP Authentication'
      AND activityDate >= '2025-12-01'
      AND activityDate < '2026-01-01'
    """

    cursor.execute(sql)

    # Process in Python
    counts = {'text': 0, 'email': 0, 'call': 0, 'voice': 0, 'unknown': 0, 'other': 0}
    users = {'text': set(), 'email': set(), 'call': set(), 'voice': set(), 'unknown': set(), 'other': set()}

    total = 0
    for row in cursor:
        event_data, username = row
        method = determine_delivery_method(event_data)
        counts[method] += 1
        if username:
            users[method].add(username)
        total += 1

        if total % 50000 == 0:
            print(f"  Processed {total:,} records...")

    cursor.close()
    conn.close()

    print(f"\nTotal records processed: {total:,}")

    print("\n" + "="*60)
    print("OTP DELIVERY METHOD ANALYSIS - DECEMBER 2025")
    print("="*60)
    print(f"\n{'Delivery Method':<20} {'Total OTPs':>15} {'Unique Users':>15}")
    print("-"*50)

    for method in ['text', 'email', 'call', 'voice', 'unknown', 'other']:
        if counts[method] > 0:
            print(f"{method:<20} {counts[method]:>15,} {len(users[method]):>15,}")

    print("-"*50)
    print(f"{'TOTAL':<20} {total:>15,}")

    # Calculate percentages
    email_otps = counts['email']
    email_users = len(users['email'])
    text_otps = counts['text']
    text_users = len(users['text'])
    call_otps = counts['call'] + counts['voice']
    call_users = len(users['call'] | users['voice'])

    if total > 0:
        email_pct = (email_otps / total) * 100
        text_pct = (text_otps / total) * 100
        call_pct = (call_otps / total) * 100

        print("\n" + "="*60)
        print("IMPACT SUMMARY")
        print("="*60)
        print(f"\nText OTP:   {text_otps:,} passcodes ({text_pct:.1f}%) from {text_users:,} users")
        print(f"Email OTP:  {email_otps:,} passcodes ({email_pct:.1f}%) from {email_users:,} users")
        print(f"Call OTP:   {call_otps:,} passcodes ({call_pct:.1f}%) from {call_users:,} users")

        print("\n" + "-"*60)
        print("WRITE-UP FOR STAKEHOLDERS:")
        print("-"*60)
        print(f"""
In December 2025, Cal Coast processed {total:,} OTP authentication events.

TEXT/SMS OTP USAGE:
- {text_otps:,} passcodes sent via text message ({text_pct:.1f}% of total)
- {text_users:,} unique members used text OTP

EMAIL OTP USAGE:
- {email_otps:,} passcodes sent via email ({email_pct:.1f}% of total)
- {email_users:,} unique members used email OTP

VOICE CALL OTP USAGE:
- {call_otps:,} passcodes sent via voice call ({call_pct:.1f}% of total)
- {call_users:,} unique members used voice OTP

IMPACT OF REMOVING EMAIL OTP:
Removing email as an OTP delivery option would affect {email_users:,} members
who used email for authentication in December. These members would need to
switch to text message (SMS) or voice call for OTP delivery.
""")


if __name__ == "__main__":
    analyze_otp_december()
