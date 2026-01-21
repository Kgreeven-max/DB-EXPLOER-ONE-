#!/usr/bin/env python3
"""
Check how customer table links to customercommunication
"""

from db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# Check customer table schema
print("customer table columns:")
print("-" * 60)
cursor.execute("DESCRIBE customer")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n")

# Search for cgregory's customer record
print("Searching for cgregory in customer table...")
print("-" * 60)
cursor.execute("""
    SELECT id, UserName, FirstName, LastName
    FROM customer
    WHERE UserName LIKE '%gregory%' OR UserName LIKE '%cmg1945%'
    LIMIT 5
""")
results = cursor.fetchall()
print(f"Found {len(results)} records:")
for r in results:
    print(f"  id: {r[0]}")
    print(f"  UserName: {r[1]}")
    print(f"  Name: {r[2]} {r[3]}")
    print()

# Also try searching by member number
print("\nSearching by userName in fraudmonitor for cgregory...")
cursor.execute("""
    SELECT DISTINCT muid, userName
    FROM fraudmonitor
    WHERE muid = '00638242923564062860'
    AND userName IS NOT NULL AND userName != ''
    LIMIT 5
""")
results = cursor.fetchall()
for r in results:
    print(f"  MUID: {r[0]}, userName: {r[1]}")

cursor.close()
conn.close()
