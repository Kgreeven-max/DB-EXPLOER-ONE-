# OTP Anomaly Investigation Findings

**Investigator:** Kendall Greeven
**Date:** January 12, 2026
**Database:** dbxdb (fraudmonitor, customer, customercommunication tables)

---

## Executive Summary

Investigation identified **2 cases** where OTP codes were sent to email addresses that:
1. Do NOT exist in the member's profile
2. Have NO corresponding "Change Primary email" or "Change Alternate email" event logged in fraudmonitor

This is anomalous because normally when an email receives OTPs, it should either:
- Already exist in the member's profile, OR
- Have been added via an email change event (which gets logged)

---

## Cases Identified

### Case 1: cgregory (MUID: 00638242923564062860)

| Field | Value |
|-------|-------|
| Member | CATRINA GREGORY |
| Username | cgregory / CMG1945 |
| MUID | 00638242923564062860 |
| Profile Email | CGREGORY619@GMAIL.COM |
| OTP Sent To | joeynaj@ibande.xyz |
| OTP Dates | Jan 6, 2026 (02:42 AM) and Jan 7, 2026 (03:00 AM) |
| Email Change Events | **NONE** |

**Observations:**
- Email `joeynaj@ibande.xyz` appears ONLY in the 2 OTP Authentication events
- No "Change Primary email" or "Change Alternate email" event exists for this member
- The domain `ibande.xyz` is an unusual TLD (.xyz)
- OTPs occurred during overnight hours (2-3 AM PST)
- IP address 15.181.21.112 associated with these events is an AWS datacenter IP

---

### Case 2: cpclements (MUID: 00638242921524906864)

| Field | Value |
|-------|-------|
| Member | CHRISTOPHER CLEMENTS |
| Username | cpclements / cpclements777 |
| MUID | 00638242921524906864 |
| Profile Email | SUZY.CLEMENTS20@GMAIL.COM |
| OTP Sent To | meekhh@mailclone2023.top |
| OTP Date | Dec 17, 2025 (09:31 AM) |
| Email Change Events | **NONE** |

**Observations:**
- Email `meekhh@mailclone2023.top` appears only in OTP Authentication event
- No "Change Primary email" or "Change Alternate email" event exists
- The domain `mailclone2023.top` is suspicious (.top TLD, contains "mailclone")
- No record of how this email was associated with the account

---

## Investigation Methodology

### Queries Used

**1. Find OTP events to suspicious domains:**
```sql
SELECT muid, userName, eventCategory, eventData, activityDate
FROM fraudmonitor
WHERE eventCategory = 'OTP Authentication'
AND eventData LIKE '%"email"%'
AND (eventData LIKE '%.xyz%' OR eventData LIKE '%.top%'
     OR eventData LIKE '%mailclone%' OR eventData LIKE '%ibande%')
ORDER BY activityDate DESC;
```

**2. Check for email change events:**
```sql
SELECT eventCategory, activityDate, eventData
FROM fraudmonitor
WHERE muid = '00638242923564062860'
AND eventCategory IN ('Change Primary email', 'Change Alternate email')
ORDER BY activityDate DESC;
```

**3. Get profile email from customer/customercommunication:**
```sql
SELECT c.UserName, cc.Value as ProfileEmail
FROM customer c
JOIN customercommunication cc ON c.id = cc.Customer_id
WHERE cc.Value LIKE '%@%'
AND c.UserName = 'cgregory';
```

**4. Compare to normal behavior (hogarth example):**
```sql
SELECT activityDate, eventCategory, eventData
FROM fraudmonitor
WHERE eventData LIKE '%hogarth%'
ORDER BY activityDate DESC;
```

---

## Comparison: Normal vs Anomalous Behavior

### Normal Behavior (jmhogarth example)
| Date | Event | Data |
|------|-------|------|
| Feb 24, 2025 | **Change Primary email** | mike@hogarth.org → "revised" |
| Oct-Jan | OTP Authentication | mxke@hogarth.org (masked) |

- Email change WAS logged before OTPs were sent to that address
- This is expected behavior

### Anomalous Behavior (cgregory)
| Date | Event | Data |
|------|-------|------|
| (none) | **No email change event** | - |
| Jan 6-7, 2026 | OTP Authentication | joeynaj@ibande.xyz |

- NO email change event exists
- OTP sent to email with no record of how it was added

---

## Full Search Results

Searched 1 year of data (124,321 OTP email events) for anomalies:

| Category | Count |
|----------|-------|
| Total OTP email events | 124,321 |
| Unique member/email combinations | 23,234 |
| Suspicious domain OTPs | 88 |
| With email change logged | 23 |
| **Without email change (anomaly)** | **65** |
| True domain mismatches (cgregory pattern) | **2** |

The 65 "without email change" cases were mostly masked versions of the same email (e.g., `mxke@protonmail.com` = `mike@protonmail.com`). Only 2 cases had truly different domains.

---

## Suspicious Domains Identified

| Domain | User | Email Change Logged? | Status |
|--------|------|---------------------|--------|
| ibande.xyz | cgregory | **NO** | ⚠️ Anomaly |
| mailclone2023.top | cpclements | **NO** | ⚠️ Anomaly |
| beepboopbot.top | mstrings | Yes | Normal |
| zenmail.top | LevSham | In profile | Normal |
| thaitudang.xyz | Robtdk | Yes | Normal |
| vuatrochoi.online | abusyjordan | Yes | Normal |
| endosferes.ru | Sallee | Yes | Normal |
| yandex.com | 4 users | In profile | Normal (legit provider) |
| yandex.ru | Bridge86 | In profile | Normal (legit provider) |
| mail.ru | irina3 | In profile | Normal (legit provider) |

---

## Key Questions for Cloud/OTP Team

1. **How can an OTP be sent to an email not in the member's profile?**
   - Is there a code path that bypasses profile validation?
   - Can OTP destination be specified in the request without verification?

2. **Why was no email change event logged?**
   - Was the email added through a different mechanism?
   - Is there a scenario where email updates don't trigger fraudmonitor logging?

3. **What systems can modify OTP delivery destination?**
   - Core banking integration?
   - SSO/authentication service?
   - Direct API calls?

---

## Appendix: Raw Event Data

### cgregory OTP Events
```
2026-01-06 02:42:12 | OTP Authentication
["email", "joeynaj@ibande.xyz", "default@calcoast.com", null, "success"]

2026-01-07 03:00:14 | OTP Authentication
["email", "joeynaj@ibande.xyz", "default@calcoast.com", null, "success"]
```

### cpclements OTP Event
```
2025-12-17 09:31:10 | OTP Authentication
["email", "meekhh@mailclone2023.top", "default@calcoast.com", null, "success"]
```

Note: `default@calcoast.com` is a system placeholder, not an actual delivery address.
