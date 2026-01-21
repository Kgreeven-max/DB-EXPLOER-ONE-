#!/usr/bin/env python3
"""
Find cgregory profile and emails
"""

from db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# Search for cgregory by username
print("Searching for cgregory/CMG1945 in customer table...")
print("-" * 60)
cursor.execute("""
    SELECT id, UserName, FirstName, LastName
    FROM customer
    WHERE UserName IN ('cgregory', 'CMG1945', 'cmg1945')
""")
results = cursor.fetchall()
print(f"Found {len(results)} records:")
for r in results:
    customer_id = r[0]
    print(f"  id: {customer_id}")
    print(f"  UserName: {r[1]}")
    print(f"  Name: {r[2]} {r[3]}")

    # Now get their emails from customercommunication
    print(f"  Emails from customercommunication:")
    cursor.execute("""
        SELECT Value, Type_id, isPrimary, Description
        FROM customercommunication
        WHERE Customer_id = %s
        AND (Value LIKE '%%@%%')
    """, (customer_id,))
    emails = cursor.fetchall()
    if not emails:
        print("    (none found)")
    for e in emails:
        print(f"    - {e[0]} (Type: {e[1]}, Primary: {e[2]})")
    print()

# Also try searching directly in customercommunication for gmail
print("\n")
print("Direct search for CGREGORY619 in customercommunication...")
print("-" * 60)
cursor.execute("""
    SELECT Customer_id, Value, Type_id, isPrimary
    FROM customercommunication
    WHERE Value LIKE '%CGREGORY619%' OR Value LIKE '%cgregory619%'
""")
results = cursor.fetchall()
print(f"Found {len(results)} records:")
for r in results:
    print(f"  Customer_id: {r[0]}")
    print(f"  Email: {r[1]}")
    print(f"  Type: {r[2]}, Primary: {r[3]}")
    print()

cursor.close()
conn.close()
