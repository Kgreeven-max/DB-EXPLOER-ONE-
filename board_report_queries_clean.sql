/*
================================================================================
DIGITAL BANKING BOARD REPORT - CLEAN SQL QUERIES
================================================================================
Version: 2.0 (v64 Only - Legacy Removed)
Updated: 2026-01-21
Database: DWHA / SymWarehouse

IMPORTANT: v96 (Jwaala Legacy) is NO LONGER NEEDED
           All users have migrated to v64 (new digital banking platform)

All queries use NOLOCK hints for performance.
================================================================================
*/

USE [SymWarehouse]
GO

-- ============================================================================
-- SECTION 1: VARIABLE DECLARATIONS
-- ============================================================================

DECLARE @asofdate DATE = GETDATE()
DECLARE @startdate DATE = master.dbo.ufn_LastDayOfMonth(DATEADD(mm, -12, @asofdate), 'c')

-- ============================================================================
-- SECTION 2: TOTAL MEMBERSHIP COUNT
-- ============================================================================

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

-- ============================================================================
-- SECTION 3: NEW DIGITAL BANKING PLATFORM STATS (PRIMARY)
-- ============================================================================

-- Penetration Rate
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
    76,
    's'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
LEFT JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
    ON s.AsOfDate = s1.AsOfDate
    AND s.digitalstat = 'NewMthUsr'
WHERE s1.AsOfDate BETWEEN @startdate AND @asofdate
AND s1.digitalstat = 'MbrCnt'

-- Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    77,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewMthUsr'

-- Active Users (120 day) - NOTE: Known to be frozen since Jul 2025
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    78,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewActUsr'

-- Total Logins
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    79,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewLogins'

-- Remote Deposit Count
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
AND s.digitalstat = 'NewRdcCount'

-- ============================================================================
-- SECTION 4: APP STORE RATINGS (NEW PLATFORM)
-- ============================================================================

-- iOS Rating
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'd' AS FormatCode,
    81,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewMobAppRtgAp'

-- iOS Review Count
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
AND s.digitalstat = 'NewMobAppRvwsAp'

-- Android Rating
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'd' AS FormatCode,
    83,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewMobAppRtgAn'

-- Android Review Count
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
AND s.digitalstat = 'NewMobAppRvwsAn'

-- ============================================================================
-- SECTION 5: BILL PAY
-- ============================================================================

-- Penetration (All Members)
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
    105,
    's'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
    ON s.AsOfDate = s1.AsOfDate AND s1.digitalstat = 'MbrCnt'
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'BpMthUsr'

-- Penetration (Checking Accounts Only)
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
    110,
    's'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.History.DigitalChannelsMemberStatsSummary s1 WITH (NOLOCK)
    ON s.AsOfDate = s1.AsOfDate AND s1.digitalstat = 'ChkgCnt'
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'BpMthUsr'

-- Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    115,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'BpMthUsr'

-- Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    120,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'BpActUsr'

-- ============================================================================
-- SECTION 6: A2A SHARE TRANSFERS
-- ============================================================================

-- Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    140,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aMthUsr'

-- Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    145,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aActUsr'

-- ============================================================================
-- SECTION 7: A2A LOAN TRANSFERS
-- ============================================================================

-- Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    149,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aLoanMthUsr'

-- Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    150,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'A2aLoanActUsr'

-- ============================================================================
-- SECTION 8: PAYITNOW
-- ============================================================================

-- Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    182,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'PinMthUsr'

-- Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    183,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'PinActUsr'

-- ============================================================================
-- SECTION 9: CARD CONTROLS (NEW DIGITAL PLATFORM)
-- ============================================================================

-- Active Cards
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    196,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewActCnt'

-- Blocked Cards
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    197,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewBlkCnt'

-- Temporarily Blocked Cards
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    198,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewTmpBlkCnt'

-- Travel Notifications (NOTE: Always returns 0 - not tracked in new platform)
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    199,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'NewTrvlCnt'

-- ============================================================================
-- SECTION 10: MOBILE WALLETS - APPLE PAY
-- ============================================================================

-- Credit Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    152,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApCrMthUsr'

-- Credit Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    153,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApCrActUsr'

-- Credit Monthly Cards
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    154,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApCrMthCard'

-- Debit Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    156,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApDbtMthUsr'

-- Debit Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    157,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApDbtActUsr'

-- Debit Monthly Cards
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    158,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'ApDbtMthCard'

-- ============================================================================
-- SECTION 11: MOBILE WALLETS - GOOGLE PAY
-- ============================================================================

-- Credit Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    160,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgCrMthUsr'

-- Credit Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    161,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgCrActUsr'

-- Credit Monthly Cards
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    162,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgCrMthCard'

-- Debit Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    164,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgDbtMthUsr'

-- Debit Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    165,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgDbtActUsr'

-- Debit Monthly Cards
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    166,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'GgDbtMthCard'

-- ============================================================================
-- SECTION 12: MOBILE WALLETS - SAMSUNG PAY
-- ============================================================================

-- Credit Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    168,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'SmCrMthUsr'

-- Debit Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    172,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'SmDbtMthUsr'

-- ============================================================================
-- SECTION 13: PAYPAL
-- ============================================================================

-- Monthly Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    180,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'PpMthUsr'

-- Active Users
UNION
SELECT
    d.*,
    s.AsOfDate,
    s.[COUNT] AS cnt,
    'c' AS FormatCode,
    181,
    'n'
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate BETWEEN @startdate AND @asofdate
AND s.digitalstat = 'PpActUsr'

ORDER BY sortorder, AsOfDate DESC

GO

/*
================================================================================
STANDALONE QUERIES
================================================================================
*/

-- Query 1: Get Enrollment Count (v64 Only)
SELECT COUNT(DISTINCT ParentAccount) AS TotalEnrollments
FROM SymWarehouse.TrackingAccount.v64_OnlineBankingTracking WITH (NOLOCK)
WHERE EXPIREDATE IS NULL

GO

-- Query 2: Get Monthly New Enrollments
DECLARE @ReportMonth DATE = DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()) - 1, 0)
DECLARE @ReportMonthEnd DATE = EOMONTH(@ReportMonth)

SELECT COUNT(DISTINCT USERCHAR1) AS NewEnrollments
FROM [Prod_EDS].[EDSDB].[Report].[TRACKING] WITH (NOLOCK)
WHERE OdsDeleteFlag = 0
AND TYPE = 64
AND EXPIREDATE IS NULL
AND CREATIONDATE >= @ReportMonth
AND CREATIONDATE <= @ReportMonthEnd

GO

-- Query 3: Quick Key Stats Check (Single Month)
DECLARE @reportMonth DATE = EOMONTH(DATEADD(MONTH, -1, GETDATE()))

SELECT
    s.digitalstat,
    d.description,
    s.[COUNT]
FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
JOIN SymWarehouse.Lookup.digitalstats d ON d.digitalstat = s.digitalstat
WHERE s.AsOfDate = @reportMonth
AND s.digitalstat IN (
    'NewMthUsr',
    'NewActUsr',
    'NewLogins',
    'NewRdcCount',
    'BpMthUsr',
    'A2aMthUsr',
    'PinMthUsr'
)
ORDER BY d.sortorder

GO

/*
================================================================================
REMOVED QUERIES (NO LONGER NEEDED)
================================================================================
The following were removed because v96 Jwaala migration is complete:

- v96_JwaalaOnlineBanking table joins
- "Truly New" vs "Legacy" split calculations
- 25% hardcoded percentage splits
- OlbMthUsr, OlbActUsr, OlbLogins (Legacy OLB - now show 0)
- MobMthUsr, MobActUsr, MobLogins (Legacy Mobile - now show 0)
================================================================================
*/
