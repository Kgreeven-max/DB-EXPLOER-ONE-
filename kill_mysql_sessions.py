#!/usr/bin/env python3
"""
Show and kill MySQL sessions for current user
"""

from db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()

# Show current processes
print("Current MySQL processes for Kendall.Greeven:")
print("=" * 80)
cursor.execute("SHOW PROCESSLIST")
processes = cursor.fetchall()

my_processes = []
for p in processes:
    if 'Kendall' in str(p[1]):
        print(f"ID: {p[0]} | User: {p[1]} | DB: {p[3]} | Command: {p[4]} | Time: {p[5]}s | State: {p[6]}")
        if p[4] != 'Sleep' or p[5] > 60:  # Active or old sleep connections
            my_processes.append(p[0])

print(f"\nFound {len(my_processes)} active/old connections")

# Kill old ones (except current)
current_id = conn.thread_id()
print(f"Current connection ID: {current_id}")

killed = 0
for pid in my_processes:
    if pid != current_id:
        try:
            cursor.execute(f"KILL {pid}")
            print(f"Killed connection {pid}")
            killed += 1
        except Exception as e:
            print(f"Could not kill {pid}: {e}")

print(f"\nKilled {killed} connections")

cursor.close()
conn.close()
