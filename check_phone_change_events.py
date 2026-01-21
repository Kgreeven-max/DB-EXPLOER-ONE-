#!/usr/bin/env python3
"""
Check if Change Phone Number events exist and what they look like
"""

from db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# Check if Change Phone Number events exist
print("CHECKING 'Change Phone Number' EVENTS")
print("=" * 80)

cursor.execute("""
    SELECT COUNT(*) FROM fraudmonitor
    WHERE eventCategory = 'Change Phone Number'
""")
count = cursor.fetchone()[0]
print(f"Total 'Change Phone Number' events: {count}\n")

# Show sample
print("Sample events:")
print("-" * 80)
cursor.execute("""
    SELECT userName, eventData, activityDate, muid
    FROM fraudmonitor
    WHERE eventCategory = 'Change Phone Number'
    ORDER BY activityDate DESC
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"User: {row[0]}")
    print(f"Date: {row[2]}")
    print(f"Data: {row[1]}")
    print("-" * 80)

# Also check what event categories exist for phone/contact changes
print("\n\nALL CHANGE-RELATED EVENT CATEGORIES:")
print("=" * 80)
cursor.execute("""
    SELECT DISTINCT eventCategory, COUNT(*) as cnt
    FROM fraudmonitor
    WHERE eventCategory LIKE '%Change%' OR eventCategory LIKE '%Phone%' OR eventCategory LIKE '%Update%'
    GROUP BY eventCategory
    ORDER BY cnt DESC
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} events")

cursor.close()
conn.close()
