/*
================================================================================
DIGITAL SERVICES METRICS REPORT - REORGANIZED SQL QUERIES
================================================================================
Version: 3.0 (Reorganized per updates.pdf annotations)
Updated: 2026-01-21
Database: DWHA / SymWarehouse

CHANGES FROM PREVIOUS VERSION:
- Section 1: Core Membership with FIXED enrollment query (v64_OnlineBankingTracking)
- Section 2: New Digital Banking moved to TOP (PRIMARY)
- Sections 3-10: Bill Pay, A2A, Mobile Wallets, PayItNow, Card Controls
- Section 11: Funded Loans by Origination Channel
- REMOVED: Audio Banking, PayPal, Mobile Coast Into Cash
- LEGACY: All sunset metrics moved to end of report

All queries use NOLOCK hints for performance.
================================================================================
*/

USE [SymWarehouse]
GO

-- ============================================================================
-- VARIABLE DECLARATIONS
-- ============================================================================

DECLARE @asofdate DATE = GETDATE()
DECLARE @startdate DATE = master.dbo.ufn_LastDayOfMonth(DATEADD(mm, -12, @asofdate), 'c')
DECLARE @MonthStart DATE = DATEADD(MONTH, DATEDIFF(MONTH, 0, @asofdate) - 1, 0)
DECLARE @MonthEnd DATE = EOMONTH(@MonthStart)

-- ============================================================================
-- SECTION 1: CORE MEMBERSHIP (TOP OF REPORT)
-- ============================================================================

-- 1.1 Total Open Accounts (MbrCnt)
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    5 AS sortorder,
    's' AS shading
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MbrCnt'

-- 1.2 Total Enrolled in Digital Banking (FIXED - v64 only)
-- NOTE: This is a calculated field from v64_OnlineBankingTracking
UNION
SELECT
    'EnrolledCnt' AS digitalstat,
    'Total Enrolled in Digital Banking' AS description,
    'Membership' AS category,
    'Membership' AS subcategory,
    6 AS sortorderold,
    6 AS sortorder,
    'Mbr' AS unit,
    s1.AsOfDate,
    (SELECT COUNT(DISTINCT ParentAccount)
     FROM SymWarehouse.TrackingAccount.v64_OnlineBankingTracking WITH (NOLOCK)
     WHERE EXPIREDATE IS NULL) AS cnt,
    'c' AS FormatCode,
    6 AS sortorder2,
    's' AS shading
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
WHERE s1.AsOfDate BETWEEN @startdate AND @asofdate
AND s1.digitalstat = 'MbrCnt'

-- 1.3 Monthly New Enrollments (NEW)
-- NOTE: Query against TRACKING table for new enrollments
UNION
SELECT
    'NewEnrollCnt' AS digitalstat,
    'Monthly New Enrollments' AS description,
    'Membership' AS category,
    'Membership' AS subcategory,
    7 AS sortorderold,
    7 AS sortorder,
    'Mbr' AS unit,
    s1.AsOfDate,
    (SELECT COUNT(DISTINCT USERCHAR1)
     FROM [Prod_EDS].[EDSDB].[Report].[TRACKING] WITH (NOLOCK)
     WHERE OdsDeleteFlag = 0 AND TYPE = 64 AND EXPIREDATE IS NULL
     AND CREATIONDATE >= @MonthStart AND CREATIONDATE <= @MonthEnd) AS cnt,
    'c' AS FormatCode,
    7 AS sortorder2,
    's' AS shading
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
WHERE s1.AsOfDate BETWEEN @startdate AND @asofdate
AND s1.digitalstat = 'MbrCnt'

-- 1.4 Digital Banking Penetration % (NEW - Enrolled/Total Members)
UNION
SELECT
    'DigiPenPct' AS digitalstat,
    'Digital Banking Penetration %' AS description,
    'Membership' AS category,
    'Membership' AS subcategory,
    8 AS sortorderold,
    8 AS sortorder,
    'Pct' AS unit,
    s1.AsOfDate,
    CAST(
        (SELECT COUNT(DISTINCT ParentAccount)
         FROM SymWarehouse.TrackingAccount.v64_OnlineBankingTracking WITH (NOLOCK)
         WHERE EXPIREDATE IS NULL) AS NUMERIC(10,2)
    ) / NULLIF(s1.[COUNT], 0) AS cnt,
    'p' AS FormatCode,
    8 AS sortorder2,
    's' AS shading
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
WHERE s1.AsOfDate BETWEEN @startdate AND @asofdate
AND s1.digitalstat = 'MbrCnt'

-- 1.5 Account Checking Penetration (monthly point-in-time)
UNION
SELECT
    'ChkgPenPct' AS digitalstat,
    'Account Checking Penetration' AS description,
    'Membership' AS category,
    'Membership' AS subcategory,
    9 AS sortorderold,
    9 AS sortorder,
    'Pct' AS unit,
    s1.AsOfDate,
    CAST(s2.[COUNT] AS NUMERIC(10,2)) / NULLIF(s1.[COUNT], 0) AS cnt,
    'p' AS FormatCode,
    9 AS sortorder2,
    's' AS shading
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s2 WITH (NOLOCK)
    ON s2.AsOfDate = s1.AsOfDate AND s2.digitalstat = 'ChkgCnt'
WHERE s1.AsOfDate BETWEEN @startdate AND @asofdate
AND s1.digitalstat = 'MbrCnt'

-- 1.6 Accounts With Checking (ChkgCnt)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    10 AS sortorder,
    's' AS shading
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ChkgCnt'

-- ============================================================================
-- SECTION 2: NEW DIGITAL BANKING (PRIMARY - TOP)
-- ============================================================================

-- 2.1 New Digital Banking Penetration %
UNION
SELECT
    'NewPct',
    'New Digital Banking Usage for all Accounts',
    'Digital',
    'Digital',
    76,
    76,
    'Acct',
    s1.AsOfDate,
    CAST(ISNULL(s.[COUNT], 0) AS NUMERIC(10,2)) / NULLIF(s1.[COUNT], 0) AS Penetration,
    'p' AS FormatCode,
    20,
    's'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
LEFT JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
    ON s.AsOfDate = s1.AsOfDate AND s.digitalstat = 'NewMthUsr'
WHERE s1.AsOfDate BETWEEN @startdate AND @asofdate
AND s1.digitalstat = 'MbrCnt'

-- 2.2 Users For Month (1)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    21,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewMthUsr'

-- 2.3 Active Users (2) - NOTE: Known frozen at 109,000 since Jul 2025
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    22,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewActUsr'

-- 2.4 Logins
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    23,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewLogins'

-- 2.5 Mobile Remote Deposits (will come from Ensenta)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    24,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewRdcCount'

-- 2.6 Mobile Apple App Rating (3)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'd' AS FormatCode,
    25,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewMobAppRtgAp'

-- 2.7 Total Mobile Apple App Reviews
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    26,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewMobAppRvwsAp'

-- 2.8 Mobile Android App Rating (3)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'd' AS FormatCode,
    27,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewMobAppRtgAn'

-- 2.9 Total Mobile Android App Reviews
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    28,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewMobAppRvwsAn'

-- ============================================================================
-- SECTION 3: BILL PAY
-- ============================================================================

-- 3.1 Bill Pay Usage for all Accounts
UNION
SELECT
    'BpAllPct',
    'Bill Pay Usage for all Accounts',
    'BillPay',
    'BillPay',
    105,
    105,
    'Acct',
    s.AsOfDate,
    CAST(s.[COUNT] AS NUMERIC(10,2)) / NULLIF(s1.[COUNT], 0) AS Penetration,
    'p' AS FormatCode,
    30,
    's'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
    ON s.AsOfDate = s1.AsOfDate AND s1.digitalstat = 'MbrCnt'
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'BpMthUsr'

-- 3.2 Bill Pay Usage for Accts with Checking (Rolling 12-month, person-centric)
UNION
SELECT
    'BpChkPct',
    'Bill Pay Usage for Accts with Checking',
    'BillPay',
    'BillPay',
    110,
    110,
    'Acct',
    s.AsOfDate,
    CAST(s.[COUNT] AS NUMERIC(10,2)) / NULLIF(s1.[COUNT], 0) AS Penetration,
    'p' AS FormatCode,
    31,
    's'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
    ON s.AsOfDate = s1.AsOfDate AND s1.digitalstat = 'ChkgCnt'
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'BpMthUsr'

-- 3.3 Bill Pay Users For Month (1)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    32,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'BpMthUsr'

-- 3.4 Bill Pay Active Users (2)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    33,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'BpActUsr'

-- ============================================================================
-- SECTION 4: A2A SHARE TRANSFERS
-- ============================================================================

-- 4.1 A2A (Share) Usage for all Accts (monthly count)
UNION
SELECT
    'A2aAllPct',
    'A2A (Share) Usage for all Accounts',
    'A2A',
    'A2A Share',
    130,
    130,
    'Acct',
    s.AsOfDate,
    CAST(s.[COUNT] AS NUMERIC(10,2)) / NULLIF(s1.[COUNT], 0) AS Penetration,
    'p' AS FormatCode,
    40,
    's'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
    ON s.AsOfDate = s1.AsOfDate AND s1.digitalstat = 'MbrCnt'
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aMthUsr'

-- 4.2 A2A (Share) Usage for Accts with Chkg
UNION
SELECT
    'A2aChkPct',
    'A2A (Share) Usage for Accts with Checking',
    'A2A',
    'A2A Share',
    135,
    135,
    'Acct',
    s.AsOfDate,
    CAST(s.[COUNT] AS NUMERIC(10,2)) / NULLIF(s1.[COUNT], 0) AS Penetration,
    'p' AS FormatCode,
    41,
    's'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
    ON s.AsOfDate = s1.AsOfDate AND s1.digitalstat = 'ChkgCnt'
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aMthUsr'

-- 4.3 A2A (Share) Users For Month (1)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    42,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aMthUsr'

-- 4.4 A2A (Share) Active Users (2)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    43,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aActUsr'

-- ============================================================================
-- SECTION 5: A2A LOAN TRANSFERS
-- ============================================================================

-- 5.1 A2A (Loan) Usage for all Accts (monthly count)
UNION
SELECT
    'A2aLoanAllPct',
    'A2A (Loan) Usage for all Accounts',
    'A2A',
    'A2A Loan',
    145,
    145,
    'Acct',
    s.AsOfDate,
    CAST(s.[COUNT] AS NUMERIC(10,2)) / NULLIF(s1.[COUNT], 0) AS Penetration,
    'p' AS FormatCode,
    50,
    's'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
    ON s.AsOfDate = s1.AsOfDate AND s1.digitalstat = 'MbrCnt'
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aLoanMthUsr'

-- 5.2 A2A (Loan) Usage for Accts with Chkg
UNION
SELECT
    'A2aLoanChkPct',
    'A2A (Loan) Usage for Accts with Checking',
    'A2A',
    'A2A Loan',
    146,
    146,
    'Acct',
    s.AsOfDate,
    CAST(s.[COUNT] AS NUMERIC(10,2)) / NULLIF(s1.[COUNT], 0) AS Penetration,
    'p' AS FormatCode,
    51,
    's'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
    ON s.AsOfDate = s1.AsOfDate AND s1.digitalstat = 'ChkgCnt'
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aLoanMthUsr'

-- 5.3 A2A (Loan) Users For Month (1)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    52,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aLoanMthUsr'

-- 5.4 A2A (Loan) Active Users (2)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    53,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aLoanActUsr'

-- ============================================================================
-- SECTION 6: APPLE PAY
-- ============================================================================

-- 6.1 ApplePay Credit Card Users For Month (1)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    60,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApCrMthUsr'

-- 6.2 ApplePay Credit Card Active Users (2)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    61,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApCrActUsr'

-- 6.3 ApplePay Unique Credit Cards Activated
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    62,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApCrMthCard'

-- 6.4 ApplePay Debit Card Users For Month (1)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    63,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApDbtMthUsr'

-- 6.5 ApplePay Debit Card Active Users (2)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    64,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApDbtActUsr'

-- 6.6 ApplePay Unique Debit Cards Activated
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    65,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApDbtMthCard'

-- ============================================================================
-- SECTION 7: GOOGLE PAY
-- ============================================================================

-- 7.1 GooglePay Credit Card Users For Month (1)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    70,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgCrMthUsr'

-- 7.2 GooglePay Credit Card Active Users (2)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    71,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgCrActUsr'

-- 7.3 GooglePay Unique Credit Cards Activated
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    72,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgCrMthCard'

-- 7.4 GooglePay Debit Card Users For Month (1)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    73,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgDbtMthUsr'

-- 7.5 GooglePay Debit Card Active Users (2)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    74,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgDbtActUsr'

-- 7.6 GooglePay Unique Debit Cards Activated
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    75,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgDbtMthCard'

-- ============================================================================
-- SECTION 8: SAMSUNG PAY
-- ============================================================================

-- 8.1 SamsungPay Credit Card Users For Month (1)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    80,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'SmCrMthUsr'

-- 8.2 SamsungPay Credit Card Active Users (2)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    81,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'SmCrActUsr'

-- 8.3 SamsungPay Unique Credit Cards Activated
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    82,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'SmCrMthCard'

-- 8.4 SamsungPay Debit Card Users For Month (1)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    83,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'SmDbtMthUsr'

-- 8.5 SamsungPay Debit Card Active Users (2)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    84,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'SmDbtActUsr'

-- 8.6 SamsungPay Unique Debit Cards Activated
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    85,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'SmDbtMthCard'

-- ============================================================================
-- SECTION 9: PAYITNOW
-- ============================================================================

-- 9.1 PayItNow Users For Month (1) - monthly basis
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    90,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'PinMthUsr'

-- 9.2 PayItNow Active Users (2)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    91,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'PinActUsr'

-- ============================================================================
-- SECTION 10: NEW DIGITAL CARD CONTROLS
-- ============================================================================

-- 10.1 Digital Card Activation Count
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    100,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewActCnt'

-- 10.2 Digital Card Block Count (monthly)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    101,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewBlkCnt'

-- 10.3 Digital Temp Card Block Count (monthly)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    102,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewTmpBlkCnt'

-- ============================================================================
-- SECTION 11: FUNDED LOANS BY ORIGINATION CHANNEL
-- NOTE: This section typically comes from Meridian Link, included as placeholder
-- ============================================================================

-- Placeholder for Funded Loans - typically sourced from Meridian Link reports
-- Online (Excluding Mobile), Online Banking, Mobile, In Branch, MSC, Total
-- These metrics are usually pulled from a separate data source

-- ============================================================================
-- ==================== LEGACY SECTIONS (MOVED TO END) ====================
-- ============================================================================

-- ============================================================================
-- LEGACY SECTION A: Legacy OLB Banking (Sunset - All showing 0%)
-- ============================================================================

-- Legacy OLB Banking Usage
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    900,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'OlbMthUsr'

-- OLB Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    901,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'OlbActUsr'

-- OLB Logins
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    902,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'OlbLogins'

-- ============================================================================
-- LEGACY SECTION B: Legacy Mobile Banking (Sunset - All showing 0%)
-- ============================================================================

-- Legacy Mobile Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    910,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MobMthUsr'

-- Legacy Mobile Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    911,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MobActUsr'

-- Legacy Mobile Logins
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    912,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MobLogins'

-- Legacy Mobile Remote Deposits
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    913,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'RdcCount'

-- Legacy Mobile Apple App Rating
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'd' AS FormatCode,
    914,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MobAppRtgApp'

-- Legacy Mobile Apple App Reviews
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    915,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MobAppRvwsApp'

-- Legacy Mobile Android App Rating
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'd' AS FormatCode,
    916,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MobAppRtgAnd'

-- Legacy Mobile Android App Reviews
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    917,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MobAppRvwsAnd'

-- ============================================================================
-- LEGACY SECTION C: Legacy OLB Card Controls (Sunset)
-- ============================================================================

-- OLB Card Activation Count
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    920,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'OlbActCnt'

-- OLB Card Block Count
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    921,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'OlbBlkCnt'

-- OLB Travel Notification Count
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    922,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'OlbTrvlCnt'

-- ============================================================================
-- LEGACY SECTION D: Legacy Mobile Card Controls (Sunset)
-- ============================================================================

-- Mobile Card Activation Count
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    930,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MobActCnt'

-- Mobile Card Block Count
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    931,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MobBlkCnt'

-- Mobile Temp Card Block Count
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    932,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MobTmpBlkCnt'

-- Mobile Travel Notification Count
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    933,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'MobTrvlCnt'

-- ============================================================================
-- LEGACY SECTION E: Coast Money Manager (Product Sunset)
-- ============================================================================

-- CMM Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    940,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmMthUsr'

-- CMM Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    941,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmActUsr'

-- CMM OLB Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    942,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmOLBMthUsr'

-- CMM OLB Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    943,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmOLBActUsr'

-- CMM OLB Sessions
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    944,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmOLBLogins'

-- CMM Mobile Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    945,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmMobMthUsr'

-- CMM Mobile Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    946,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmMobActUsr'

-- CMM Mobile Sessions
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    947,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmMobLogins'

-- CMM New Signups
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    948,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmNewSignup'

-- CMM OLB New Signups
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    949,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmOLBNewSignup'

-- CMM Mobile New Signups
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    950,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmMobNewSignup'

-- CMM Users with Aggregated Account
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    951,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmUsrAggAct'

-- CMM Apple App Rating
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'd' AS FormatCode,
    952,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmAppRtgApp'

-- CMM Apple App Reviews
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    953,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmAppRvwsApp'

-- CMM Android App Rating
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'd' AS FormatCode,
    954,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmAppRtgAnd'

-- CMM Android App Reviews
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    955,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'CmmAppRvwsAnd'

ORDER BY sortorder, AsOfDate DESC

GO

/*
================================================================================
STANDALONE ENROLLMENT QUERIES
================================================================================
*/

-- Query 1: Total Enrolled Members (v64 only) - FIXED
SELECT COUNT(DISTINCT ParentAccount) AS TotalEnrolled
FROM SymWarehouse.TrackingAccount.v64_OnlineBankingTracking WITH (NOLOCK)
WHERE EXPIREDATE IS NULL

GO

-- Query 2: Monthly New Enrollments
DECLARE @MonthStart DATE = DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) - 1, 0)
DECLARE @MonthEnd DATE = EOMONTH(@MonthStart)

SELECT COUNT(DISTINCT USERCHAR1) AS NewEnrollments
FROM [Prod_EDS].[EDSDB].[Report].[TRACKING] WITH (NOLOCK)
WHERE OdsDeleteFlag = 0
AND TYPE = 64
AND EXPIREDATE IS NULL
AND CREATIONDATE >= @MonthStart
AND CREATIONDATE <= @MonthEnd

GO

/*
================================================================================
ACTIVE USERS (120-DAY) - VERIFICATION QUERY
================================================================================
This query is run against the MySQL dbxdb database (fraudmonitor table)
to get the REAL active user count, replacing the frozen NewActUsr stat.

The NewActUsr stat from DigitalChannelsMemberStatsSummary has been frozen
at ~109,000 since July 2025 due to upstream ETL issues.

This verification query should return a value > 112,496 (NewMthUsr)
since 120-day active users should exceed monthly users.

Expected result: ~115,000 - 130,000 (dynamic, changes daily)
================================================================================
*/

-- MySQL Query (run against dbxdb on infinity-9ix.calcoastcu.org:3306)
-- NOTE: This is MySQL syntax, not T-SQL
/*
SELECT COUNT(DISTINCT masterMembership) AS Active120DayUsers
FROM fraudmonitor
WHERE activityDate >= DATE_SUB(NOW(), INTERVAL 120 DAY)
AND eventCategory = 'LoginSuccessful';
*/

-- Equivalent Python code (from board_report_export.py):
/*
from db_connection import get_connection
from datetime import datetime, timedelta

conn = get_connection()
cursor = conn.cursor()
cutoff_date = datetime.now() - timedelta(days=120)

query = """
SELECT COUNT(DISTINCT masterMembership) AS Active120DayUsers
FROM fraudmonitor
WHERE activityDate >= %s
AND eventCategory = 'LoginSuccessful'
"""

cursor.execute(query, (cutoff_date,))
result = cursor.fetchone()
print(f"Active Users (120-day): {result[0]:,}")
*/

GO

/*
================================================================================
REMOVED METRICS (NO LONGER IN REPORT)
================================================================================
These metrics have been REMOVED from the report entirely:

1. Audio Banking (AudMthUsr, AudActUsr, AudLogins) - No longer tracked
2. PayPal (PpMthUsr, PpActUsr) - Not accurately calculated
3. Mobile Coast Into Cash Referrals (CICMthRefCnt) - Not being tracked, no data
4. Mobile Coast Into Cash New Accounts (CICNewUserCnt) - Not being tracked, no data
================================================================================
*/
