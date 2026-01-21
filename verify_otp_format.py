#!/usr/bin/env python3
"""Verify OTP data format interpretation"""

from db_connection import get_connection
import json

conn = get_connection()
cursor = conn.cursor()

print('=== SAMPLE OTP EVENT DATA FORMATS ===\n')

# Sample where first element is an email address (old format)
cursor.execute("""
    SELECT eventData, userName, platform
    FROM fraudmonitor
    WHERE eventCategory = 'OTP Authentication'
    AND activityDate >= '2025-12-01' AND activityDate < '2026-01-01'
    AND JSON_UNQUOTE(JSON_EXTRACT(eventData, '$[0]')) LIKE '%@%'
    LIMIT 5
""")
print('OLD FORMAT (email in position 0):')
for row in cursor.fetchall():
    print(f'  User: {row[1]}, Platform: {row[2]}')
    print(f'  Data: {row[0]}')
    print()

# Sample where first element is 'text'
cursor.execute("""
    SELECT eventData, userName, platform
    FROM fraudmonitor
    WHERE eventCategory = 'OTP Authentication'
    AND activityDate >= '2025-12-01' AND activityDate < '2026-01-01'
    AND JSON_UNQUOTE(JSON_EXTRACT(eventData, '$[0]')) = 'text'
    LIMIT 5
""")
print('NEW FORMAT (text):')
for row in cursor.fetchall():
    print(f'  User: {row[1]}, Platform: {row[2]}')
    print(f'  Data: {row[0]}')
    print()

# Sample where first element is 'email' explicitly
cursor.execute("""
    SELECT eventData, userName, platform
    FROM fraudmonitor
    WHERE eventCategory = 'OTP Authentication'
    AND activityDate >= '2025-12-01' AND activityDate < '2026-01-01'
    AND JSON_UNQUOTE(JSON_EXTRACT(eventData, '$[0]')) = 'email'
    LIMIT 5
""")
print('NEW FORMAT (email explicitly):')
for row in cursor.fetchall():
    print(f'  User: {row[1]}, Platform: {row[2]}')
    print(f'  Data: {row[0]}')
    print()

# Check the alerthistory for OTP delivery details
print('=== CHECKING ALERTHISTORY FOR OTP PATTERNS ===\n')
cursor.execute("""
    SELECT Subject, ChannelId, COUNT(*) as cnt
    FROM alerthistory
    WHERE Subject LIKE '%code%' OR Subject LIKE '%OTP%' OR Subject LIKE '%passcode%'
    AND createdts >= '2025-12-01' AND createdts < '2026-01-01'
    GROUP BY Subject, ChannelId
    ORDER BY cnt DESC
    LIMIT 20
""")
for row in cursor.fetchall():
    print(f'  {row[0]} via {row[1]}: {row[2]:,}')

cursor.close()
conn.close()
