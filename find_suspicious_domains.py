#!/usr/bin/env python3
"""
Find all suspicious/Russian domains in active use
"""

from db_connection import get_connection
import re
from collections import defaultdict

conn = get_connection()
cursor = conn.cursor()

# Suspicious patterns
SUSPICIOUS = [
    '@yandex', '.ru"', '.xyz"', '.top"', '.online"',
    'mailclone', 'ibande', 'zenmail', '.su"'
]

print("Searching for suspicious domains in fraudmonitor (last 1 year)...\n")

# Build query
conditions = " OR ".join([f"eventData LIKE '%{p}%'" for p in SUSPICIOUS])
query = f"""
SELECT muid, userName, eventCategory, eventData, activityDate
FROM fraudmonitor
WHERE ({conditions})
AND activityDate > DATE_SUB(NOW(), INTERVAL 365 DAY)
ORDER BY activityDate DESC
"""

cursor.execute(query)
rows = cursor.fetchall()
print(f"Found {len(rows)} events\n")

# Extract emails and group by domain
def extract_emails(text):
    return re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', str(text))

domain_users = defaultdict(set)
domain_events = defaultdict(list)

for muid, username, category, event_data, activity_date in rows:
    emails = extract_emails(event_data)
    for email in emails:
        domain = email.split('@')[1].lower()
        # Filter to suspicious only
        if any(s.replace('"','').replace('@','') in domain for s in SUSPICIOUS):
            domain_users[domain].add(username or muid)
            if len(domain_events[domain]) < 5:  # Keep 5 examples per domain
                domain_events[domain].append({
                    'email': email,
                    'user': username,
                    'muid': muid,
                    'category': category,
                    'date': activity_date
                })

cursor.close()
conn.close()

# Print results
print("=" * 80)
print("SUSPICIOUS DOMAINS FOUND (grouped by domain)")
print("=" * 80)

for domain in sorted(domain_users.keys()):
    users = domain_users[domain]
    print(f"\n{domain}")
    print(f"  Users: {len(users)}")
    print(f"  Examples:")
    for e in domain_events[domain]:
        print(f"    - {e['email']} | {e['user']} | {e['category']} | {e['date']}")
