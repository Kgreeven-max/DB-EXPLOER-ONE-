#!/usr/bin/env python3
"""
Check what OTP event formats look like
"""

from db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# Sample OTP events to see formats
print("Sample OTP events (looking at eventData formats):\n")
cursor.execute("""
    SELECT eventData, activityDate
    FROM fraudmonitor
    WHERE eventCategory = 'OTP Authentication'
    AND activityDate > DATE_SUB(NOW(), INTERVAL 30 DAY)
    ORDER BY activityDate DESC
    LIMIT 20
""")

for row in cursor.fetchall():
    print(f"{row[1]} | {row[0][:150]}...")
    print("-" * 100)

cursor.close()
conn.close()
