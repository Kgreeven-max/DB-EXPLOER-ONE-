#!/usr/bin/env python3
"""
CIO December 2025 Login Report
Generates summary report of digital banking logins with geographic demographics
"""

import pandas as pd
from datetime import datetime
import requests
import time
import json
import os
from db_connection import get_connection

# Configuration
START_DATE = '2025-12-01 00:00:00'
END_DATE = '2026-01-01 00:00:00'
IP_CACHE_FILE = 'ip_cache_dec2025.json'
OUTPUT_FILE = 'CIO_December_2025_Login_Report.md'

def load_ip_cache():
    """Load IP cache from file if exists"""
    if os.path.exists(IP_CACHE_FILE):
        try:
            with open(IP_CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_ip_cache(cache):
    """Save IP cache to file"""
    with open(IP_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def get_ip_geolocation(ip_address, ip_cache):
    """Get geographic information for IP address with caching"""
    if ip_address in ip_cache:
        return ip_cache[ip_address]

    try:
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=2
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                result = {
                    'country': data.get('country', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'isp': data.get('isp', 'Unknown')
                }
                ip_cache[ip_address] = result
                return result

        time.sleep(1.5)  # Rate limit
    except Exception as e:
        pass

    # Default for failed lookups
    default = {
        'country': 'Unknown',
        'region': 'Unknown',
        'city': 'Unknown',
        'isp': 'Unknown'
    }
    ip_cache[ip_address] = default
    return default

def fetch_login_data():
    """Fetch December 2025 login data from database"""
    print("\n[1/4] Connecting to database...")
    conn = get_connection()
    print("      Connected to dbxdb on infinity-9ix.calcoastcu.org")

    print("\n[2/4] Fetching December 2025 login data...")

    query = """
    SELECT
        userName,
        activityDate,
        platform,
        ipAddress,
        browser
    FROM fraudmonitor
    WHERE eventCategory = 'LoginSuccessful'
      AND activityDate >= %s
      AND activityDate < %s
    """

    df = pd.read_sql(query, conn, params=[START_DATE, END_DATE])

    cursor = conn.cursor()
    cursor.close()
    conn.close()

    return df

def process_ips(df, ip_cache):
    """Process unique IPs for geolocation"""
    unique_ips = df['ipAddress'].dropna().unique()
    total_ips = len(unique_ips)

    # Find IPs not in cache
    uncached_ips = [ip for ip in unique_ips if ip not in ip_cache]
    cached_count = total_ips - len(uncached_ips)

    print(f"\n[3/4] Processing IP geolocation...")
    print(f"      Total unique IPs: {total_ips:,}")
    print(f"      Already cached: {cached_count:,}")
    print(f"      Need to lookup: {len(uncached_ips):,}")

    if len(uncached_ips) > 0:
        print(f"\n      Processing uncached IPs (1.5s delay per request)...")
        print(f"      Estimated time: {len(uncached_ips) * 1.5 / 60:.1f} minutes")
        print()

        for i, ip in enumerate(uncached_ips):
            get_ip_geolocation(ip, ip_cache)

            # Progress update every 100 IPs
            if (i + 1) % 100 == 0:
                pct = (i + 1) / len(uncached_ips) * 100
                remaining = (len(uncached_ips) - i - 1) * 1.5 / 60
                print(f"      Progress: {i + 1:,}/{len(uncached_ips):,} ({pct:.1f}%) - {remaining:.1f} min remaining")
                # Save cache periodically
                save_ip_cache(ip_cache)

        # Final save
        save_ip_cache(ip_cache)
        print(f"      Complete! Cache saved to {IP_CACHE_FILE}")

    return ip_cache

def generate_report(df, ip_cache):
    """Generate the CIO report"""
    print("\n[4/4] Generating report...")

    # Basic metrics
    total_logins = len(df)
    unique_members = df['userName'].nunique()
    avg_logins = total_logins / unique_members if unique_members > 0 else 0

    # Platform breakdown
    platform_stats = df.groupby('platform').agg({
        'userName': ['count', 'nunique']
    }).reset_index()
    platform_stats.columns = ['platform', 'total_logins', 'unique_members']

    # Add geolocation to dataframe
    df['country'] = df['ipAddress'].apply(lambda x: ip_cache.get(x, {}).get('country', 'Unknown') if pd.notna(x) else 'Unknown')
    df['region'] = df['ipAddress'].apply(lambda x: ip_cache.get(x, {}).get('region', 'Unknown') if pd.notna(x) else 'Unknown')

    # State/region breakdown (US only)
    us_logins = df[df['country'] == 'United States']
    state_stats = us_logins.groupby('region').agg({
        'userName': ['count', 'nunique']
    }).reset_index()
    state_stats.columns = ['state', 'total_logins', 'unique_members']
    state_stats = state_stats.sort_values('total_logins', ascending=False)

    # International logins
    intl_logins = df[df['country'] != 'United States']
    intl_stats = intl_logins.groupby('country').agg({
        'userName': ['count', 'nunique'],
        'ipAddress': 'nunique'
    }).reset_index()
    intl_stats.columns = ['country', 'total_logins', 'unique_members', 'unique_ips']
    intl_stats = intl_stats.sort_values('total_logins', ascending=False)

    # Generate markdown report
    report = f"""# Cal Coast Credit Union
## December 2025 Digital Banking Login Report
### Prepared for: Chief Information Officer
### Report Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
### Data Period: December 1-31, 2025

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Successful Logins | {total_logins:,} |
| Unique Members | {unique_members:,} |
| Average Logins per Member | {avg_logins:.1f} |

---

## Login Activity by Platform

| Platform | Description | Total Logins | Unique Members | % of Total |
|----------|-------------|--------------|----------------|------------|
"""

    for _, row in platform_stats.iterrows():
        platform_name = 'Mobile App' if row['platform'] == 'MB' else 'Web Browser' if row['platform'] == 'OLB' else row['platform']
        pct = row['total_logins'] / total_logins * 100 if total_logins > 0 else 0
        report += f"| {row['platform']} | {platform_name} | {row['total_logins']:,} | {row['unique_members']:,} | {pct:.1f}% |\n"

    report += f"""
---

## Geographic Demographics (US)

### Top 10 States by Login Volume

| Rank | State | Total Logins | Unique Members | % of US Logins |
|------|-------|--------------|----------------|----------------|
"""

    us_total = len(us_logins)
    for i, (_, row) in enumerate(state_stats.head(10).iterrows()):
        pct = row['total_logins'] / us_total * 100 if us_total > 0 else 0
        report += f"| {i+1} | {row['state']} | {row['total_logins']:,} | {row['unique_members']:,} | {pct:.1f}% |\n"

    # State summary
    total_states = len(state_stats)
    ca_logins = state_stats[state_stats['state'] == 'California']['total_logins'].sum() if 'California' in state_stats['state'].values else 0
    ca_pct = ca_logins / us_total * 100 if us_total > 0 else 0
    out_of_state = us_total - ca_logins
    out_of_state_pct = out_of_state / us_total * 100 if us_total > 0 else 0

    report += f"""
### State Distribution Summary

| Metric | Value |
|--------|-------|
| Total US States Represented | {total_states} |
| California Logins | {ca_logins:,} ({ca_pct:.1f}%) |
| Out-of-State Logins | {out_of_state:,} ({out_of_state_pct:.1f}%) |

---

## International Login Activity

"""

    if len(intl_stats) > 0 and intl_stats[intl_stats['country'] != 'Unknown']['total_logins'].sum() > 0:
        intl_filtered = intl_stats[intl_stats['country'] != 'Unknown']
        report += """| Country | Total Logins | Unique Members | Unique IPs |
|---------|--------------|----------------|------------|
"""
        for _, row in intl_filtered.iterrows():
            report += f"| {row['country']} | {row['total_logins']:,} | {row['unique_members']:,} | {row['unique_ips']:,} |\n"

        report += f"""
### International Summary

| Metric | Value |
|--------|-------|
| Total International Logins | {intl_filtered['total_logins'].sum():,} |
| Total International Members | {intl_filtered['unique_members'].sum():,} |
| Countries Detected | {len(intl_filtered)} |
"""
    else:
        report += "*No international logins detected in December 2025.*\n"

    report += f"""
---

## Technical Notes

- **Data Source:** dbxdb.fraudmonitor table
- **Event Type:** LoginSuccessful
- **Timestamps:** UTC (database storage)
- **IP Geolocation:** ip-api.com (state/region level)
- **LoginSuccessful events:** Available since October 28, 2025
- **Unknown locations:** IPs that could not be geolocated (private IPs, VPNs, etc.)

---

*Report generated by cio_december_2025_login_report.py*
"""

    # Write report to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"      Report saved to: {OUTPUT_FILE}")

    return report

def main():
    print("=" * 80)
    print("CIO DECEMBER 2025 LOGIN REPORT - GENERATION IN PROGRESS")
    print("=" * 80)

    # Load existing IP cache
    ip_cache = load_ip_cache()

    # Fetch login data
    df = fetch_login_data()
    print(f"      Found {len(df):,} successful logins")
    print(f"      Unique members: {df['userName'].nunique():,}")
    print(f"      Unique IP addresses: {df['ipAddress'].nunique():,}")

    # Process IPs for geolocation
    ip_cache = process_ips(df, ip_cache)

    # Generate report
    report = generate_report(df, ip_cache)

    print("\n" + "=" * 80)
    print("REPORT COMPLETE")
    print("=" * 80)

    # Print summary to console
    print("\n--- Quick Summary ---")
    print(f"Total Logins: {len(df):,}")
    print(f"Unique Members: {df['userName'].nunique():,}")
    print(f"Output file: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
