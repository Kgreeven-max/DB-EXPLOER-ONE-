# DBXDB Database Documentation

## Technical Reference for Legal, Audit, and Compliance Review

**Version:** 1.1
**Date:** December 23, 2025
**Prepared by:** Digital Banking Team, Cal Coast Credit Union
**Database:** dbxdb (MySQL)
**Server:** infinity-9ix.calcoastcu.org

---

## Table of Contents

0. [Executive Summary](#0-executive-summary)
1. [Database Overview](#1-database-overview)
2. [Core Tables for Fraud Monitoring](#2-core-tables-for-fraud-monitoring)
3. [fraudmonitor Table - Detailed Schema](#3-fraudmonitor-table---detailed-schema)
4. [alerthistory Table - Detailed Schema](#4-alerthistory-table---detailed-schema)
5. [Event Types Reference](#5-event-types-reference)
6. [Data Flow and Architecture](#6-data-flow-and-architecture)
7. [Example Account Analysis](#7-example-account-analysis)
8. [Common Audit Queries](#8-common-audit-queries)
9. [Appendix A: Data Dictionary](#appendix-a-complete-data-dictionary)
10. [Appendix B: Glossary of Terms](#appendix-b-glossary-of-terms)
11. [Appendix C: PII and Sensitive Data](#appendix-c-pii-and-sensitive-data)
12. [Appendix D: Audit Trail Evidence](#appendix-d-audit-trail-evidence)

---

## 0. Executive Summary

### Purpose
This document provides a complete technical reference to the DBXDB database, which stores all digital banking activity for Cal Coast Credit Union members. It is intended for use by legal counsel, auditors, compliance officers, and investigators who need to understand, query, or analyze member activity data.

### What DBXDB Contains
- **Member profiles** - Names, contact info, account status
- **Authentication logs** - Every login attempt (success/failure), OTP verifications
- **Activity tracking** - All actions taken in online/mobile banking
- **Alert records** - Every notification sent to members (email, SMS, push)
- **Device information** - Registered mobile devices and trusted browsers

### Data Retention
- **Retention period:** 5 years
- **Oldest available data:** Varies by table - No tables have been purged or archived since the inception of the database. An archiving process will take place in January 2026 for the fraudmonitor and alerthistory tables.

### Data Integrity
- All records are immutable (cannot be modified after creation)
- Each record has a unique identifier and timestamp
- Records are created in real-time as events occur
- No manual data entry - all records are system-generated

### Access Controls
- Database access requires authenticated credentials
- Read-only access for audit/compliance queries
- All access is logged

### Limitations - What DBXDB Does NOT Contain

DBXDB tracks **user actions and intent** in digital banking. It does NOT contain:

| Data Type | Where It Lives |
|-----------|----------------|
| Actual money movement (transfers completed, funds debited/credited) | Core Banking System (Symitar/Episys) |
| Account balances | Core Banking System |
| Check images from Remote Deposit | Alogent system |
| ATM/Debit card transactions | Card processor (FIS) |
| In-branch transactions | Core Banking System |
| Wire transfer completion | Core Banking System |
| ACH transaction settlement | Core Banking System |

**Example:** DBXDB shows a member *initiated* an External Account Transfer. To prove the money *actually moved*, you need core banking records from Symitar.

**For complete fraud investigation:** DBXDB provides the "who, when, where, what device" evidence. Core banking provides the "did the money move" evidence.

---

## 1. Database Overview

### Purpose
DBXDB is the primary database for Cal Coast Credit Union's Digital Banking Platform (DBX). It stores:
- Member authentication and session data
- Transaction activity logs
- Security events and fraud monitoring data
- Alert configurations and delivery history
- Account and membership information

### Scale
- **Total Tables:** 512
- **Fraud/Alert Related Tables:** 39

---

## 2. Core Tables for Fraud Monitoring

Fraud detection and alerting tables:

### Primary Tables

| Table Name | Purpose |
|------------|---------|
| `fraudmonitor` | **Main activity tracking table** - Logs all user events, logins, changes, and transactions |
| `alerthistory` | Records all alerts sent to members (email, SMS, push) |
| `archivedalerthistory` | Archived alert records |

### Alert Configuration Tables

| Table Name | Purpose |
|------------|---------|
| `alert` | Alert definitions and settings |
| `alerttype` | Types of alerts (security, account, transaction) |
| `alertsubtype` | Sub-categories of alerts |
| `alertcategory_view` | Alert categories view |
| `alertcondition` | Conditions that trigger alerts |
| `alertattribute` | Alert configuration attributes |
| `globalAlert` | System-wide alert configurations |

### User Alert Tables

| Table Name | Purpose |
|------------|---------|
| `customeralertswitch` | Customer alert on/off switches |
| `customeralertcategorychannel` | Customer channel preferences per category |
| `dbxcustomeralertentitlement` | DBX customer alert thresholds |

*Note: Legacy tables `useralerts`, `useraccountalerts`, and `customeralertentitlement` exist but contain stale data (no activity since 2019) and are not actively used.*

---

## 3. fraudmonitor Table - Detailed Schema

Primary table for tracking user activity in digital banking.

### Column Definitions

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | bigint | NO (PK) | Unique record identifier |
| `sessionid` | varchar(50) | YES | User session identifier - links multiple events in one session |
| `ipAddress` | varchar(50) | YES | IP address of the user (IPv4 or IPv6) |
| `muid` | varchar(50) | YES | Member Unique ID |
| `masterMembership` | varchar(50) | YES | Parent account/membership number |
| `userName` | varchar(50) | YES | Login username |
| `activityDate` | timestamp | NO | Date and time of the event (UTC) |
| `platform` | varchar(10) | YES | Platform code (see below) |
| `platformOS` | varchar(10) | YES | Operating system |
| `eventData` | json | YES | JSON array with event-specific details |
| `eventCategory` | varchar(255) | YES | Type of event (see Event Types section) |
| `delivered` | tinyint(1) | YES | Alert delivery status (1=delivered, 0=not delivered) |
| `browser` | varchar(255) | YES | Browser/device information |

### Platform Codes

| Code | Meaning |
|------|---------|
| `MB` | Mobile Banking (iOS/Android app) |
| `OLB` | Online Banking (Web browser) |

### NULL Values Explanation

Some fields contain NULL values. This is normal and does not indicate missing or corrupt data.

| Field | % NULL | Reason |
|-------|--------|--------|
| `delivered` | 100% | Field not used - ignore this column |
| `sessionid` | 0.9% | System-generated events (not user-initiated) |
| `ipAddress` | 0.9% | System-generated events (no client IP) |
| `platform` | 0.9% | System-generated events |
| `platformOS` | 0.9% | System-generated events |
| `browser` | 0.9% | System-generated events |
| `userName` | 1.9% | Events before user identification (OTP attempts, lockouts) |
| `muid` | 1.3% | Events before member lookup completes |
| `masterMembership` | 1.8% | Events before account association |
| `eventData` | 0% | Always populated |
| `eventCategory` | 0% | Always populated (note: 4,092 legacy records from July 2024 contain value "None") |

**When userName is NULL:**
- OTP Authentication (215K records) - OTP sent before user is verified
- Account Lockout (105K records) - Lockout triggered by failed attempts
- LoginFailure (5K records) - Failed login before username validated

**NULL does not mean:**
- Data was deleted
- An error occurred
- The record is incomplete

NULL simply means the value was not applicable or not yet known at the time the event was recorded.

### eventData JSON Structure

The `eventData` field is **always populated** (never NULL). It contains a JSON array with event-specific details.

**NULL values INSIDE the JSON array are normal.** They indicate optional fields that don't apply to that specific event.

Example: `["email@example.com", null, null, "619-555-1234", null, "0001234567"]`
- The `null` values mean the member doesn't have an alternate email or additional phone numbers on file.

#### eventData by Event Type

| Event Category | Array Structure | Example |
|----------------|-----------------|---------|
| **LoginSuccessful** | [primary_email, alt_email, phone1, phone2, phone3, account#] | `["user@email.com", null, "619-555-1234", null, null, "0001234567"]` |
| **LoginFailure** | [username, "password", "failed", first_name, last_name, ...] | `["jsmith", "password", "failed", "JOHN", "SMITH", ...]` |
| **Account Lockout** | [reason] | `["Incorrect Password"]` |
| **OTP Authentication** | [method, masked_phone, null, full_phone, status] | `["text", "xxx-xxx-1234", null, "619-555-1234", "success"]` |
| **Change Primary email** | [field_name, new_value, action] | `["Primary Email", "new@email.com", "revised"]` |
| **Change Phone Number** | [phone_type, new_number, action] | `["Home Phone", "8589991839", "revised"]` |
| **Change of Address** | [type, street, unit, country, state, city, zip, ...] | `["Mailing Address", "123 Main St", "", "US", "CA", "San Diego", "92101", ...]` |
| **New  Device Register** | [device_id, type] | `["a422a50484993ad9", "Remember Me"]` |
| **Card Activation** | [masked_card, status, message] | `["xxxx-xxxx-xxxx-1234", "Success", ""]` |
| **Remote Deposit** | [account, amount, check_number, ...] | Deposit details |
| **Bill Pay Payment** | [null, amount, account_desc, payment_type, ...] | `[null, "50.00", "CHECKING|0001234567", "PAY_NOW", ...]` |

#### NULL Values Inside eventData

3.5M+ LoginSuccessful events have `null` inside the array - this is normal and means:
- Member has no alternate email on file
- Member has fewer than 3 phone numbers registered
- Field is optional and not populated

**This is NOT an error or missing data.**

---

## 4. alerthistory Table - Detailed Schema

Tracks all alerts sent to members (email, SMS, push).

### Column Definitions

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar(50) | Unique alert record ID (UUID) |
| `EventId` | varchar(50) | Reference to triggering event |
| `AlertSubTypeId` | varchar(50) | Specific alert subtype code |
| `AlertTypeId` | varchar(50) | Alert type code |
| `AlertCategoryId` | varchar(50) | Category (ALERT_CAT_SECURITY, ALERT_CAT_ACCOUNTS, ALERT_CAT_TRANSACTIONAL) |
| `AlertStatusId` | varchar(50) | Event status (SID_EVENT_SUCCESS, SID_EVENT_FAILURE) |
| `Customer_Id` | varchar(50) | Customer identifier |
| `LanguageCode` | varchar(10) | Language (en-US) |
| `ChannelId` | varchar(50) | Delivery channel (CH_EMAIL, CH_SMS, CH_PUSH_NOTIFICATION, CH_NOTIFICATION_CENTER) |
| `Status` | varchar(50) | Delivery status |
| `Subject` | varchar(250) | Email subject line |
| `Message` | text | Full message content (HTML) |
| `SenderName` | varchar(50) | Sender name |
| `SenderEmail` | varchar(100) | Sender email |
| `ReferenceNumber` | varchar(50) | Transaction reference if applicable |
| `DispatchDate` | datetime | When alert was sent |
| `ErrorMessage` | text | Error details if delivery failed |
| `createdby` | varchar(50) | Username who triggered the alert |
| `createdts` | timestamp | Record creation timestamp |

### NULL Values Explanation

Some fields contain NULL values. This is normal and expected.

| Field | % NULL | Reason |
|-------|--------|--------|
| `Subject` | 32.1% | SMS and Push alerts do not have subject lines (only email) |
| `ReferenceNumber` | 41.1% | Only transaction alerts have reference numbers (security alerts do not) |
| `ErrorMessage` | 47.5% | Only failed deliveries have error messages (successful ones are NULL) |

**All other fields are 0% NULL** - they are always populated.

**NULL does not mean:**
- Data was deleted or lost
- An error occurred
- The alert was not sent

NULL simply means the field is not applicable for that alert type or delivery status.

### Delivery Status Values

| Status | Meaning |
|--------|---------|
| `SID_DELIVERY_SUBMITTED` | Alert sent successfully |
| `SID_DELIVERY_NOTSUBMITTED` | Alert not sent (conditions not met) |
| `SID_DELIVERYFAILED` | Delivery attempted but failed |

### Alert Category Codes

| Code | Description |
|------|-------------|
| `ALERT_CAT_SECURITY` | Security-related alerts (login failures, lockouts) |
| `ALERT_CAT_ACCOUNTS` | Account activity alerts (transfers, deposits, withdrawals) |
| `ALERT_CAT_TRANSACTIONAL` | Transaction and payment alerts |

### Complete AlertSubTypeId Values

All 30 alert types in the system, organized by category:

#### Security Alerts
| SubType | Count | Description |
|---------|-------|-------------|
| `LOGIN_ATTEMPT` | 3,191,450 | Successful login notification |
| `FAILED_LOGIN_ATTEMPT` | 1,701,765 | Failed login notification |
| `ACCOUNT_LOCKED` | 187,291 | Account locked due to failed attempts |
| `PASSWORD_CHANGE` | 77,229 | Password was changed |
| `USERNAME_CHANGE` | 9,020 | Username was changed |
| `LOCKED_ACCOUNT_ACTION` | 64 | Action taken on locked account |

#### Balance Alerts
| SubType | Count | Description |
|---------|-------|-------------|
| `WITHDRAWALS_ABOVE` | 6,328,207 | Withdrawal exceeds member's threshold |
| `DEPOSITS_ABOVE` | 1,343,489 | Deposit exceeds member's threshold |
| `MAX_BALANCE_ST` | 1,306,901 | Balance exceeds maximum threshold |
| `WITHDRAWALS_BELOW` | 128,497 | Withdrawal below member's threshold |
| `MIN_BALANCE_ST` | 85,005 | Balance falls below minimum threshold |
| `OVERDRAFT_ALERT` | 44,282 | Account is overdrawn |
| `DEPOSITS_BELOW` | 33,371 | Deposit below member's threshold |
| `LOW_LOC_AVAIL` | 5,262 | Low available credit on line of credit |

#### Transaction Alerts
| SubType | Count | Description |
|---------|-------|-------------|
| `ONETIME_OWN_ACCOUNT_TRANSFER` | 945,886 | One-time internal transfer completed |
| `DIRECT_DEPOSITS` | 492,720 | Direct deposit received |
| `CHECK_STATUS` | 101,017 | Check cleared or status changed |
| `SCHEDULED_OTHER_BANK_TRANSFER` | 14,096 | Scheduled external transfer executed |
| `SCHEDULED_OWN_ACCOUNT_TRANSFER` | 9,141 | Scheduled internal transfer executed |
| `OTHER_BANK_RECIPIENT_ADDED` | 5,010 | New external account linked |
| `DEPOSIT_MATURITY_REMINDER` | 798 | CD or term deposit maturing soon |

#### Profile Change Alerts
| SubType | Count | Description |
|---------|-------|-------------|
| `HOME_ADDRESS_CHANGE` | 14,161 | Home address was updated |
| `PRIMARY_PHONE_CHANGE` | 6,547 | Primary phone number changed |
| `HOME_PHONE_CHANGE` | 6,621 | Home phone number changed |
| `WORK_PHONE_CHANGE` | 5,013 | Work phone number changed |
| `PRIMARY_ADDRESS_CHANGE` | 4,248 | Primary address was updated |
| `PRIMARY_EMAIL_CHANGE` | 4,238 | Primary email address changed |
| `SECONDARY_EMAIL_CHANGE` | 3,759 | Secondary email address changed |

#### Payment Alerts
| SubType | Count | Description |
|---------|-------|-------------|
| `PAYMENT_DUE_DATE` | 9,739 | Loan payment due date reminder |
| `PAYMENT_OVERDUE` | 4,755 | Loan payment is overdue |

---

## 5. Event Types Reference

Event categories in `fraudmonitor.eventCategory` with counts:

### Authentication Events

| Event Category | Count | Description |
|----------------|-------|-------------|
| `LoginSuccessful` | 3,673,373 | User successfully logged in | This event was added on October 28th, 2025 and is not present prior to this date 
| `LoginFailure` | 242,277 | Failed login attempt (wrong password, etc.) |
| `Account Lockout` | 226,146 | Account locked due to multiple failures |
| `OTP Authentication` | 2,224,180 | One-time password verification (login, sensitive actions) |
| `OTP Authentication - View Card Details` | 10,667 | OTP for viewing card numbers |

*Note: LoginSuccessful and LoginFailure events added October 28, 2025 (maintenance update).*

### Device & Session Events

| Event Category | Count | Description |
|----------------|-------|-------------|
| `New  Device Register` | 10,490,760 | New device registered for mobile banking |

### Profile Change Events

| Event Category | Count | Description |
|----------------|-------|-------------|
| `Change Primary email` | - | Primary email address changed |
| `Change Alternate email` | - | Secondary email address changed |
| `Change Phone Number` | 7,730 | Phone number modified |
| `Change of Address` | 14,244 | Mailing/physical address updated |
| `Add New Number` | - | New phone number added to account |

### Transaction Events

| Event Category | Count | Description |
|----------------|-------|-------------|
| `External Account Transfer Scheduled` | 163,366 | Transfer to external bank scheduled |
| `New External Account Added` | 53,951 | External account linked for transfers |
| `Bill Pay Payment Sent/Scheduled` | 241,790 | Bill payment created |
| `Bill Pay Exception` | - | Bill payment error or exception |
| `New  Bill Payee Created` | 6,972 | New bill pay recipient added |
| `P2P Payment Scheduled` | 8,141 | Person-to-person payment initiated |
| `New PayItNow Recipient` | - | New instant payment recipient added |
| `Remote Deposit` | 409,517 | Mobile check deposit submitted |
| `Card Activation` | 19,712 | Debit/credit card activated |

*Note: P2P Payment Scheduled events are no longer accurately tracked after January 23, 2025 due to a change in the P2P SSO integration. Events after this date are sporadic and do not represent actual P2P activity volume.*

---

## 6. Data Flow and Architecture

### Event Capture Flow

```
Member Action (Login, Transfer, etc.)
        │
        ▼
┌─────────────────────┐
│  Digital Banking    │
│  Application        │
│  (Mobile/Web)       │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   fraudmonitor      │◄──── Real-time event logging
│   table             │       - Session tracking
│                     │       - IP capture
│                     │       - Platform detection
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Alert Engine       │◄──── Evaluates alert rules
│                     │       - User preferences
│                     │       - Global settings
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   alerthistory      │◄──── Delivery tracking
│   table             │       - Email/SMS/Push
│                     │       - Success/Failure
└─────────────────────┘
```

### Relationship Between Tables

- **fraudmonitor.userName** links to **customer.userName**
- **fraudmonitor.sessionid** groups events within a single session
- **alerthistory.Customer_Id** links to customer records
- **alerthistory.EventId** may reference fraudmonitor events

---

## 6.5 User Flow Walkthroughs

Data flow examples: user action → fraudmonitor → alerthistory. Use these to trace events during an audit.

---

### Scenario 1: OTP + Login Flow (Web Banking)

When a member logs into Online Banking (OLB), they verify via OTP before access is granted.

#### Step 1: Member enters credentials on calcoastcu.org

#### Step 2: OTP Authentication Event Created

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ fraudmonitor record ID: 17344552                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ activityDate:    2025-12-16 16:42:02                                        │
│ userName:        nashgreeven23                                              │
│ eventCategory:   OTP Authentication                                         │
│ platform:        OLB                                                        │
│ ipAddress:       63.196.134.181                                             │
│ sessionid:       3F0826A9033BA54E342E479151E08018                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

**eventData Breakdown:**
| Index | Value | Meaning |
|-------|-------|---------|
| 0 | "text" | OTP delivery method (text or voice) |
| 1 | "xxx-xxx-3429" | Masked phone number (shown to user) |
| 2 | null | Reserved |
| 3 | "760-659-3429" | Full phone number |
| 4 | "success" | OTP verification result |

#### Step 3: LoginSuccessful Event Created (1 second later)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ fraudmonitor record ID: 17344555                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ activityDate:    2025-12-16 16:42:03  ← 1 second after OTP                  │
│ userName:        nashgreeven23                                              │
│ eventCategory:   LoginSuccessful                                            │
│ platform:        OLB                                                        │
│ ipAddress:       63.196.134.181       ← Same IP as OTP event                │
│ sessionid:       C15324A169E69F218288BEFED4F1A8D9                           │
│ eventData:       ["kgreeven@calcoastcu.org", "greevenkendall@gmail.com",    │
│                   "760-659-3429", "760-659-3429", "760-659-3429", null]     │
└─────────────────────────────────────────────────────────────────────────────┘
```

**eventData Breakdown (Login):**
| Index | Value | Meaning |
|-------|-------|---------|
| 0 | "kgreeven@calcoastcu.org" | Primary email |
| 1 | "greevenkendall@gmail.com" | Alternate email |
| 2-4 | "760-659-3429" | Phone numbers on file |
| 5 | null or account# | Account reference |

Same IP address (63.196.134.181) and close timestamps indicate same login session.

---

### Scenario 2: Email/Phone Change Flow

Profile updates are logged for fraud monitoring.

#### Real Example: Member changes primary email

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ fraudmonitor record ID: 17840134                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ activityDate:    2025-12-22 22:09:12                                        │
│ userName:        aschauder01                                                │
│ eventCategory:   Change Primary email                                       │
│ platform:        OLB                                                        │
│ ipAddress:       70.95.65.35                                                │
│ eventData:       ["Primary Email", "aschauderari@gmail.com", "revised"]     │
└─────────────────────────────────────────────────────────────────────────────┘
```

**eventData Breakdown (Profile Change):**
| Index | Value | Meaning |
|-------|-------|---------|
| 0 | "Primary Email" | Field that was changed |
| 1 | "aschauderari@gmail.com" | New value |
| 2 | "revised" | Action type |

#### Phone Number Change Example:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ fraudmonitor record ID: 17838533                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ activityDate:    2025-12-22 21:50:51                                        │
│ userName:        justinc442                                                 │
│ eventCategory:   Change Phone Number                                        │
│ platform:        MB                                                         │
│ eventData:       ["Work Phone", "6193897538", "revised"]                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

Fraud indicator: Rapid email + phone + address changes from unfamiliar IPs may indicate account takeover.

---

### Scenario 3: Failed Login + Account Lockout → Alert Sent

Multiple failed login attempts trigger Account Lockout and send a security alert.

#### Step 1: Member enters wrong password multiple times

```
Timeline for user: astewart57 (December 15, 2025)
─────────────────────────────────────────────────────────────────────────────
23:18:43  │ LoginFailure    │ OLB │ IP: 2600:8801:8e23:4300:...
23:18:44  │ Account Lockout │ OLB │ IP: 2600:8801:8e23:4300:...  ← LOCKED
23:19:49  │ LoginFailure    │ OLB │ IP: 2600:8801:8e23:4300:...  (still locked)
23:19:49  │ Account Lockout │ OLB │ IP: 2600:8801:8e23:4300:...
23:21:24  │ LoginFailure    │ OLB │ IP: 2600:8801:8e23:4300:...
23:21:25  │ Account Lockout │ OLB │ IP: 2600:8801:8e23:4300:...
─────────────────────────────────────────────────────────────────────────────
```

#### Step 2: Alert Engine triggers FAILED_LOGIN_ATTEMPT alert

#### Step 3: alerthistory records created

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ alerthistory records for astewart57                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ DispatchDate:    2025-12-15 23:52:08                                        │
│ AlertSubTypeId:  FAILED_LOGIN_ATTEMPT                                       │
│ createdby:       astewart57            ← Links to fraudmonitor.userName     │
│                                                                             │
│ Channel Attempts:                                                           │
│   CH_EMAIL               → SID_DELIVERY_SUBMITTED     ✓ Sent                │
│   CH_NOTIFICATION_CENTER → SID_DELIVERY_SUBMITTED     ✓ Sent                │
│   CH_SMS                 → SID_DELIVERYFAILED         ✗ Global alert        │
│   CH_PUSH_NOTIFICATION   → SID_DELIVERYFAILED         ✗ Invalid Subscribers │
└─────────────────────────────────────────────────────────────────────────────┘
```

Note: Alert sent ~30 minutes after lockout (23:21 lockout → 23:52 alert) due to batch processing delay.

---

### Field Correlation Map

`fraudmonitor` → `alerthistory` field mapping:

```
┌─────────────────────────────────────┐         ┌─────────────────────────────────────┐
│         fraudmonitor                │         │          alerthistory               │
├─────────────────────────────────────┤         ├─────────────────────────────────────┤
│                                     │         │                                     │
│  userName ──────────────────────────┼────────►│  createdby                          │
│  (e.g., "astewart57")               │         │  (e.g., "astewart57")               │
│                                     │         │                                     │
│  activityDate ──────────────────────┼───~────►│  DispatchDate                       │
│  (2025-12-15 23:21:25)              │  delay  │  (2025-12-15 23:52:08)              │
│                                     │         │                                     │
│  eventCategory ─────────────────────┼───map──►│  AlertSubTypeId                     │
│  "LoginFailure" / "Account Lockout" │         │  "FAILED_LOGIN_ATTEMPT"             │
│                                     │         │                                     │
│  ipAddress                          │         │  (not stored in alerthistory)       │
│                                     │         │                                     │
│  sessionid                          │         │  EventId (may link)                 │
│                                     │         │                                     │
│  eventData (JSON array)             │         │  Message (HTML content with         │
│  [raw details]                      │         │   details formatted for user)       │
│                                     │         │                                     │
│  platform                           │         │  ChannelId                          │
│  "OLB" / "MB"                       │         │  "CH_EMAIL" / "CH_SMS" / "CH_PUSH_NOTIFICATION"  │
│                                     │         │                                     │
└─────────────────────────────────────┘         └─────────────────────────────────────┘
```

### Event Category → Alert SubType Mapping

**How Events Trigger Alerts:**
- fraudmonitor logs the **user action** (what the member did)
- alerthistory logs the **notification sent** (if the member has that alert enabled)
- Not every event triggers an alert - members choose which alerts they want

#### Direct Mappings (fraudmonitor event → alerthistory alert)

| fraudmonitor.eventCategory | alerthistory.AlertSubTypeId | Trigger Condition |
|----------------------------|-----------------------------|--------------------|
| LoginSuccessful | LOGIN_ATTEMPT | Always (if enabled by member) |
| LoginFailure | FAILED_LOGIN_ATTEMPT | Always |
| Account Lockout | ACCOUNT_LOCKED | Always |
| Change Primary email | PRIMARY_EMAIL_CHANGE | Always |
| Change Alternate email | SECONDARY_EMAIL_CHANGE | Always |
| Change Phone Number | PRIMARY_PHONE_CHANGE, HOME_PHONE_CHANGE, WORK_PHONE_CHANGE | Depends on which phone changed |
| Change of Address | HOME_ADDRESS_CHANGE, PRIMARY_ADDRESS_CHANGE | Depends on address type |
| External Account Transfer Scheduled | SCHEDULED_OTHER_BANK_TRANSFER | When scheduled |
| External Account Transfer Scheduled | ONETIME_OWN_ACCOUNT_TRANSFER | When one-time |
| New External Account Added | OTHER_BANK_RECIPIENT_ADDED | Always |
| Remote Deposit | DEPOSITS_ABOVE | If deposit exceeds member's threshold |

#### Threshold-Based Alerts (triggered by account activity, not specific events)

| Alert Type | Trigger |
|------------|---------|
| WITHDRAWALS_ABOVE | Any withdrawal exceeding member-set threshold |
| WITHDRAWALS_BELOW | Any withdrawal below member-set threshold |
| DEPOSITS_ABOVE | Any deposit exceeding member-set threshold |
| DEPOSITS_BELOW | Any deposit below member-set threshold |
| MAX_BALANCE_ST | Account balance exceeds member-set maximum |
| MIN_BALANCE_ST | Account balance falls below member-set minimum |
| OVERDRAFT_ALERT | Account goes negative |
| LOW_LOC_AVAIL | Line of credit available amount is low |

#### System-Generated Alerts (not from user actions)

| Alert Type | Trigger |
|------------|---------|
| DIRECT_DEPOSITS | ACH direct deposit received |
| CHECK_STATUS | Check cleared or status changed |
| PAYMENT_DUE_DATE | Loan payment due date approaching |
| PAYMENT_OVERDUE | Loan payment past due |
| DEPOSIT_MATURITY_REMINDER | CD or term deposit approaching maturity |

---

## 7. Example Account Analysis

Using account **nashgreeven23** as a reference:

### Recent Activity Summary (December 2025)

| Date/Time | Event | Platform | IP Address | Browser |
|-----------|-------|----------|------------|---------|
| 2025-12-22 22:07:15 | LoginSuccessful | MB | 45.59.210.118 | iPhone |
| 2025-12-22 16:44:17 | LoginSuccessful | MB | 45.59.210.118 | iPhone |
| 2025-12-22 13:59:49 | LoginSuccessful | MB | 2600:1700:5390... (IPv6) | iPhone |
| 2025-12-16 16:42:03 | LoginSuccessful | OLB | 63.196.134.181 | Firefox |
| 2025-12-16 16:42:02 | OTP Authentication | OLB | 63.196.134.181 | Firefox |

### Data Notes

- Primary device: Mobile Banking (MB) on iPhone
- Occasional OLB via Firefox
- IPv4: 45.59.210.118 | IPv6: 2600:1700:5390... (home ISP)
- OTP precedes OLB logins (required for web access)
- eventData: `["kgreeven@calcoastcu.org", "greevenkendall@gmail.com", "760-659-3429", "760-659-3429", "760-659-3429", "0001122897"]`

---

## 8. Common Audit Queries

### Query 1: Find All Activity for a Specific User

```sql
SELECT
    activityDate,
    eventCategory,
    platform,
    ipAddress,
    browser,
    eventData
FROM fraudmonitor
WHERE userName = 'username_here'
ORDER BY activityDate DESC
LIMIT 100;
```

### Query 2: Find Failed Login Attempts in Last 24 Hours

```sql
SELECT
    userName,
    ipAddress,
    activityDate,
    platform,
    browser
FROM fraudmonitor
WHERE eventCategory = 'LoginFailure'
  AND activityDate >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY activityDate DESC;
```

### Query 3: Account Lockouts by Day

```sql
SELECT
    DATE(activityDate) as lockout_date,
    COUNT(*) as lockout_count,
    COUNT(DISTINCT userName) as unique_users
FROM fraudmonitor
WHERE eventCategory = 'Account Lockout'
  AND activityDate >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(activityDate)
ORDER BY lockout_date DESC;
```

### Query 4: Email/Phone Changes (Potential Fraud Indicator)

```sql
SELECT
    activityDate,
    userName,
    masterMembership,
    eventCategory,
    ipAddress,
    eventData,
    browser
FROM fraudmonitor
WHERE eventCategory IN (
    'Change Primary email',
    'Change Alternate email',
    'Change Phone Number'
)
  AND activityDate >= '2025-01-01'
ORDER BY activityDate DESC;
```

### Query 5: Suspicious IP Activity (Multiple Accounts from Same IP)

```sql
SELECT
    ipAddress,
    COUNT(DISTINCT userName) as unique_users,
    GROUP_CONCAT(DISTINCT userName) as usernames,
    COUNT(*) as total_events,
    MIN(activityDate) as first_seen,
    MAX(activityDate) as last_seen
FROM fraudmonitor
WHERE activityDate >= DATE_SUB(NOW(), INTERVAL 7 DAY)
  AND ipAddress IS NOT NULL
GROUP BY ipAddress
HAVING unique_users > 3
ORDER BY unique_users DESC;
```

### Query 6: Alert Delivery Failures

```sql
SELECT
    DispatchDate,
    Customer_Id,
    AlertSubTypeId,
    ChannelId,
    Status,
    ErrorMessage
FROM alerthistory
WHERE Status IN ('SID_DELIVERY_NOTSUBMITTED', 'SID_DELIVERYFAILED')
  AND DispatchDate >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY DispatchDate DESC;
```

### Query 7: Device Registration Patterns

```sql
SELECT
    DATE(activityDate) as reg_date,
    COUNT(*) as new_devices,
    COUNT(DISTINCT userName) as unique_users
FROM fraudmonitor
WHERE eventCategory = 'New  Device Register'
  AND activityDate >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(activityDate)
ORDER BY reg_date DESC;
```

### Query 8: OTP Authentication by Status

```sql
SELECT
    JSON_EXTRACT(eventData, '$[4]') as otp_status,
    COUNT(*) as count,
    DATE(activityDate) as date
FROM fraudmonitor
WHERE eventCategory = 'OTP Authentication'
  AND activityDate >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY JSON_EXTRACT(eventData, '$[4]'), DATE(activityDate)
ORDER BY date DESC, count DESC;
```

### Query 9: Find Customer_Id by Username

Use this to get the Customer_Id needed for alerthistory lookups.

```sql
-- Replace 'USERNAME_HERE' with the actual username
SELECT id AS Customer_Id, UserName, FirstName, LastName
FROM customer
WHERE UserName = 'USERNAME_HERE';
```

### Query 10: Look Up Member Activity by Username

```sql
-- Replace 'USERNAME_HERE' with the actual username
SELECT *
FROM fraudmonitor
WHERE userName = 'USERNAME_HERE'
ORDER BY activityDate DESC
LIMIT 1000;
```

### Query 11: Look Up Member Activity by Membership Number

```sql
-- Replace 'MEMBERSHIP_NUMBER' with the actual membership number
SELECT *
FROM fraudmonitor
WHERE masterMembership = 'MEMBERSHIP_NUMBER'
ORDER BY activityDate DESC
LIMIT 1000;
```

### Query 12: Look Up Alerts Sent to Member

First use Query 9 to get the Customer_Id, then use it here.

```sql
-- Replace 'CUSTOMER_ID' with the Customer_Id from Query 9
SELECT *
FROM alerthistory
WHERE Customer_Id = 'CUSTOMER_ID'
ORDER BY createdts DESC
LIMIT 1000;
```

---

## Appendix A: Complete Data Dictionary

Active tables in DBXDB, organized by function.

**Active Tables:** 20

*Last updated: December 23, 2025*

---

### A.1 Core Member Tables

These tables store member profile and contact information.

#### customer (160,210 rows)
**Purpose:** Primary member/user profile table. Contains all registered digital banking users.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar(50) | Primary key - unique customer identifier |
| `CustomerType_id` | varchar(50) | Customer type (TYPE_ID_RETAIL, TYPE_ID_BUSINESS) |
| `FirstName` | varchar(200) | Member's first name |
| `LastName` | varchar(200) | Member's last name |
| `Status_id` | varchar(50) | Account status (SID_CUS_ACTIVE, SID_CUS_LOCKED) |
| `UserName` | varchar(50) | **Unique login username** - links to fraudmonitor.userName |
| `DateOfBirth` | date | Member's date of birth |
| `Ssn` | varchar(50) | Last 4 digits of SSN (masked) |
| `Token` | varchar(200) | Core system token identifier |
| `IsOlbAllowed` | tinyint(1) | Online banking access permission |
| `isUserAccountLocked` | tinyint(1) | Account lock status |
| `IsEnrolledForOlb` | tinyint(1) | OLB enrollment status |
| `isBillPaySupported` | bit(1) | Bill pay feature enabled |
| `isP2PSupported` | bit(1) | Person-to-person payment enabled |
| `isWireTransferEligible` | bit(1) | Wire transfer eligible |
| `lockedOn` | timestamp | Timestamp when account was locked |
| `createdts` | timestamp | Account creation date |
| `lastmodifiedts` | timestamp | Last profile update |

**Key Relationships:**
- `customer.UserName` → `fraudmonitor.userName`
- `customer.id` → `customeraddress.Customer_id`
- `customer.id` → `customercommunication.Customer_id`
- `customer.id` → `customerdevice.Customer_id`

---

#### customeraddress (313,884 rows)
**Purpose:** Physical and mailing addresses for members.

| Column | Type | Description |
|--------|------|-------------|
| `Customer_id` | varchar(50) | Links to customer.id |
| `Address_id` | varchar(50) | Links to address details |
| `Type_id` | varchar(50) | Address type (home, mailing, work) |
| `isPrimary` | tinyint(1) | Primary address flag |
| `DurationOfStay` | varchar(50) | How long at address |
| `HomeOwnership` | varchar(50) | Own/rent status |

---

#### customercommunication (327,932 rows)
**Purpose:** Contact information (email addresses, phone numbers).

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar(50) | Primary key |
| `Type_id` | varchar(50) | Communication type (email, phone, work phone) |
| `Customer_id` | varchar(50) | Links to customer.id |
| `isPrimary` | tinyint(1) | Primary contact flag |
| `Value` | varchar(100) | **Email address or phone number** |
| `Extension` | varchar(50) | Phone extension |
| `phoneCountryCode` | varchar(10) | Country code for phone |

---

#### customerdevice (979,391 rows)
**Purpose:** Registered devices for mobile banking. Used to track device enrollment and activity.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar(50) | Device unique identifier |
| `Customer_id` | varchar(50) | Links to customer.id |
| `DeviceName` | varchar(50) | Device name (iPhone, Android, etc.) |
| `LastLoginTime` | timestamp | Last login from this device |
| `LastUsedIp` | varchar(50) | Last IP address used |
| `Status_id` | varchar(50) | Device status |
| `OperatingSystem` | varchar(50) | iOS, Android, etc. |
| `Channel_id` | varchar(50) | Access channel |
| `EnrollmentDate` | date | When device was registered |

---

### A.2 Authentication & Security Tables

These tables track authentication events, OTPs, and security-related data.

#### OTP (17,999 rows)
**Purpose:** One-Time Password storage for authentication. Records are short-lived.

| Column | Type | Description |
|--------|------|-------------|
| `securityKey` | varchar(50) | Primary key - unique OTP session |
| `Otp` | varchar(10) | The 6-digit OTP code |
| `OtpType` | varchar(45) | Type of OTP request |
| `InvalidAttempt` | int | Number of failed attempts |
| `createdts` | timestamp | When OTP was generated |
| `Phone` | varchar(45) | Phone number OTP was sent to |
| `User_id` | varchar(50) | Associated user |
| `NumberOfRetries` | int | Retry count |

---

#### passwordhistory (160,201 rows)
**Purpose:** Tracks password changes for security compliance.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar(50) | Primary key |
| `Customer_id` | varchar(50) | Links to customer.id |
| `PreviousPassword` | varchar(100) | Hashed previous password |
| `createdts` | timestamp | When password was changed |

---

#### customer_rememberme (111,048 rows)
**Purpose:** Stores "remember this device" tokens for trusted device login.

| Column | Type | Description |
|--------|------|-------------|
| `device_id` | varchar(50) | Device identifier |
| `Customer_id` | varchar(50) | Links to customer.id |
| `device_token` | varchar(50) | Trust token |
| `createdts` | timestamp | When token was created |
| `lastmodifiedts` | timestamp | Last use of token |

---

#### fraudmonitor (17,810,987 rows) - Primary Activity Table
Main activity tracking table. Records all user actions in digital banking.

| Column | Type | Description |
|--------|------|-------------|
| `id` | bigint | Primary key - auto-increment |
| `sessionid` | varchar(50) | Session identifier - groups related events |
| `ipAddress` | varchar(50) | User's IP address (IPv4 or IPv6) |
| `muid` | varchar(50) | Member unique ID |
| `masterMembership` | varchar(50) | Parent account number |
| `userName` | varchar(50) | **Login username - links to customer.UserName** |
| `activityDate` | timestamp | When event occurred |
| `platform` | varchar(10) | **MB** (Mobile Banking) or **OLB** (Online Banking) |
| `platformOS` | varchar(10) | Operating system |
| `eventData` | json | **JSON array with event-specific details** |
| `eventCategory` | varchar(255) | **Event type (see Section 5)** |
| `delivered` | tinyint(1) | Alert delivery status |
| `browser` | varchar(255) | Browser/device info |

**Example nashgreeven23 record:**
```json
{
  "userName": "nashgreeven23",
  "eventCategory": "LoginSuccessful",
  "platform": "MB",
  "eventData": ["kgreeven@calcoastcu.org", "greevenkendall@gmail.com", "760-659-3429", "760-659-3429", "760-659-3429", "0001122897"]
}
```

---

### A.3 Alert Configuration Tables

These tables define the alert system structure and available alert types.

#### alert (24 rows)
**Purpose:** Alert definitions and master configuration.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar(50) | Primary key |
| `AlertType_id` | varchar(50) | Links to alerttype |
| `Name` | varchar(50) | Alert name |
| `Description` | varchar(250) | Alert description |
| `IsSmsActive` | tinyint(1) | SMS channel enabled |
| `IsEmailActive` | tinyint(1) | Email channel enabled |
| `IsPushActive` | tinyint(1) | Push notification enabled |

---

#### alerttype (4 rows)
**Purpose:** High-level alert categories.

| ID | Name | Description |
|----|------|-------------|
| 1 | Security | Account security alerts |
| 2 | Accounts | Account activity alerts |
| 3 | Transactions | Transaction alerts |
| 4 | General | General notifications |

---

#### alertsubtype (33 rows)
**Purpose:** Specific alert types within categories.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar(100) | Alert subtype ID (e.g., FAILED_LOGIN_ATTEMPT) |
| `AlertTypeId` | varchar(255) | Parent alert type |
| `Name` | varchar(255) | Display name |
| `Description` | varchar(1000) | Detailed description |
| `Status_id` | varchar(50) | Active/inactive |

**Common AlertSubTypeId Values:**
- `FAILED_LOGIN_ATTEMPT` - Login failure notification
- `MAX_BALANCE_ST` - Balance threshold alert
- `DEPOSITS_ABOVE` - Deposit amount alert
- `WITHDRAWALS_ABOVE` - Withdrawal amount alert
- `ONETIME_OWN_ACCOUNT_TRANSFER` - Transfer notification
- `WORK_PHONE_CHANGE` - Phone change alert
- `PRIMARY_EMAIL_CHANGE` - Email change alert

---

#### alertcondition (8 rows)
**Purpose:** Defines conditions that trigger alerts.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar(255) | Condition ID |
| `Name` | varchar(255) | Condition name |
| `NoOfFields` | int | Number of fields to evaluate |

---

### A.4 Customer Alert Settings Tables

These tables store per-customer alert preferences.

#### customeralertswitch (32,707 rows)
**Purpose:** On/off switches for alert categories per customer/account.

| Column | Type | Description |
|--------|------|-------------|
| `Customer_id` | varchar(100) | Customer identifier |
| `AccountID` | varchar(50) | Account number |
| `AlertCategoryId` | varchar(100) | Alert category |
| `AccountType` | varchar(100) | Account type |
| `Status_id` | varchar(100) | On/Off status |

---

#### customeralertcategorychannel (102,481 rows)
**Purpose:** Customer's preferred delivery channel per alert category.

| Column | Type | Description |
|--------|------|-------------|
| `Customer_id` | varchar(100) | Customer identifier |
| `AlertCategoryId` | varchar(100) | Alert category |
| `ChannelId` | varchar(100) | CH_EMAIL, CH_SMS, CH_PUSH_NOTIFICATION, CH_NOTIFICATION_CENTER |
| `AccountId` | varchar(100) | Account number |

---

#### dbxcustomeralertentitlement (172,799 rows)
**Purpose:** DBX-specific alert entitlements and thresholds per customer.

| Column | Type | Description |
|--------|------|-------------|
| `Customer_id` | varchar(50) | Customer identifier |
| `AlertTypeId` | varchar(255) | Alert type |
| `AccountId` | varchar(255) | Account number |
| `Value1` | varchar(255) | Threshold value 1 (e.g., min balance) |
| `Value2` | varchar(255) | Threshold value 2 (e.g., max amount) |
| `Balance` | varchar(255) | Current balance |

---

### A.5 Alert Delivery Tables

These tables track alert dispatch and delivery status.

#### alerthistory (15,951,807 rows) - Primary Alert Table
Records all alerts sent to members. Tracks delivery status across all channels.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar(100) | Primary key (UUID) |
| `EventId` | varchar(100) | Reference to triggering event |
| `AlertSubTypeId` | varchar(100) | **Alert type (FAILED_LOGIN_ATTEMPT, etc.)** |
| `AlertTypeId` | varchar(100) | Parent alert type |
| `AlertCategoryId` | varchar(100) | Alert category (ALERT_CAT_SECURITY, ALERT_CAT_ACCOUNTS, ALERT_CAT_TRANSACTIONAL) |
| `AlertStatusId` | varchar(50) | Event status |
| `Customer_Id` | varchar(50) | Customer identifier |
| `ChannelId` | varchar(100) | **Delivery channel (CH_EMAIL, CH_SMS, CH_PUSH_NOTIFICATION, CH_NOTIFICATION_CENTER)** |
| `Status` | varchar(255) | **Delivery status (SID_DELIVERY_SUBMITTED, SID_DELIVERYFAILED)** |
| `Subject` | varchar(255) | Email subject line |
| `Message` | text | Full message content (HTML) |
| `ReferenceNumber` | varchar(100) | Transaction reference if applicable |
| `DispatchDate` | timestamp | **When alert was sent** |
| `ErrorMessage` | text | Error details if delivery failed |
| `createdby` | varchar(255) | **Username who triggered the alert** |

**Key Relationships:**
- `alerthistory.createdby` ≈ `fraudmonitor.userName`
- `alerthistory.DispatchDate` follows `fraudmonitor.activityDate`
- `alerthistory.AlertSubTypeId` maps from `fraudmonitor.eventCategory`

---

#### notification (1,266,276 rows)
**Purpose:** General in-app notifications.

| Column | Type | Description |
|--------|------|-------------|
| `notificationId` | int | Primary key |
| `notificationModule` | varchar(100) | Source module |
| `notificationSubject` | varchar(1000) | Subject line |
| `notificationText` | varchar(10000) | Full text |
| `isRead` | varchar(100) | Read status |
| `receivedDate` | datetime | When received |

---

### A.6 DBX Alert System Tables

Digital Banking Experience (DBX) specific alert configuration.

#### dbxalertcategory (3 rows)
**Purpose:** DBX alert categories.

| ID | Name | accountLevel |
|----|------|--------------|
| ALERT_CAT_ACCOUNTS | Account Alerts | Yes |
| ALERT_CAT_SECURITY | Security Alerts | No |
| ALERT_CAT_TRANSACTIONAL | Transaction Alerts | Yes |

---

#### dbxalerttype (21 rows)
**Purpose:** DBX-specific alert type definitions.

| Column | Type | Description |
|--------|------|-------------|
| `id` | varchar(255) | Alert type ID |
| `Name` | varchar(255) | Display name |
| `AlertCategoryId` | varchar(255) | Parent category |
| `AttributeId` | varchar(100) | Threshold attribute |
| `AlertConditionId` | varchar(255) | Trigger condition |
| `IsGlobal` | tinyint | Global alert flag |

---

### A.7 Other Active Tables

#### customerpreference (1,751 rows)
**Purpose:** User preferences and default settings.

| Column | Type | Description |
|--------|------|-------------|
| `Customer_id` | varchar(50) | Customer identifier |
| `DefaultAccountDeposit` | varchar(45) | Default deposit account |
| `DefaultAccountTransfers` | varchar(50) | Default transfer account |
| `PreferedOtpMethod` | varchar(50) | Preferred OTP method (text/voice) |
| `areUserAlertsTurnedOn` | varchar(50) | Master alert toggle |

---

### A.8 Table Relationship Diagram

```
┌─────────────────┐      ┌─────────────────────┐      ┌─────────────────┐
│    customer     │──────│ customercommunication│      │   fraudmonitor  │
│                 │      │                     │      │                 │
│  id             │◄─────│  Customer_id        │      │  userName ──────┼───┐
│  UserName ──────┼──────┼──────────────────────────►│                 │   │
│  Status_id      │      │  Value (email/phone)│      │  eventCategory  │   │
│  createdts      │      └─────────────────────┘      │  activityDate   │   │
└────────┬────────┘                                   │  ipAddress      │   │
         │                                            │  eventData      │   │
         │        ┌─────────────────────┐             └────────┬────────┘   │
         │        │   customerdevice    │                      │            │
         ├───────►│                     │                      │            │
         │        │  Customer_id        │                      ▼            │
         │        │  DeviceName         │             ┌─────────────────┐   │
         │        │  LastLoginTime      │             │  alerthistory   │   │
         │        │  LastUsedIp         │             │                 │   │
         │        └─────────────────────┘             │  createdby ◄────┼───┘
         │                                            │  AlertSubTypeId │
         │        ┌─────────────────────┐             │  DispatchDate   │
         │        │  customeraddress    │             │  Status         │
         └───────►│                     │             │  Message        │
                  │  Customer_id        │             └─────────────────┘
                  │  Address_id         │
                  └─────────────────────┘
```

---

### A.9 Empty/Inactive Tables (Not Documented)

Empty or stale tables (no activity since 2019). Not used in current audits.

**Empty Tables:**
- `customernote` - Empty (0 rows)
- `customersecurityquestions` - Empty (0 rows)
- `membershipowner` - Empty (0 rows)
- `globalAlert` - Empty (0 rows)
- `scheduledtransaction` - Empty (0 rows)
- `travelnotification` - Empty (0 rows)

**Stale Tables (Low count + No recent data):**
- `externalaccount` - 30 rows, last activity 2018 (deprecated external transfer feature)
- `useralerts` - 6 rows, no 2024+ data (legacy alert system)
- `useraccountalerts` - 102 rows, no 2024+ data (legacy alert system)
- `customeralertentitlement` - Empty (replaced by `dbxcustomeralertentitlement`)
- `transaction` - 694 rows, last activity 2019 (legacy, not used for current transactions)
- `membership` - 36 rows, no timestamps (legacy test data)
- `membershipaccounts` - 40 rows, no timestamps (legacy test data)

*Last updated: December 23, 2025*

---

## Appendix B: Glossary of Terms

| Term | Definition |
|------|------------|
| **DBXDB** | Digital Banking Experience Database - the primary database storing all online/mobile banking activity |
| **OLB** | Online Banking - web browser access via calcoastcu.org |
| **MB** | Mobile Banking - iOS/Android app access |
| **OTP** | One-Time Password - 6-digit code sent via text or voice for authentication |
| **Session ID** | Unique identifier linking multiple events from a single user session |
| **IP Address** | Internet Protocol address - identifies the network location of the user's device |
| **IPv4** | Standard IP format (e.g., 192.168.1.1) |
| **IPv6** | Extended IP format (e.g., 2600:1700:5390:...) - used by mobile carriers |
| **PII** | Personally Identifiable Information - data that can identify an individual |
| **SSN** | Social Security Number - stored as last 4 digits only |
| **Alert** | Notification sent to member via email, SMS, or push notification |
| **Event Category** | Classification of user action (LoginSuccessful, Account Lockout, etc.) |
| **eventData** | JSON array containing event-specific details (emails, phones, amounts) |
| **Platform** | Access method - MB (mobile) or OLB (web browser) |
| **Channel** | Delivery method for alerts - CH_EMAIL, CH_SMS, CH_PUSH_NOTIFICATION, CH_NOTIFICATION_CENTER |
| **Customer_Id** | Unique internal identifier for a member |
| **userName** | Member's login username (chosen during enrollment) |
| **masterMembership** | Primary account/membership number |
| **Timestamp (UTC)** | Date/time in Coordinated Universal Time (8 hours ahead of PST) |

---

## Appendix C: PII and Sensitive Data

### Fields Containing PII

| Table | Field | Data Type | Protection |
|-------|-------|-----------|------------|
| `customer` | `FirstName`, `LastName` | Full name | None (plaintext) |
| `customer` | `DateOfBirth` | Full DOB | None (plaintext) |
| `customer` | `Ssn` | Last 4 digits only | Masked (only last 4 stored) |
| `customer` | `UserName` | Login username | None (user-chosen) |
| `customercommunication` | `Value` | Email/Phone | None (plaintext) |
| `customeraddress` | `Address_id` | Physical address ref | Linked to address table |
| `fraudmonitor` | `eventData` | JSON with emails/phones | None (plaintext in JSON) |
| `fraudmonitor` | `ipAddress` | User IP address | None (plaintext) |
| `alerthistory` | `Message` | Alert content (HTML) | Contains member-specific data |
| `OTP` | `Otp` | 6-digit code | Short-lived (expires in minutes) |
| `OTP` | `Phone` | Phone number | None (plaintext) |
| `passwordhistory` | `PreviousPassword` | Password | Hashed (not reversible) |

### Data Protection Notes

1. **SSN Handling:** Only the last 4 digits are stored. Full SSN is never written to DBXDB.

2. **Password Storage:** Passwords are hashed using one-way encryption. The original password cannot be recovered from the stored hash.

3. **OTP Expiration:** One-time passwords expire within minutes and are not reusable.

4. **Email/Phone Storage:** Contact information is stored in plaintext for operational use (sending alerts, OTP delivery).

5. **IP Address Logging:** IP addresses are logged for security and fraud detection purposes.

### Accessing Member Data

To retrieve all data for a specific member:

```sql
-- Find customer record
SELECT * FROM customer WHERE UserName = 'username_here';

-- Find all activity
SELECT * FROM fraudmonitor WHERE userName = 'username_here' ORDER BY activityDate;

-- Find all alerts sent
SELECT * FROM alerthistory WHERE createdby = 'username_here' ORDER BY DispatchDate;

-- Find contact info
SELECT * FROM customercommunication WHERE Customer_id = 'customer_id_here';
```

---

## Appendix D: Audit Trail Evidence

### What Constitutes Proof of User Action

Each record in `fraudmonitor` proves that a specific action occurred because:

1. **Unique Record ID** - Every event has an auto-increment `id` that cannot be duplicated
2. **Timestamp** - `activityDate` records exact UTC time of the event
3. **User Identification** - `userName` identifies who performed the action
4. **Session Tracking** - `sessionid` links related events in a single session
5. **Network Origin** - `ipAddress` records where the action originated
6. **Device/Browser** - `browser` field captures device fingerprint
7. **Platform** - `platform` indicates mobile app vs web browser
8. **Event Details** - `eventData` JSON contains specifics (amounts, recipients, etc.)

### Chain of Evidence

```
Member performs action
        ↓
fraudmonitor record created (immutable)
        ↓
Alert engine evaluates rules
        ↓
alerthistory record created (immutable)
        ↓
Notification delivered (email/SMS/push)
```

### Timestamp Interpretation

- All timestamps are stored in **UTC** (Coordinated Universal Time)
- To convert to Pacific Time: subtract 8 hours (PST) or 7 hours (PDT)
- Example: `2025-12-22 22:07:15 UTC` = `2025-12-22 14:07:15 PST`

---

*For questions, contact Digital Banking.*
