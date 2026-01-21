# Digital Banking Board Report - SQL Query Documentation

## Overview
This document provides comprehensive documentation for all SQL queries used in the Digital Banking Board Report. These queries pull from the DWHA (Data Warehouse) SQL Server.

**Important:** v96 (Jwaala Legacy) is NO LONGER NEEDED - all users have migrated to v64 (new digital banking platform).

---

## Database Connection
- **Server:** DWHA
- **Database:** SymWarehouse
- **Authentication:** Windows Authentication (Trusted_Connection)

---

## Primary Data Source

### DigitalChannelsMemberStatsSummary Table
```
SymWarehouse.History.DigitalChannelsMemberStatsSummary
```

This summary table contains pre-aggregated monthly statistics for all digital banking metrics.

**Key Columns:**
| Column | Description |
|--------|-------------|
| digitalstat | Stat code identifier |
| AsOfDate | Month-end date of the statistic |
| COUNT | The numeric value for that stat |

**Lookup Table:**
```
SymWarehouse.Lookup.digitalstats
```
Contains friendly descriptions for each stat code.

---

## Key Stat Codes for Board Report

### NEW Digital Banking Platform (v64) - PRIMARY FOCUS

| Stat Code | Description | Example (Dec 2025) |
|-----------|-------------|-------------------|
| **NewMthUsr** | Monthly Active Users | 112,496 |
| **NewActUsr** | Active Users (120 day) | 109,000 (frozen since Jul 2025) |
| **NewLogins** | Total Monthly Logins | 2,161,336 |
| **NewRdcCount** | Remote Deposit Count | 31,647 |

**IMPORTANT:** Use `NewMthUsr`, NOT `NewDBmthusr` (incorrect column name in some reports)

### Bill Pay & Transfers

| Stat Code | Description | Example |
|-----------|-------------|---------|
| **BpMthUsr** | Bill Pay Monthly Users | 10,860 |
| **BpActUsr** | Bill Pay Active Users (120d) | - |
| **A2aMthUsr** | A2A Share Monthly Users | 4,407 |
| **A2aActUsr** | A2A Share Active Users | - |
| **A2aLoanMthUsr** | A2A Loan Monthly Users | - |
| **PinMthUsr** | PayItNow Monthly Users | 1,422 |
| **PinActUsr** | PayItNow Active Users | - |

### Card Controls (New Digital Platform)

| Stat Code | Description |
|-----------|-------------|
| **NewActCnt** | Cards with Active Status |
| **NewBlkCnt** | Cards Blocked |
| **NewTmpBlkCnt** | Cards Temporarily Blocked |
| **NewTrvlCnt** | Travel Notifications (Always 0 - not tracked) |

### Mobile Wallet Statistics

| Stat Code | Description |
|-----------|-------------|
| **ApCrMthUsr** | Apple Pay Credit Monthly Users |
| **ApDbtMthUsr** | Apple Pay Debit Monthly Users |
| **GgCrMthUsr** | Google Pay Credit Monthly Users |
| **GgDbtMthUsr** | Google Pay Debit Monthly Users |
| **SmCrMthUsr** | Samsung Pay Credit Monthly Users |
| **SmDbtMthUsr** | Samsung Pay Debit Monthly Users |
| **PpMthUsr** | PayPal Monthly Users |

### App Store Ratings

| Stat Code | Description |
|-----------|-------------|
| **NewMobAppRtgAp** | New Platform iOS App Rating |
| **NewMobAppRvwsAp** | New Platform iOS Review Count |
| **NewMobAppRtgAn** | New Platform Android Rating |
| **NewMobAppRvwsAn** | New Platform Android Review Count |

### Legacy Stats (Historical Reference Only - Show 0)

| Stat Code | Description |
|-----------|-------------|
| OlbMthUsr | Legacy OLB Monthly Users |
| OlbActUsr | Legacy OLB Active Users |
| OlbLogins | Legacy OLB Logins |
| MobMthUsr | Legacy Mobile Monthly Users |
| MobActUsr | Legacy Mobile Active Users |
| MobLogins | Legacy Mobile Logins |

---

## Production SQL Queries

### 1. Monthly Stats for Board Report (13-Month Trend)

```sql
USE [SymWarehouse]

DECLARE @asofdate DATE = GETDATE()
DECLARE @startdate DATE = master.dbo.ufn_LastDayOfMonth(DATEADD(mm, -12, @asofdate), 'c')

-- New Digital Banking Monthly Users
SELECT
    d.digitalstat,
    d.description,
    s.AsOfDate,
    s.[COUNT]
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewMthUsr'
ORDER BY s.AsOfDate DESC
```

### 2. All Key Digital Banking Stats (Single Month)

```sql
DECLARE @reportMonth DATE = '2025-12-31'

SELECT
    d.digitalstat,
    d.description,
    s.AsOfDate,
    s.[COUNT]
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate = @reportMonth
AND s.digitalstat IN (
    'NewMthUsr',      -- Monthly Users
    'NewActUsr',      -- Active Users (120d)
    'NewLogins',      -- Total Logins
    'NewRdcCount',    -- Remote Deposits
    'BpMthUsr',       -- Bill Pay Monthly
    'A2aMthUsr',      -- A2A Share Monthly
    'PinMthUsr'       -- PayItNow Monthly
)
ORDER BY d.sortorder
```

### 3. Enrollment Count (v64 Only)

```sql
-- Total Active Enrollments in New Digital Banking
SELECT COUNT(DISTINCT ParentAccount) AS TotalEnrollments
FROM SymWarehouse.TrackingAccount.v64_OnlineBankingTracking WITH (NOLOCK)
WHERE EXPIREDATE IS NULL
```

### 4. Monthly New Enrollments

```sql
DECLARE @ReportMonth DATE = '2025-12-01'
DECLARE @ReportMonthEnd DATE = '2025-12-31'

SELECT COUNT(DISTINCT USERCHAR1) AS NewEnrollments
FROM [Prod_EDS].[EDSDB].[Report].[TRACKING] WITH (NOLOCK)
WHERE OdsDeleteFlag = 0
AND TYPE = 64
AND EXPIREDATE IS NULL
AND CREATIONDATE >= @ReportMonth
AND CREATIONDATE <= @ReportMonthEnd
```

### 5. Penetration Rate Calculation

```sql
DECLARE @reportMonth DATE = '2025-12-31'

-- Digital Banking Penetration (Monthly Users / Total Members)
SELECT
    s1.AsOfDate,
    CAST(s.[COUNT] AS NUMERIC(10,2)) / s1.[COUNT] AS DigitalPenetration
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s1
    ON s.AsOfDate = s1.AsOfDate
    AND s1.digitalstat = 'MbrCnt'
WHERE s.AsOfDate = @reportMonth
AND s.digitalstat = 'NewMthUsr'
```

### 6. 13-Month Trend Report (Complete)

```sql
USE [SymWarehouse]

DECLARE @asofdate DATE = GETDATE()
DECLARE @startdate DATE = master.dbo.ufn_LastDayOfMonth(DATEADD(mm, -12, @asofdate), 'c')

SELECT
    d.digitalstat,
    d.description,
    d.shortdescription,
    d.category,
    s.AsOfDate,
    s.[COUNT]
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat IN (
    -- Core Usage
    'MbrCnt',
    'NewMthUsr',
    'NewActUsr',
    'NewLogins',
    'NewRdcCount',
    -- Transfers
    'BpMthUsr',
    'BpActUsr',
    'A2aMthUsr',
    'A2aActUsr',
    'A2aLoanMthUsr',
    'A2aLoanActUsr',
    'PinMthUsr',
    'PinActUsr',
    -- Card Controls
    'NewActCnt',
    'NewBlkCnt',
    'NewTmpBlkCnt',
    'NewTrvlCnt'
)
ORDER BY d.sortorder, s.AsOfDate DESC
```

---

## Known Data Issues

| Issue | Status | Notes |
|-------|--------|-------|
| **NewActUsr frozen at 109,000** | Since Jul 2025 | DBA investigation needed - value not updating |
| **NewTrvlCnt always 0** | By design | Travel notifications not tracked in new platform |
| **Legacy OLB/Mob stats = 0** | Expected | All users migrated to v64 |
| **Stored proc not found** | Confirmed | GetDigitalServicesMetrics13Months doesn't exist - use underlying query directly |

---

## Removed Queries (No Longer Needed)

The following are NOT needed since v96 Jwaala migration is complete:

- v96_JwaalaOnlineBanking table joins
- "Truly New" vs "Legacy" split calculations
- 25% hardcoded percentage splits
- Legacy OLB/Mob queries (kept for historical reference but return 0)

---

## Data Validation Rules

1. **Active Users >= Monthly Users** (Normally)
   - Current anomaly: NewActUsr (109,000) < NewMthUsr (112,496)
   - This indicates the 120-day calculation is frozen

2. **No NULL values** for core metrics
   - NewMthUsr, NewLogins, NewRdcCount should never be NULL

3. **Division by Zero Protection**
   - Always use NULLIF or ISNULL when calculating percentages:
   ```sql
   CAST(s.[COUNT] AS NUMERIC(10,2)) / NULLIF(s1.[COUNT], 0)
   ```

---

## Report Sources

- **Underlying Query:** `C:\Users\kgreeven\Downloads\Underlying query for GetDigitalServicesMetrics13Months.sql`
- **RDL Report:** `C:\Users\kgreeven\Desktop\DB Exploxer\DigitalServicesMetricsOverYear(1).rdl`
- **Connection Module:** `C:\Users\kgreeven\Desktop\DB Exploxer\dwha_connection.py`

---

## Change Log

| Date | Change |
|------|--------|
| 2026-01-21 | Initial documentation - removed v96 legacy references, documented correct stat codes |
