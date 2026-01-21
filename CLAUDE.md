# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DB Explorer is a Python-based toolkit for querying and analyzing Cal Coast Credit Union's DBXDB MySQL database. The database contains digital banking activity including fraud monitoring, authentication logs, and alert history.

## Database Connection

Use `db_connection.py` for all database queries:
```python
from db_connection import get_connection
conn = get_connection()
cursor = conn.cursor()
# ... execute queries
cursor.close()
conn.close()
```

Database: `dbxdb` on `infinity-9ix.calcoastcu.org:3306`

## Key Database Tables

- **fraudmonitor** (~17.8M rows) - Main activity tracking: logins, credential changes, transactions, OTP events
- **alerthistory** (~16M rows) - Alert delivery records (email, SMS, push notifications)

### Common Query Patterns

Query fraudmonitor by user:
```sql
SELECT activityDate, eventCategory, eventData, ipAddress, platform
FROM fraudmonitor
WHERE userName = 'username'
ORDER BY activityDate DESC
```

Query alerthistory by subject:
```sql
SELECT createdts, Customer_Id, Subject, ChannelId, Status
FROM alerthistory
WHERE Subject LIKE '%Password%'
ORDER BY createdts DESC
```

## Running Scripts

Use `py` (Windows Python launcher) instead of `python`:
```bash
py fraud_analysis_csv copy 2.py
py -c "from db_connection import get_connection; ..."
```

## Important Notes

- Password contains `!` character - avoid inline bash commands; use Python scripts instead
- Large table queries may timeout - use `LIMIT` or date filters
- `alerthistory` uses `Customer_Id` not `userName` for user identification
- P2P tracking stopped working accurately after January 23, 2025 (SSO integration change)
- LoginSuccessful/LoginFailure events added October 28, 2025

## Documentation

`DBXDB_Documentation.md` contains comprehensive database documentation for auditors and legal review.
