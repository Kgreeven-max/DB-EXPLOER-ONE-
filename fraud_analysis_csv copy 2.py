#!/usr/bin/env python3
"""
Fraud Analysis Script with Advanced Risk Scoring
Outputs comprehensive fraud report to CSV with IP geolocation
"""

import pymysql
import pandas as pd
from datetime import datetime, timedelta
import requests
import warnings
import sys
import time

warnings.filterwarnings('ignore')

# Known suspicious email domains
SUSPICIOUS_DOMAINS = [
    'telegmail.com', 'tuta.com', 'proton.me', 'protonmail.com',
    'hi2.in', 'guerrillamail.com', 'temp-mail.org', 'mailinator.com',
    '10minutemail.com', 'throwaway.email', 'yopmail.com', 'maildrop.cc',
    'trashmail.com', 'sharklasers.com', 'guerrillamail.info', 'mail.tm',
    'temp-mail.io', 'mohmal.com', 'dispostable.com', 'fakeinbox.com'
]

# High risk countries
HIGH_RISK_COUNTRIES = [
    'Russia', 'China', 'Nigeria', 'Romania', 'Brazil', 'North Korea',
    'India', 'Indonesia', 'Philippines', 'Vietnam', 'Ukraine', 'Iran'
]

def get_ip_geolocation(ip_address, ip_cache={}):
    """Get geographic information for IP address with caching"""
    # Check cache first
    if ip_address in ip_cache:
        return ip_cache[ip_address]

    try:
        # Using ip-api.com (free, no key needed, 45 req/min limit)
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=2
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                result = {
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'org': data.get('org', 'Unknown'),
                    'lat': data.get('lat', ''),
                    'lon': data.get('lon', ''),
                    'timezone': data.get('timezone', 'Unknown'),
                    'zip': data.get('zip', ''),
                    'as': data.get('as', 'Unknown')
                }
                ip_cache[ip_address] = result
                return result

        # Rate limit - wait a bit
        time.sleep(1.5)
    except:
        pass

    # Default if lookup fails
    default = {
        'country': 'Unknown',
        'city': 'Unknown',
        'region': 'Unknown',
        'isp': 'Unknown',
        'org': 'Unknown',
        'lat': '',
        'lon': '',
        'timezone': 'Unknown',
        'zip': '',
        'as': 'Unknown'
    }
    ip_cache[ip_address] = default
    return default

def check_suspicious_domain(domain):
    """Check if email domain is suspicious"""
    if not domain:
        return 'UNKNOWN'

    domain_lower = domain.lower()

    # Check against known suspicious domains
    for sus_domain in SUSPICIOUS_DOMAINS:
        if sus_domain in domain_lower:
            return f'YES - {sus_domain.upper()}'

    # Check for suspicious TLDs
    suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.click', '.download', '.review', '.top', '.buzz']
    for tld in suspicious_tlds:
        if domain_lower.endswith(tld):
            return f'SUSPICIOUS TLD - {tld}'

    # Check for numbers in domain (often suspicious)
    domain_parts = domain_lower.split('.')
    if len(domain_parts) > 0 and any(char.isdigit() for char in domain_parts[0]):
        return 'NUMBERS IN DOMAIN'

    return 'No'

def check_vpn_indicators(isp, org):
    """Check for VPN/Proxy indicators"""
    vpn_keywords = ['vpn', 'proxy', 'tor', 'relay', 'anonymous', 'hosting',
                    'datacenter', 'cloud', 'server', 'virtual', 'private']
    combined = f"{isp} {org}".lower()

    for keyword in vpn_keywords:
        if keyword in combined:
            return f'YES - {keyword.upper()}'
    return 'No'

def calculate_geo_risk_score(geo_data):
    """Calculate risk score based on geographic data"""
    score = 0
    factors = []

    # Country risk
    country = geo_data.get('country', 'Unknown')
    if country == 'Unknown':
        score += 20
        factors.append('Unknown location')
    elif country in HIGH_RISK_COUNTRIES:
        score += 50
        factors.append(f'High-risk country: {country}')
    elif country != 'United States':
        score += 30
        factors.append(f'Foreign: {country}')

    # ISP/Org risk
    isp = geo_data.get('isp', '').lower()
    org = geo_data.get('org', '').lower()

    vpn_check = check_vpn_indicators(isp, org)
    if vpn_check.startswith('YES'):
        score += 40
        factors.append(vpn_check)

    # Hosting providers
    hosting_providers = ['amazon', 'google cloud', 'azure', 'digitalocean', 'linode']
    for provider in hosting_providers:
        if provider in isp or provider in org:
            score += 30
            factors.append(f'Hosting provider: {provider}')
            break

    return score, '; '.join(factors) if factors else 'Normal'

def main():
    print("=" * 80)
    print("ADVANCED FRAUD ANALYSIS - EMAIL CHANGE RISK REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # MySQL configuration (same as migration script)
    mysql_config = {
        'host': 'infinity-9ix.calcoastcu.org',
        'port': 3306,
        'user': 'Kendall.Greeven',
        'password': "Note9Shucran32!JelloAzulXie",
        'database': 'dbxdb',
        'charset': 'utf8mb4',
        'connect_timeout': 30,
    }

    print("\nConnecting to MySQL database...")

    try:
        conn = pymysql.connect(**mysql_config)
        print("✓ Connected successfully")

        # Your advanced SQL query with CTEs - UPDATED TO SEPTEMBER 1ST START DATE
        query = """
WITH
email_changes AS (
    SELECT
        id,
        sessionid,
        ipAddress,
        muid,
        masterMembership,
        userName,
        activityDate,
        platform,
        platformOS,
        eventData,
        eventCategory,
        delivered,
        browser,
        TRIM(BOTH '"' FROM SUBSTRING_INDEX(SUBSTRING_INDEX(eventData, '@', 1), '"', -1)) as new_email_user,
        SUBSTRING_INDEX(SUBSTRING_INDEX(eventData, '@', -1), '"', 1) as new_email_domain,
        CASE
            WHEN eventCategory = 'Change Primary email' THEN 'PRIMARY'
            WHEN eventCategory = 'Change Alternate email' THEN 'ALTERNATE'
            ELSE REPLACE(eventCategory, 'Change ', '')
        END as email_type
    FROM fraudmonitor
    WHERE eventCategory IN ('Change Primary email', 'Change Alternate email')
        AND activityDate >= '2025-09-01'
        AND masterMembership IS NOT NULL
),
ip_history AS (
    SELECT
        fm.userName,
        fm.masterMembership,
        fm.ipAddress,
        COUNT(DISTINCT fm.sessionid) as total_sessions,
        COUNT(*) as total_events,
        MIN(fm.activityDate) as first_seen,
        MAX(fm.activityDate) as last_seen,
        COUNT(DISTINCT DATE(fm.activityDate)) as days_active,
        COUNT(DISTINCT fm.eventCategory) as event_variety,
        COUNT(DISTINCT fm.platform) as platform_variety,
        SUM(CASE WHEN fm.browser IS NOT NULL THEN 1 ELSE 0 END) as browser_events,
        SUM(CASE WHEN fm.eventCategory LIKE '%login%' THEN 1 ELSE 0 END) as login_events,
        SUM(CASE WHEN fm.eventCategory LIKE '%fail%' THEN 1 ELSE 0 END) as failed_events,
        SUM(CASE WHEN fm.eventCategory LIKE '%change%' THEN 1 ELSE 0 END) as change_events,
        SUM(CASE WHEN fm.eventCategory LIKE '%password%' THEN 1 ELSE 0 END) as password_events,
        COUNT(CASE WHEN fm.activityDate >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 END) as last_24h_events,
        COUNT(CASE WHEN fm.activityDate >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as last_7d_events,
        COUNT(CASE WHEN fm.activityDate >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as last_30d_events,
        GROUP_CONCAT(DISTINCT HOUR(fm.activityDate) ORDER BY HOUR(fm.activityDate)) as active_hours,
        GROUP_CONCAT(DISTINCT fm.platform ORDER BY fm.platform) as platforms_used
    FROM fraudmonitor fm
    WHERE fm.userName IN (SELECT DISTINCT userName FROM email_changes)
        AND fm.activityDate >= '2025-09-01'
        AND fm.ipAddress IS NOT NULL
    GROUP BY fm.userName, fm.masterMembership, fm.ipAddress
),
account_patterns AS (
    SELECT
        userName,
        masterMembership,
        COUNT(DISTINCT ipAddress) as total_unique_ips,
        COUNT(DISTINCT sessionid) as total_sessions,
        COUNT(*) as total_events,
        SUM(CASE WHEN eventCategory LIKE '%change%' THEN 1 ELSE 0 END) as total_changes,
        SUM(CASE WHEN eventCategory LIKE '%email%' THEN 1 ELSE 0 END) as email_changes,
        SUM(CASE WHEN eventCategory LIKE '%password%' THEN 1 ELSE 0 END) as password_changes,
        SUM(CASE WHEN eventCategory LIKE '%phone%' THEN 1 ELSE 0 END) as phone_changes,
        COUNT(DISTINCT platform) as platform_diversity,
        SUM(CASE WHEN browser IS NOT NULL THEN 1 ELSE 0 END) as browser_usage_count,
        MIN(activityDate) as account_first_activity,
        MAX(activityDate) as account_last_activity,
        DATEDIFF(MAX(activityDate), MIN(activityDate)) as account_age_days,
        SUM(CASE WHEN activityDate >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 1 ELSE 0 END) as last_24h_activity,
        SUM(CASE WHEN activityDate >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as last_7d_activity,
        COUNT(CASE WHEN activityDate < DATE_SUB(NOW(), INTERVAL 7 DAY)
                   AND activityDate >= '2025-09-01' THEN 1 END) / NULLIF(DATEDIFF(NOW(), '2025-09-01'), 0) as avg_daily_activity_historical,
        SUM(CASE WHEN eventCategory LIKE '%fail%' OR eventCategory LIKE '%denied%' THEN 1 ELSE 0 END) as failed_attempts,
        COUNT(DISTINCT SUBSTRING_INDEX(ipAddress, '.', 3)) as unique_ip_subnets
    FROM fraudmonitor
    WHERE userName IN (SELECT DISTINCT userName FROM email_changes)
        AND activityDate >= '2025-09-01'
    GROUP BY userName, masterMembership
),
risk_scores AS (
    SELECT
        ec.*,
        COALESCE(iph.total_sessions, 0) as ip_total_sessions,
        COALESCE(iph.first_seen, ec.activityDate) as ip_first_seen,
        COALESCE(iph.last_seen, ec.activityDate) as ip_last_seen,
        COALESCE(iph.days_active, 1) as ip_days_active,
        COALESCE(iph.browser_events, 0) as ip_browser_events,
        COALESCE(iph.failed_events, 0) as ip_failed_events,
        COALESCE(iph.change_events, 0) as ip_change_events,
        COALESCE(ap.total_unique_ips, 1) as total_unique_ips,
        COALESCE(ap.email_changes, 0) as account_email_changes,
        COALESCE(ap.password_changes, 0) as account_password_changes,
        COALESCE(ap.browser_usage_count, 0) as browser_usage_count,
        COALESCE(ap.account_age_days, 0) as account_age_days,
        COALESCE(ap.last_24h_activity, 1) as last_24h_activity,
        COALESCE(ap.failed_attempts, 0) as failed_attempts,
        COALESCE(ap.avg_daily_activity_historical, 0) as historical_avg_daily,
        CASE
            WHEN COALESCE(iph.total_sessions, 0) = 0 THEN 50
            WHEN COALESCE(iph.total_sessions, 0) <= 2 THEN 30
            ELSE 0
        END as new_ip_risk,
        CASE WHEN ec.browser IS NOT NULL THEN 30 ELSE 0 END as browser_risk,
        CASE
            WHEN COALESCE(iph.days_active, 1) <= 1 THEN 20
            WHEN COALESCE(iph.days_active, 1) <= 3 THEN 10
            ELSE 0
        END as ip_age_risk,
        CASE
            WHEN COALESCE(ap.email_changes, 0) > 3 THEN 30
            WHEN COALESCE(ap.email_changes, 0) > 2 THEN 20
            WHEN COALESCE(ap.email_changes, 0) > 1 THEN 10
            ELSE 0
        END as frequent_changes_risk,
        CASE
            WHEN COALESCE(ap.failed_attempts, 0) > 10 THEN 30
            WHEN COALESCE(ap.failed_attempts, 0) > 5 THEN 20
            WHEN COALESCE(ap.failed_attempts, 0) > 0 THEN 10
            ELSE 0
        END as failed_attempts_risk,
        CASE
            WHEN ap.last_24h_activity > GREATEST(ap.avg_daily_activity_historical * 5, 10) THEN 30
            WHEN ap.last_24h_activity > GREATEST(ap.avg_daily_activity_historical * 3, 5) THEN 15
            ELSE 0
        END as activity_spike_risk,
        CASE
            WHEN HOUR(ec.activityDate) BETWEEN 0 AND 5 THEN 15
            WHEN HOUR(ec.activityDate) BETWEEN 22 AND 23 THEN 5
            ELSE 0
        END as odd_hour_risk,
        CASE
            WHEN ec.new_email_domain IN ('gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com') THEN 0
            WHEN ec.new_email_domain LIKE '%temp%' OR ec.new_email_domain LIKE '%disposable%' THEN 50
            WHEN ec.new_email_domain LIKE '%guerrilla%' OR ec.new_email_domain LIKE '%mailinator%' THEN 50
            ELSE 15
        END as unusual_domain_risk,
        CASE
            WHEN ec.browser IS NOT NULL AND COALESCE(iph.total_sessions, 0) = 0 THEN 20
            ELSE 0
        END as combo_risk
    FROM email_changes ec
    LEFT JOIN ip_history iph
        ON ec.userName = iph.userName
        AND ec.ipAddress = iph.ipAddress
    LEFT JOIN account_patterns ap
        ON ec.userName = ap.userName
),
ip_sharing AS (
    SELECT
        ipAddress,
        COUNT(DISTINCT userName) as shared_accounts,
        COUNT(DISTINCT masterMembership) as shared_parents,
        GROUP_CONCAT(DISTINCT userName ORDER BY userName SEPARATOR ', ') as other_users
    FROM fraudmonitor
    WHERE activityDate >= '2025-09-01'
        AND ipAddress IN (SELECT DISTINCT ipAddress FROM email_changes WHERE ipAddress IS NOT NULL)
    GROUP BY ipAddress
),
recent_activity_raw AS (
    SELECT
        userName,
        activityDate,
        eventCategory,
        platform,
        ipAddress,
        browser,
        ROW_NUMBER() OVER (PARTITION BY userName ORDER BY activityDate DESC) as rn
    FROM fraudmonitor
    WHERE userName IN (SELECT DISTINCT userName FROM email_changes)
        AND activityDate >= '2025-09-01'
),
recent_activity AS (
    SELECT
        userName,
        GROUP_CONCAT(
            CONCAT(
                DATE_FORMAT(activityDate, '%m/%d %H:%i'),
                ' | ',
                SUBSTRING(eventCategory, 1, 30),
                ' | ',
                COALESCE(SUBSTRING(platform, 1, 15), 'Unknown'),
                ' | ',
                ipAddress,
                IF(browser IS NOT NULL, ' | BROWSER', '')
            )
            ORDER BY activityDate DESC
            SEPARATOR '; '
        ) as recent_history
    FROM recent_activity_raw
    WHERE rn <= 10
    GROUP BY userName
)
SELECT
    rs.masterMembership as Parent_Account,
    rs.muid as MUID,
    rs.userName as Username,
    rs.sessionid as Session_ID,
    (rs.new_ip_risk + rs.browser_risk + rs.ip_age_risk +
     rs.frequent_changes_risk + rs.failed_attempts_risk +
     rs.activity_spike_risk + rs.odd_hour_risk +
     rs.unusual_domain_risk + rs.combo_risk) as Risk_Score,
    CASE
        WHEN (rs.new_ip_risk + rs.browser_risk + rs.ip_age_risk + rs.frequent_changes_risk +
              rs.failed_attempts_risk + rs.activity_spike_risk + rs.odd_hour_risk +
              rs.unusual_domain_risk + rs.combo_risk) >= 100 THEN 'CRITICAL'
        WHEN (rs.new_ip_risk + rs.browser_risk + rs.ip_age_risk + rs.frequent_changes_risk +
              rs.failed_attempts_risk + rs.activity_spike_risk + rs.odd_hour_risk +
              rs.unusual_domain_risk + rs.combo_risk) >= 75 THEN 'HIGH'
        WHEN (rs.new_ip_risk + rs.browser_risk + rs.ip_age_risk + rs.frequent_changes_risk +
              rs.failed_attempts_risk + rs.activity_spike_risk + rs.odd_hour_risk +
              rs.unusual_domain_risk + rs.combo_risk) >= 50 THEN 'MEDIUM'
        WHEN (rs.new_ip_risk + rs.browser_risk + rs.ip_age_risk + rs.frequent_changes_risk +
              rs.failed_attempts_risk + rs.activity_spike_risk + rs.odd_hour_risk +
              rs.unusual_domain_risk + rs.combo_risk) >= 25 THEN 'LOW'
        ELSE 'MINIMAL'
    END as Risk_Level,
    CONCAT(
        IF(rs.new_ip_risk > 0, CONCAT('NewIP(', rs.new_ip_risk, ') '), ''),
        IF(rs.browser_risk > 0, CONCAT('Browser(', rs.browser_risk, ') '), ''),
        IF(rs.frequent_changes_risk > 0, CONCAT('FreqChanges(', rs.frequent_changes_risk, ') '), ''),
        IF(rs.failed_attempts_risk > 0, CONCAT('Failed(', rs.failed_attempts_risk, ') '), ''),
        IF(rs.activity_spike_risk > 0, CONCAT('Spike(', rs.activity_spike_risk, ') '), ''),
        IF(rs.odd_hour_risk > 0, CONCAT('OddHr(', rs.odd_hour_risk, ') '), ''),
        IF(rs.unusual_domain_risk > 0, CONCAT('Domain(', rs.unusual_domain_risk, ') '), ''),
        IF(rs.combo_risk > 0, CONCAT('Combo(', rs.combo_risk, ') '), '')
    ) as Risk_Factors,
    DATE_FORMAT(rs.activityDate, '%Y-%m-%d %H:%i:%s') as Change_DateTime,
    rs.email_type as Email_Type,
    CONCAT(rs.new_email_user, '@', rs.new_email_domain) as New_Email,
    rs.new_email_domain as Email_Domain,
    rs.ipAddress as IP_Address,
    CASE
        WHEN rs.ip_total_sessions = 0 THEN 'NEW'
        WHEN rs.ip_total_sessions <= 5 THEN 'RARE'
        ELSE 'KNOWN'
    END as IP_Status,
    rs.ip_total_sessions as IP_Sessions,
    rs.ip_days_active as IP_Days,
    TIMESTAMPDIFF(HOUR, rs.ip_first_seen, rs.activityDate) as Hours_Since_First_IP,
    COALESCE(ips.shared_accounts, 1) as IP_Shared_Count,
    LEFT(ips.other_users, 200) as IP_Other_Users,
    rs.account_age_days as Account_Age_Days,
    rs.total_unique_ips as Total_IPs_Used,
    rs.account_email_changes as Prior_Email_Changes,
    rs.failed_attempts as Failed_Login_Attempts,
    CONCAT(
        '24h:', rs.last_24h_activity,
        ' | Norm:', ROUND(rs.historical_avg_daily, 1),
        ' | Browser:', rs.browser_usage_count
    ) as Activity_Stats,
    COALESCE(rs.platform, 'Unknown') as Platform,
    COALESCE(rs.browser, 'App') as Access_Type,
    CASE
        WHEN (rs.new_ip_risk + rs.browser_risk + rs.ip_age_risk + rs.frequent_changes_risk +
              rs.failed_attempts_risk + rs.activity_spike_risk + rs.odd_hour_risk +
              rs.unusual_domain_risk + rs.combo_risk) >= 100 THEN 'LOCK ACCOUNT NOW'
        WHEN (rs.new_ip_risk + rs.browser_risk + rs.ip_age_risk + rs.frequent_changes_risk +
              rs.failed_attempts_risk + rs.activity_spike_risk + rs.odd_hour_risk +
              rs.unusual_domain_risk + rs.combo_risk) >= 75 THEN 'CALL MEMBER IN 1 HOUR'
        WHEN (rs.new_ip_risk + rs.browser_risk + rs.ip_age_risk + rs.frequent_changes_risk +
              rs.failed_attempts_risk + rs.activity_spike_risk + rs.odd_hour_risk +
              rs.unusual_domain_risk + rs.combo_risk) >= 50 THEN 'VERIFY TODAY'
        WHEN (rs.new_ip_risk + rs.browser_risk + rs.ip_age_risk + rs.frequent_changes_risk +
              rs.failed_attempts_risk + rs.activity_spike_risk + rs.odd_hour_risk +
              rs.unusual_domain_risk + rs.combo_risk) >= 25 THEN 'MONITOR'
        ELSE 'OK'
    END as Action_Required,
    LEFT(COALESCE(ra.recent_history, 'No recent activity'), 500) as Recent_Activity
FROM risk_scores rs
LEFT JOIN ip_sharing ips ON rs.ipAddress = ips.ipAddress
LEFT JOIN recent_activity ra ON rs.userName = ra.userName
ORDER BY
    (rs.new_ip_risk + rs.browser_risk + rs.ip_age_risk + rs.frequent_changes_risk +
     rs.failed_attempts_risk + rs.activity_spike_risk + rs.odd_hour_risk +
     rs.unusual_domain_risk + rs.combo_risk) DESC,
    rs.activityDate DESC
        """

        print("\nExecuting advanced risk analysis query...")
        print("This may take a moment due to complex calculations...")

        df = pd.read_sql(query, conn)
        conn.close()

        print(f"✓ Found {len(df)} email change events to analyze")

        if df.empty:
            print("\nNo email changes found since September 1st")
            return

        # Add geolocation and additional analysis columns
        print("\n" + "=" * 80)
        print("ANALYZING IP ADDRESSES AND EMAIL DOMAINS")
        print("=" * 80)

        # Initialize new columns
        df['IP_Country'] = ''
        df['IP_City'] = ''
        df['IP_Region'] = ''
        df['IP_ISP'] = ''
        df['IP_Organization'] = ''
        df['IP_Latitude'] = ''
        df['IP_Longitude'] = ''
        df['IP_Timezone'] = ''
        df['Is_Foreign_IP'] = ''
        df['Is_VPN_Proxy'] = ''
        df['VPN_Details'] = ''
        df['Is_Suspicious_Domain'] = ''
        df['Domain_Risk_Details'] = ''
        df['Geo_Risk_Score'] = 0
        df['Geo_Risk_Factors'] = ''
        df['Combined_Risk_Score'] = 0
        df['Final_Risk_Assessment'] = ''

        # Process unique IPs for geolocation
        unique_ips = df['IP_Address'].dropna().unique()
        ip_cache = {}

        print(f"\nAnalyzing {len(unique_ips)} unique IP addresses...")

        for i, ip in enumerate(unique_ips):
            if pd.isna(ip) or ip == '' or ip == 'None':
                continue

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(unique_ips)} IPs analyzed...")

            # Get geolocation with rate limiting
            geo_data = get_ip_geolocation(ip, ip_cache)

            # Update all rows with this IP
            mask = df['IP_Address'] == ip
            df.loc[mask, 'IP_Country'] = geo_data['country']
            df.loc[mask, 'IP_City'] = geo_data['city']
            df.loc[mask, 'IP_Region'] = geo_data['region']
            df.loc[mask, 'IP_ISP'] = geo_data['isp']
            df.loc[mask, 'IP_Organization'] = geo_data['org']
            df.loc[mask, 'IP_Latitude'] = str(geo_data['lat'])
            df.loc[mask, 'IP_Longitude'] = str(geo_data['lon'])
            df.loc[mask, 'IP_Timezone'] = geo_data['timezone']

            # Check if foreign
            is_foreign = 'YES' if geo_data['country'] not in ['United States', 'Unknown'] else 'NO'
            df.loc[mask, 'Is_Foreign_IP'] = is_foreign

            # Check for VPN/Proxy
            vpn_check = check_vpn_indicators(geo_data['isp'], geo_data['org'])
            df.loc[mask, 'Is_VPN_Proxy'] = 'YES' if vpn_check.startswith('YES') else 'NO'
            df.loc[mask, 'VPN_Details'] = vpn_check

            # Calculate geo risk score
            geo_risk_score, geo_factors = calculate_geo_risk_score(geo_data)
            df.loc[mask, 'Geo_Risk_Score'] = geo_risk_score
            df.loc[mask, 'Geo_Risk_Factors'] = geo_factors

        print("\n✓ IP address analysis complete")

        # Analyze email domains
        print("\nAnalyzing email domains for suspicious patterns...")

        for idx, row in df.iterrows():
            domain = row['Email_Domain']

            # Check for suspicious domains
            domain_check = check_suspicious_domain(domain)
            df.at[idx, 'Is_Suspicious_Domain'] = 'YES' if domain_check != 'No' else 'NO'
            df.at[idx, 'Domain_Risk_Details'] = domain_check

            # Calculate combined risk score
            base_risk = row['Risk_Score'] if pd.notna(row['Risk_Score']) else 0
            geo_risk = row['Geo_Risk_Score'] if pd.notna(row['Geo_Risk_Score']) else 0
            domain_risk = 50 if domain_check != 'No' else 0

            combined_score = base_risk + geo_risk + domain_risk
            df.at[idx, 'Combined_Risk_Score'] = combined_score

            # Final assessment
            if combined_score >= 200:
                df.at[idx, 'Final_Risk_Assessment'] = 'EXTREME - IMMEDIATE LOCK'
            elif combined_score >= 150:
                df.at[idx, 'Final_Risk_Assessment'] = 'CRITICAL - LOCK & CALL'
            elif combined_score >= 100:
                df.at[idx, 'Final_Risk_Assessment'] = 'HIGH - URGENT REVIEW'
            elif combined_score >= 75:
                df.at[idx, 'Final_Risk_Assessment'] = 'ELEVATED - VERIFY'
            elif combined_score >= 50:
                df.at[idx, 'Final_Risk_Assessment'] = 'MODERATE - MONITOR'
            else:
                df.at[idx, 'Final_Risk_Assessment'] = 'LOW - ROUTINE'

        print("✓ Email domain analysis complete")

        # Sort by combined risk score
        df = df.sort_values('Combined_Risk_Score', ascending=False)

        # Generate output filename
        output_file = f"fraud_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Save to CSV
        df.to_csv(output_file, index=False, encoding='utf-8-sig')

        print(f"\n✓ Full analysis saved to: {output_file}")

        # Print summary statistics
        print("\n" + "=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)

        print(f"\nTotal Email Changes Analyzed: {len(df)}")
        print(f"Unique Accounts: {df['Username'].nunique()}")
        print(f"Unique IP Addresses: {df['IP_Address'].nunique()}")

        # Risk distribution
        print("\nRisk Level Distribution:")
        risk_counts = df['Risk_Level'].value_counts()
        for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL']:
            count = risk_counts.get(level, 0)
            pct = (count / len(df)) * 100 if len(df) > 0 else 0
            print(f"  {level:10} : {count:4} ({pct:5.1f}%)")

        # Geographic analysis
        print(f"\nGeographic Analysis:")
        foreign_count = len(df[df['Is_Foreign_IP'] == 'YES'])
        vpn_count = len(df[df['Is_VPN_Proxy'] == 'YES'])
        print(f"  Foreign IPs: {foreign_count} ({foreign_count/len(df)*100:.1f}%)")
        print(f"  VPN/Proxy Detected: {vpn_count} ({vpn_count/len(df)*100:.1f}%)")

        # Suspicious domains
        sus_domain_count = len(df[df['Is_Suspicious_Domain'] == 'YES'])
        print(f"\nSuspicious Email Domains: {sus_domain_count}")

        if sus_domain_count > 0:
            print("\nTop Suspicious Domains Used:")
            sus_domains = df[df['Is_Suspicious_Domain'] == 'YES']['Email_Domain'].value_counts().head(10)
            for domain, count in sus_domains.items():
                details = df[df['Email_Domain'] == domain]['Domain_Risk_Details'].iloc[0]
                print(f"  • {domain}: {count} uses - {details}")

        # Critical risks
        critical = df[df['Final_Risk_Assessment'].str.contains('EXTREME|CRITICAL')]
        if not critical.empty:
            print("\n" + "=" * 80)
            print("⚠️  CRITICAL RISKS REQUIRING IMMEDIATE ACTION")
            print("=" * 80)

            for idx, row in critical.head(10).iterrows():
                print(f"\n[{row['Final_Risk_Assessment']}]")
                print(f"Account: {row['Parent_Account']} / {row['Username']}")
                print(f"  • Email: {row['New_Email']}")
                print(f"  • Domain Risk: {row['Domain_Risk_Details']}")
                print(f"  • IP: {row['IP_Address']}")
                print(f"  • Location: {row['IP_City']}, {row['IP_Region']}, {row['IP_Country']}")
                print(f"  • VPN/Proxy: {row['VPN_Details']}")
                print(f"  • Risk Score: {row['Combined_Risk_Score']} (Base:{row['Risk_Score']} + Geo:{row['Geo_Risk_Score']})")
                print(f"  • ACTION: {row['Action_Required']}")

        # Browser-based changes
        browser_changes = df[df['Access_Type'] != 'App']
        if not browser_changes.empty:
            print(f"\n⚠️  Browser-Based Changes (Higher Risk): {len(browser_changes)}")
            browsers = browser_changes['Access_Type'].value_counts().head(5)
            for browser, count in browsers.items():
                print(f"  • {browser}: {count}")

        print("\n" + "=" * 80)
        print(f"Complete analysis exported to: {output_file}")
        print("Please review CRITICAL and HIGH risk events immediately!")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()