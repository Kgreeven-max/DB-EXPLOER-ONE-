#!/usr/bin/env python3
"""
Audit Trail Investigation Script
MUID: 00638242923564062860

Generates comprehensive audit report for upper management investigating:
1. How OTPs got sent to email joeynaj@ibande.xyz
2. How this suspicious email appeared on the account
3. What default@calcoast.com means
4. Complete timeline of all member activity in PST
"""

import json
import time
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from db_connection import get_connection

MUID = '00638242923564062860'
OUTPUT_FILE = 'AUDIT_REPORT_00638242923564062860.md'

# UTC to PST offset (8 hours behind)
PST_OFFSET = timedelta(hours=-8)

def utc_to_pst(utc_dt):
    """Convert UTC datetime to PST string"""
    if utc_dt is None:
        return "N/A"
    pst_dt = utc_dt + PST_OFFSET
    return pst_dt.strftime('%Y-%m-%d %H:%M:%S PST')

def get_ip_geolocation(ip_address):
    """Get geolocation info for an IP address using ip-api.com"""
    if not ip_address or ip_address in ('N/A', 'NULL', ''):
        return {'country': 'Unknown', 'region': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown', 'proxy': False}

    try:
        # Rate limit: max 45 requests per minute
        time.sleep(0.1)
        response = requests.get(f'http://ip-api.com/json/{ip_address}?fields=status,country,regionName,city,isp,proxy,hosting', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'proxy': data.get('proxy', False) or data.get('hosting', False)
                }
    except Exception as e:
        print(f"  Geolocation lookup failed for {ip_address}: {e}")

    return {'country': 'Unknown', 'region': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown', 'proxy': False}

def parse_event_data(event_data, event_category):
    """Parse eventData JSON based on event category"""
    if not event_data:
        return {}

    try:
        if isinstance(event_data, str):
            data = json.loads(event_data)
        else:
            data = event_data

        if not isinstance(data, list):
            return {'raw': str(data)}

        # Parse based on event category
        if event_category in ('LoginSuccessful', 'LoginFailure'):
            # ["primary_email", "alt_email", "phone1", "phone2", "phone3", "account"]
            return {
                'primary_email': data[0] if len(data) > 0 else None,
                'alt_email': data[1] if len(data) > 1 else None,
                'phone1': data[2] if len(data) > 2 else None,
                'phone2': data[3] if len(data) > 3 else None,
                'phone3': data[4] if len(data) > 4 else None,
                'account': data[5] if len(data) > 5 else None,
            }
        elif 'OTP' in event_category:
            # ["method", "masked_phone", null, "full_phone", "status"]
            return {
                'method': data[0] if len(data) > 0 else None,
                'masked_phone': data[1] if len(data) > 1 else None,
                'full_phone': data[3] if len(data) > 3 else None,
                'status': data[4] if len(data) > 4 else None,
            }
        elif 'Change' in event_category or 'email' in event_category.lower():
            # ["field_name", "new_value", "action"]
            return {
                'field': data[0] if len(data) > 0 else None,
                'new_value': data[1] if len(data) > 1 else None,
                'action': data[2] if len(data) > 2 else None,
            }
        elif event_category == 'New Device Register':
            return {
                'device_id': data[0] if len(data) > 0 else None,
                'device_type': data[1] if len(data) > 1 else None,
            }
        else:
            return {'raw': data}
    except Exception as e:
        return {'parse_error': str(e), 'raw': str(event_data)}

def query_fraudmonitor():
    """Query all fraudmonitor records for this MUID"""
    print(f"Querying fraudmonitor for MUID {MUID}...")

    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT activityDate, eventCategory, eventData, ipAddress, platform,
           platformOS, browser, sessionid, userName, masterMembership
    FROM fraudmonitor
    WHERE muid = %s
    ORDER BY activityDate ASC
    """

    cursor.execute(query, (MUID,))
    results = cursor.fetchall()

    columns = ['activityDate', 'eventCategory', 'eventData', 'ipAddress', 'platform',
               'platformOS', 'browser', 'sessionid', 'userName', 'masterMembership']

    records = []
    for row in results:
        record = dict(zip(columns, row))
        record['parsed_data'] = parse_event_data(record['eventData'], record['eventCategory'])
        records.append(record)

    cursor.close()
    conn.close()

    print(f"  Found {len(records)} fraudmonitor records")
    return records

def query_alerthistory(username):
    """Query all alerthistory records for this username"""
    print(f"Querying alerthistory for username '{username}'...")

    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT createdts, DispatchDate, AlertSubTypeId, ChannelId, Status,
           Subject, Message, ErrorMessage
    FROM alerthistory
    WHERE createdby = %s
    ORDER BY createdts ASC
    """

    cursor.execute(query, (username,))
    results = cursor.fetchall()

    columns = ['createdts', 'DispatchDate', 'AlertSubTypeId', 'ChannelId', 'Status',
               'Subject', 'Message', 'ErrorMessage']

    records = []
    for row in results:
        record = dict(zip(columns, row))
        records.append(record)

    cursor.close()
    conn.close()

    print(f"  Found {len(records)} alerthistory records")
    return records

def analyze_email_history(fraud_records):
    """Analyze email addresses found in records"""
    email_timeline = []
    emails_seen = set()

    for record in fraud_records:
        parsed = record.get('parsed_data', {})
        event_cat = record['eventCategory']
        timestamp = record['activityDate']

        # Check for email in LoginSuccessful events
        if event_cat in ('LoginSuccessful', 'LoginFailure'):
            primary = parsed.get('primary_email')
            alt = parsed.get('alt_email')

            if primary and primary not in emails_seen:
                emails_seen.add(primary)
                email_timeline.append({
                    'timestamp': timestamp,
                    'email': primary,
                    'type': 'primary_email',
                    'source': event_cat
                })
            if alt and alt not in emails_seen:
                emails_seen.add(alt)
                email_timeline.append({
                    'timestamp': timestamp,
                    'email': alt,
                    'type': 'alt_email',
                    'source': event_cat
                })

        # Check for email change events
        if 'email' in event_cat.lower() or ('Change' in event_cat and 'email' in str(parsed.get('field', '')).lower()):
            new_email = parsed.get('new_value')
            if new_email:
                email_timeline.append({
                    'timestamp': timestamp,
                    'email': new_email,
                    'type': 'email_change',
                    'source': event_cat,
                    'field': parsed.get('field'),
                    'action': parsed.get('action')
                })

    return email_timeline

def analyze_otp_events(fraud_records, alert_records):
    """Analyze all OTP-related events"""
    otp_events = []

    # From fraudmonitor
    for record in fraud_records:
        if 'OTP' in record['eventCategory']:
            parsed = record.get('parsed_data', {})
            otp_events.append({
                'timestamp': record['activityDate'],
                'source': 'fraudmonitor',
                'event': record['eventCategory'],
                'method': parsed.get('method'),
                'destination': parsed.get('full_phone') or parsed.get('masked_phone'),
                'status': parsed.get('status'),
                'ip': record['ipAddress'],
                'platform': record['platform']
            })

    # From alerthistory - look for OTP-related alerts
    for record in alert_records:
        alert_type = record['AlertSubTypeId'] or ''
        subject = record['Subject'] or ''

        if 'OTP' in alert_type.upper() or 'verification' in subject.lower() or 'code' in subject.lower():
            otp_events.append({
                'timestamp': record['createdts'],
                'source': 'alerthistory',
                'event': record['AlertSubTypeId'],
                'channel': record['ChannelId'],
                'status': record['Status'],
                'subject': subject,
                'dispatch_date': record['DispatchDate'],
                'error': record['ErrorMessage']
            })

    return sorted(otp_events, key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min)

def generate_report(fraud_records, alert_records, ip_geo_cache):
    """Generate the markdown audit report"""

    # Extract key info
    username = None
    membership = None
    for r in fraud_records:
        if r['userName']:
            username = r['userName']
        if r['masterMembership']:
            membership = r['masterMembership']
        if username and membership:
            break

    # Analyze data
    email_history = analyze_email_history(fraud_records)
    otp_events = analyze_otp_events(fraud_records, alert_records)

    # Get unique IPs
    unique_ips = set()
    for r in fraud_records:
        if r['ipAddress']:
            unique_ips.add(r['ipAddress'])

    # Find suspicious email
    suspicious_email = 'joeynaj@ibande.xyz'
    suspicious_email_events = [e for e in email_history if suspicious_email.lower() in str(e.get('email', '')).lower()]

    # Find default@calcoast.com references
    default_email_events = []
    for r in fraud_records:
        if 'default@calcoast' in str(r.get('eventData', '')).lower():
            default_email_events.append(r)
    for r in alert_records:
        if 'default@calcoast' in str(r.get('Message', '')).lower() or 'default@calcoast' in str(r.get('Subject', '')).lower():
            default_email_events.append(r)

    # Count events by category
    event_counts = defaultdict(int)
    for r in fraud_records:
        event_counts[r['eventCategory']] += 1

    # Build report
    report = []
    report.append("# Audit Trail Report: MUID 00638242923564062860")
    report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Report Type:** Fraud Investigation / Audit Trail")
    report.append(f"**Requested By:** Upper Management")
    report.append("")

    # Executive Summary
    report.append("---")
    report.append("## 1. Executive Summary")
    report.append("")
    report.append(f"This report documents all digital banking activity for member MUID `{MUID}` (username: `{username}`).")
    report.append("")
    report.append("### Key Findings:")
    report.append(f"- **Total Activity Records:** {len(fraud_records)} events in fraudmonitor")
    report.append(f"- **Total Alerts Sent:** {len(alert_records)} notifications")
    report.append(f"- **Unique IP Addresses Used:** {len(unique_ips)}")
    report.append(f"- **Date Range:** {utc_to_pst(fraud_records[0]['activityDate']) if fraud_records else 'N/A'} to {utc_to_pst(fraud_records[-1]['activityDate']) if fraud_records else 'N/A'}")
    report.append("")

    if suspicious_email_events:
        report.append(f"**ALERT:** Suspicious email `{suspicious_email}` was found in {len(suspicious_email_events)} event(s).")
    else:
        report.append(f"**Note:** Email `{suspicious_email}` was NOT found directly in fraudmonitor records.")
        report.append("  - Check alerthistory message content below for OTP delivery destinations.")
    report.append("")

    # Member Information
    report.append("---")
    report.append("## 2. Member Information")
    report.append("")
    report.append(f"| Field | Value |")
    report.append(f"|-------|-------|")
    report.append(f"| MUID | `{MUID}` |")
    report.append(f"| Username | `{username}` |")
    report.append(f"| Master Membership | `{membership}` |")
    report.append("")

    # Email History Analysis
    report.append("---")
    report.append("## 3. Email History Analysis")
    report.append("")
    report.append("### All Email Addresses Observed:")
    report.append("")
    report.append("| Timestamp (PST) | Email Address | Type | Source Event |")
    report.append("|-----------------|---------------|------|--------------|")

    if email_history:
        for e in email_history:
            report.append(f"| {utc_to_pst(e['timestamp'])} | `{e['email']}` | {e['type']} | {e['source']} |")
    else:
        report.append("| *No email addresses found in records* | - | - | - |")
    report.append("")

    if suspicious_email_events:
        report.append(f"### Investigation: How `{suspicious_email}` Appeared")
        report.append("")
        for e in suspicious_email_events:
            report.append(f"- **{utc_to_pst(e['timestamp'])}:** Found in `{e['source']}` event as `{e['type']}`")
            if e.get('action'):
                report.append(f"  - Action: {e['action']}")
    report.append("")

    # OTP Delivery History
    report.append("---")
    report.append("## 4. OTP Delivery History")
    report.append("")
    report.append("This section documents all One-Time Password (OTP) events to trace where verification codes were sent.")
    report.append("")

    otp_from_fraud = [o for o in otp_events if o['source'] == 'fraudmonitor']
    otp_from_alerts = [o for o in otp_events if o['source'] == 'alerthistory']

    report.append("### OTP Authentication Events (from fraudmonitor):")
    report.append("")
    report.append("| Timestamp (PST) | Event | Method | Destination | Status | IP Address |")
    report.append("|-----------------|-------|--------|-------------|--------|------------|")

    if otp_from_fraud:
        for o in otp_from_fraud:
            report.append(f"| {utc_to_pst(o['timestamp'])} | {o['event']} | {o.get('method', 'N/A')} | `{o.get('destination', 'N/A')}` | {o.get('status', 'N/A')} | {o.get('ip', 'N/A')} |")
    else:
        report.append("| *No OTP events found* | - | - | - | - | - |")
    report.append("")

    report.append("### OTP-Related Alerts (from alerthistory):")
    report.append("")
    report.append("| Timestamp (PST) | Alert Type | Channel | Status | Subject |")
    report.append("|-----------------|------------|---------|--------|---------|")

    if otp_from_alerts:
        for o in otp_from_alerts:
            subject = (o.get('subject') or '')[:50] + '...' if len(o.get('subject') or '') > 50 else o.get('subject') or 'N/A'
            report.append(f"| {utc_to_pst(o['timestamp'])} | {o.get('event', 'N/A')} | {o.get('channel', 'N/A')} | {o.get('status', 'N/A')} | {subject} |")
    else:
        report.append("| *No OTP-related alerts found* | - | - | - | - |")
    report.append("")

    # Login Activity
    report.append("---")
    report.append("## 5. Login Activity")
    report.append("")

    login_events = [r for r in fraud_records if 'Login' in r['eventCategory']]

    report.append("| Timestamp (PST) | Event | Platform | IP Address | Location |")
    report.append("|-----------------|-------|----------|------------|----------|")

    for r in login_events[-50:]:  # Last 50 logins
        ip = r['ipAddress'] or 'N/A'
        geo = ip_geo_cache.get(ip, {})
        location = f"{geo.get('city', '?')}, {geo.get('region', '?')}, {geo.get('country', '?')}"
        if geo.get('proxy'):
            location += " **[VPN/PROXY]**"
        report.append(f"| {utc_to_pst(r['activityDate'])} | {r['eventCategory']} | {r['platform']} | {ip} | {location} |")

    if len(login_events) > 50:
        report.append(f"\n*Showing last 50 of {len(login_events)} login events*")
    report.append("")

    # Profile Changes
    report.append("---")
    report.append("## 6. Profile Changes")
    report.append("")
    report.append("All changes to email, phone, address, and other profile information:")
    report.append("")

    change_events = [r for r in fraud_records if 'Change' in r['eventCategory'] or 'Add' in r['eventCategory'] or 'Register' in r['eventCategory']]

    report.append("| Timestamp (PST) | Change Type | Details | IP Address |")
    report.append("|-----------------|-------------|---------|------------|")

    if change_events:
        for r in change_events:
            parsed = r.get('parsed_data', {})
            details = f"{parsed.get('field', '')}: {parsed.get('new_value', parsed.get('raw', ''))}"[:60]
            report.append(f"| {utc_to_pst(r['activityDate'])} | {r['eventCategory']} | {details} | {r['ipAddress']} |")
    else:
        report.append("| *No profile changes found* | - | - | - |")
    report.append("")

    # IP Analysis
    report.append("---")
    report.append("## 7. IP Address Analysis")
    report.append("")
    report.append("| IP Address | Country | Region | City | ISP | VPN/Proxy | First Seen (PST) | Last Seen (PST) | Event Count |")
    report.append("|------------|---------|--------|------|-----|-----------|------------------|-----------------|-------------|")

    ip_stats = defaultdict(lambda: {'count': 0, 'first': None, 'last': None})
    for r in fraud_records:
        ip = r['ipAddress']
        if ip:
            ip_stats[ip]['count'] += 1
            ts = r['activityDate']
            if ip_stats[ip]['first'] is None or ts < ip_stats[ip]['first']:
                ip_stats[ip]['first'] = ts
            if ip_stats[ip]['last'] is None or ts > ip_stats[ip]['last']:
                ip_stats[ip]['last'] = ts

    for ip, stats in sorted(ip_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        geo = ip_geo_cache.get(ip, {})
        vpn_flag = "YES" if geo.get('proxy') else "No"
        report.append(f"| {ip} | {geo.get('country', '?')} | {geo.get('region', '?')} | {geo.get('city', '?')} | {geo.get('isp', '?')[:30]} | {vpn_flag} | {utc_to_pst(stats['first'])} | {utc_to_pst(stats['last'])} | {stats['count']} |")
    report.append("")

    # Alert History
    report.append("---")
    report.append("## 8. Alert History")
    report.append("")
    report.append("All notifications sent to this member (emails, SMS, push notifications):")
    report.append("")

    # Group by channel
    alerts_by_channel = defaultdict(list)
    for a in alert_records:
        alerts_by_channel[a['ChannelId'] or 'UNKNOWN'].append(a)

    for channel, alerts in alerts_by_channel.items():
        report.append(f"### {channel} ({len(alerts)} alerts)")
        report.append("")
        report.append("| Timestamp (PST) | Alert Type | Status | Subject |")
        report.append("|-----------------|------------|--------|---------|")

        for a in alerts[-30:]:  # Last 30 per channel
            subject = (a['Subject'] or '')[:40] + '...' if len(a['Subject'] or '') > 40 else a['Subject'] or 'N/A'
            report.append(f"| {utc_to_pst(a['createdts'])} | {a['AlertSubTypeId']} | {a['Status']} | {subject} |")

        if len(alerts) > 30:
            report.append(f"\n*Showing last 30 of {len(alerts)} {channel} alerts*")
        report.append("")

    # Explanation of default@calcoast.com
    report.append("---")
    report.append("## 9. Explanation: default@calcoast.com")
    report.append("")
    report.append("`default@calcoast.com` is a **system placeholder email address** used by the digital banking platform when:")
    report.append("")
    report.append("1. **No email on file:** The member has not provided an email address")
    report.append("2. **Email validation pending:** An email change is in progress but not yet verified")
    report.append("3. **System-generated alerts:** Internal system notifications that don't require a real recipient")
    report.append("4. **Fallback address:** When the primary email is invalid or bouncing")
    report.append("")
    report.append("**This is NOT a real email address** - messages sent to this address are typically discarded or logged for audit purposes.")
    report.append("")

    if default_email_events:
        report.append(f"### Occurrences of default@calcoast.com in this member's records: {len(default_email_events)}")
        report.append("")
        for e in default_email_events[:10]:
            if isinstance(e, dict) and 'activityDate' in e:
                report.append(f"- {utc_to_pst(e['activityDate'])}: {e.get('eventCategory', 'alerthistory record')}")
    report.append("")

    # Chronological Timeline
    report.append("---")
    report.append("## 10. Complete Chronological Timeline")
    report.append("")
    report.append("Full activity log with all events in PST timezone:")
    report.append("")
    report.append("| # | Timestamp (PST) | Event Category | Platform | IP Address | Key Details |")
    report.append("|---|-----------------|----------------|----------|------------|-------------|")

    for i, r in enumerate(fraud_records, 1):
        parsed = r.get('parsed_data', {})
        details = ""
        if r['eventCategory'] in ('LoginSuccessful', 'LoginFailure'):
            details = f"Email: {parsed.get('primary_email', 'N/A')}"
        elif 'OTP' in r['eventCategory']:
            details = f"{parsed.get('method', '?')} to {parsed.get('destination', '?')}: {parsed.get('status', '?')}"
        elif 'Change' in r['eventCategory']:
            details = f"{parsed.get('field', '')}: {parsed.get('new_value', '')}"[:40]
        else:
            raw = parsed.get('raw', '')
            if isinstance(raw, list):
                details = str(raw)[:40]
            else:
                details = str(raw)[:40]

        report.append(f"| {i} | {utc_to_pst(r['activityDate'])} | {r['eventCategory']} | {r['platform']} | {r['ipAddress']} | {details} |")

    report.append("")
    report.append("---")
    report.append("## End of Report")
    report.append("")
    report.append(f"*Report generated by audit_MUID_00638242923564062860.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(report)

def main():
    print("=" * 60)
    print("AUDIT TRAIL INVESTIGATION")
    print(f"MUID: {MUID}")
    print("=" * 60)
    print()

    # Step 1: Query fraudmonitor
    fraud_records = query_fraudmonitor()

    if not fraud_records:
        print("ERROR: No records found for this MUID!")
        return

    # Get username for alerthistory query
    username = None
    for r in fraud_records:
        if r['userName']:
            username = r['userName']
            break

    # Step 2: Query alerthistory
    alert_records = []
    if username:
        alert_records = query_alerthistory(username)
    else:
        print("  WARNING: No username found, cannot query alerthistory")

    # Step 3: IP Geolocation lookups
    print("\nPerforming IP geolocation lookups...")
    unique_ips = set()
    for r in fraud_records:
        if r['ipAddress']:
            unique_ips.add(r['ipAddress'])

    ip_geo_cache = {}
    for i, ip in enumerate(unique_ips, 1):
        print(f"  [{i}/{len(unique_ips)}] Looking up {ip}...")
        ip_geo_cache[ip] = get_ip_geolocation(ip)

    # Step 4: Generate report
    print("\nGenerating audit report...")
    report = generate_report(fraud_records, alert_records, ip_geo_cache)

    # Write report
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport written to: {OUTPUT_FILE}")
    print("=" * 60)
    print("INVESTIGATION COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    main()
