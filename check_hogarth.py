#!/usr/bin/env python3
from db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT * FROM fraudmonitor WHERE eventData LIKE '%hogarth%' ORDER BY activityDate DESC")
rows = cursor.fetchall()
cols = [d[0] for d in cursor.description]

print(f"Found {len(rows)} rows\n")
print("Columns:", cols)
print("\n" + "="*100)

for row in rows:
    print(f"\nDate: {row[cols.index('activityDate')]}")
    print(f"Category: {row[cols.index('eventCategory')]}")
    print(f"MUID: {row[cols.index('muid')]}")
    print(f"Username: {row[cols.index('userName')]}")
    print(f"IP: {row[cols.index('ipAddress')]}")
    print(f"EventData: {row[cols.index('eventData')]}")
    print("-"*100)

cursor.close()
conn.close()
