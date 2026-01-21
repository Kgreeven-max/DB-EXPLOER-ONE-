"""
Debug the amount discrepancy
"""
import pandas as pd

# Read the Excel to check the math
df = pd.read_excel(r'C:\Users\kgreeven\Desktop\WALLET_ACTIVITY_FULL_REPORT.xlsx', sheet_name='SUMMARY')

print("Checking SUMMARY tab totals:")
print()

# Get totals from summary tab
mw_amount = df['PAN-07 Mobile Wallet - Amount ($)'].sum()
ct_amount = df['PAN-07 Physical Card - Amount ($)'].sum()
total = mw_amount + ct_amount

print(f"Mobile Wallet Amount: ${mw_amount:,.2f}")
print(f"Physical Card Amount: ${ct_amount:,.2f}")
print(f"SUMMARY Total:        ${total:,.2f}")
print()
print(f"Database PAN-07:      $34,675,080,196.34")
print(f"Difference:           ${34675080196.34 - total:,.2f}")
print()

# Check if the issue is the MIN calculation
# For each account: MWT + CT should equal the original P07 amount
# But we capped MWT at MIN(MW, P07) which is wrong for amounts

print("The issue: We used MIN(MW_Amount, P07_Amount) for Mobile Wallet")
print("This doesn't preserve the total PAN-07 amount correctly.")
print()
print("FIX: Card Tap Amount should be P07_Amount - MW_Amount (can go negative if MW > P07)")
print("But we clip to 0, losing that amount.")
