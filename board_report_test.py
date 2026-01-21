#!/usr/bin/env python3
"""
Digital Banking Board Report - SQL Query Validation Tests

This script validates the SQL queries used in the board report by:
1. Testing connectivity to DWHA
2. Verifying all required stat codes exist
3. Checking for data anomalies (NULL values, frozen data)
4. Validating data relationships
5. Generating a test report

Usage: py board_report_test.py
"""

from datetime import datetime, timedelta
from dwha_connection import get_dwha_connection


def test_connection():
    """Test 1: Verify DWHA connection"""
    print("\n" + "="*60)
    print("TEST 1: DWHA Connection Test")
    print("="*60)
    try:
        conn = get_dwha_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"[PASS] Connected to DWHA")
        print(f"       Server: {version[:60]}...")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        return False


def test_summary_table_exists():
    """Test 2: Verify summary table exists and has recent data"""
    print("\n" + "="*60)
    print("TEST 2: Summary Table Verification")
    print("="*60)
    try:
        conn = get_dwha_connection()
        cursor = conn.cursor()

        query = """
        SELECT TOP 1 AsOfDate, COUNT(*) as StatCount
        FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary WITH (NOLOCK)
        GROUP BY AsOfDate
        ORDER BY AsOfDate DESC
        """
        cursor.execute(query)
        row = cursor.fetchone()

        if row:
            latest_date, stat_count = row
            print(f"[PASS] Summary table exists")
            print(f"       Latest data: {latest_date}")
            print(f"       Stats for that month: {stat_count}")

            # Check if data is recent (within last 45 days)
            if isinstance(latest_date, datetime):
                days_old = (datetime.now() - latest_date).days
            else:
                days_old = (datetime.now().date() - latest_date).days

            if days_old > 45:
                print(f"[WARN] Data is {days_old} days old - may need refresh")
        else:
            print("[FAIL] No data found in summary table")
            return False

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_key_stat_codes():
    """Test 3: Verify all required stat codes return data"""
    print("\n" + "="*60)
    print("TEST 3: Key Stat Codes Verification")
    print("="*60)

    required_stats = [
        ('NewMthUsr', 'Monthly Users'),
        ('NewActUsr', 'Active Users (120d)'),
        ('NewLogins', 'Total Logins'),
        ('NewRdcCount', 'Remote Deposits'),
        ('BpMthUsr', 'Bill Pay Monthly'),
        ('A2aMthUsr', 'A2A Share Monthly'),
        ('PinMthUsr', 'PayItNow Monthly'),
        ('MbrCnt', 'Total Members'),
    ]

    try:
        conn = get_dwha_connection()
        cursor = conn.cursor()

        all_passed = True
        results = {}

        for stat_code, description in required_stats:
            query = f"""
            SELECT TOP 1 s.digitalstat, s.AsOfDate, s.[COUNT]
            FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary s WITH (NOLOCK)
            WHERE s.digitalstat = '{stat_code}'
            ORDER BY s.AsOfDate DESC
            """
            cursor.execute(query)
            row = cursor.fetchone()

            if row:
                stat, date, count = row
                results[stat_code] = count
                status = "[PASS]" if count and count > 0 else "[WARN]"
                print(f"{status} {stat_code}: {count:,} ({description})")
                if count is None or count == 0:
                    all_passed = False
            else:
                print(f"[FAIL] {stat_code}: NOT FOUND ({description})")
                all_passed = False
                results[stat_code] = None

        cursor.close()
        conn.close()
        return all_passed, results
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False, {}


def test_data_relationships(stats):
    """Test 4: Validate data relationships"""
    print("\n" + "="*60)
    print("TEST 4: Data Relationship Validation")
    print("="*60)

    issues = []

    # Check: Active Users should normally be >= Monthly Users
    if stats.get('NewActUsr') and stats.get('NewMthUsr'):
        if stats['NewActUsr'] < stats['NewMthUsr']:
            issues.append(f"[WARN] NewActUsr ({stats['NewActUsr']:,}) < NewMthUsr ({stats['NewMthUsr']:,})")
            print(f"[WARN] Active Users < Monthly Users (known frozen issue)")
            print(f"       NewActUsr: {stats['NewActUsr']:,}")
            print(f"       NewMthUsr: {stats['NewMthUsr']:,}")
        else:
            print(f"[PASS] Active Users >= Monthly Users")

    # Check: Monthly users should be less than total members
    if stats.get('NewMthUsr') and stats.get('MbrCnt'):
        if stats['NewMthUsr'] > stats['MbrCnt']:
            issues.append(f"[FAIL] NewMthUsr ({stats['NewMthUsr']:,}) > MbrCnt ({stats['MbrCnt']:,})")
            print(f"[FAIL] Monthly Users > Total Members (impossible)")
        else:
            penetration = (stats['NewMthUsr'] / stats['MbrCnt']) * 100
            print(f"[PASS] Digital penetration: {penetration:.1f}%")

    # Check for reasonable login count
    if stats.get('NewLogins') and stats.get('NewMthUsr'):
        avg_logins = stats['NewLogins'] / stats['NewMthUsr']
        if avg_logins < 1 or avg_logins > 100:
            print(f"[WARN] Unusual avg logins per user: {avg_logins:.1f}")
        else:
            print(f"[PASS] Avg logins per user: {avg_logins:.1f}")

    return len(issues) == 0


def test_frozen_values():
    """Test 5: Check for frozen/stuck values"""
    print("\n" + "="*60)
    print("TEST 5: Frozen Value Detection")
    print("="*60)

    try:
        conn = get_dwha_connection()
        cursor = conn.cursor()

        # Check last 6 months for NewActUsr
        query = """
        SELECT TOP 6 AsOfDate, [COUNT]
        FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary WITH (NOLOCK)
        WHERE digitalstat = 'NewActUsr'
        ORDER BY AsOfDate DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        if rows:
            values = [row[1] for row in rows]
            unique_values = set(values)

            print("NewActUsr - Last 6 months:")
            for date, count in rows:
                print(f"  {date}: {count:,}")

            if len(unique_values) == 1:
                print(f"[WARN] NewActUsr appears FROZEN at {values[0]:,}")
                print("       -> Escalate to DBA for investigation")
            else:
                print(f"[PASS] NewActUsr showing variation ({len(unique_values)} unique values)")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def test_enrollment_count():
    """Test 6: Verify enrollment count from v64 tracking table"""
    print("\n" + "="*60)
    print("TEST 6: Enrollment Count (v64 Only)")
    print("="*60)

    try:
        conn = get_dwha_connection()
        cursor = conn.cursor()

        query = """
        SELECT COUNT(DISTINCT ParentAccount) AS TotalEnrollments
        FROM SymWarehouse.TrackingAccount.v64_OnlineBankingTracking WITH (NOLOCK)
        WHERE EXPIREDATE IS NULL
        """
        cursor.execute(query)
        row = cursor.fetchone()

        if row and row[0]:
            enrollment_count = row[0]
            print(f"[PASS] v64 Active Enrollments: {enrollment_count:,}")

            # Compare with expected range (~147,000)
            if 100000 < enrollment_count < 200000:
                print("       Value is within expected range")
            else:
                print(f"[WARN] Value outside expected range (100k-200k)")

            return True, enrollment_count
        else:
            print("[FAIL] Could not retrieve enrollment count")
            return False, 0

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        print("       (Table may not be accessible)")
        return False, 0


def test_twelve_month_trend():
    """Test 7: Pull 12-month trend for key metrics"""
    print("\n" + "="*60)
    print("TEST 7: 12-Month Trend Analysis")
    print("="*60)

    try:
        conn = get_dwha_connection()
        cursor = conn.cursor()

        query = """
        SELECT
            AsOfDate,
            MAX(CASE WHEN digitalstat = 'NewMthUsr' THEN [COUNT] END) AS MthUsr,
            MAX(CASE WHEN digitalstat = 'NewLogins' THEN [COUNT] END) AS Logins,
            MAX(CASE WHEN digitalstat = 'NewRdcCount' THEN [COUNT] END) AS RDC
        FROM SymWarehouse.History.DigitalChannelsMemberStatsSummary WITH (NOLOCK)
        WHERE digitalstat IN ('NewMthUsr', 'NewLogins', 'NewRdcCount')
        AND AsOfDate >= DATEADD(month, -12, GETDATE())
        GROUP BY AsOfDate
        ORDER BY AsOfDate DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        if rows:
            print(f"{'Month':<12} {'Monthly Users':>14} {'Logins':>14} {'RDC':>10}")
            print("-" * 52)

            prev_mth = None
            issues = []

            for date, mth_usr, logins, rdc in rows:
                date_str = date.strftime('%Y-%m') if hasattr(date, 'strftime') else str(date)[:7]
                mth_str = f"{mth_usr:,}" if mth_usr else "NULL"
                login_str = f"{logins:,}" if logins else "NULL"
                rdc_str = f"{rdc:,}" if rdc else "NULL"
                print(f"{date_str:<12} {mth_str:>14} {login_str:>14} {rdc_str:>10}")

                # Check for NULL values
                if mth_usr is None:
                    issues.append(f"NULL NewMthUsr for {date_str}")

                # Check for unexpected drops (>20%)
                if prev_mth and mth_usr and prev_mth > 0:
                    change = (mth_usr - prev_mth) / prev_mth * 100
                    if change < -20:
                        issues.append(f"Large drop in {date_str}: {change:.1f}%")

                prev_mth = mth_usr

            if issues:
                print("\nIssues detected:")
                for issue in issues:
                    print(f"  [WARN] {issue}")
            else:
                print("\n[PASS] 12-month trend looks healthy")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False


def generate_summary_report(test_results):
    """Generate final test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY REPORT")
    print("="*60)

    passed = sum(1 for r in test_results if r)
    total = len(test_results)

    print(f"\nTests Passed: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
    else:
        print(f"\n[WARNING] {total - passed} test(s) had issues")

    print("\n" + "-"*60)
    print("Known Issues to Monitor:")
    print("-"*60)
    print("1. NewActUsr frozen at 109,000 since Jul 2025 - DBA escalation needed")
    print("2. NewTrvlCnt always 0 - Travel notifications not tracked")
    print("3. Legacy OLB/Mob stats = 0 - Expected (migration complete)")
    print("-"*60)


def main():
    """Run all validation tests"""
    print("\n" + "#"*60)
    print("# DIGITAL BANKING BOARD REPORT - SQL VALIDATION TESTS")
    print(f"# Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#"*60)

    test_results = []

    # Test 1: Connection
    result1 = test_connection()
    test_results.append(result1)

    if not result1:
        print("\n[ABORT] Cannot continue without database connection")
        return

    # Test 2: Summary table
    result2 = test_summary_table_exists()
    test_results.append(result2)

    # Test 3: Key stat codes
    result3, stats = test_key_stat_codes()
    test_results.append(result3)

    # Test 4: Data relationships
    result4 = test_data_relationships(stats)
    test_results.append(result4)

    # Test 5: Frozen values
    result5 = test_frozen_values()
    test_results.append(result5)

    # Test 6: Enrollment count
    result6, _ = test_enrollment_count()
    test_results.append(result6)

    # Test 7: 12-month trend
    result7 = test_twelve_month_trend()
    test_results.append(result7)

    # Generate summary
    generate_summary_report(test_results)


if __name__ == "__main__":
    main()
