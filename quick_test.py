"""Quick test to verify data access."""
from dwha_connection import get_dwha_connection
import pandas as pd

conn = get_dwha_connection()

print("Testing wallet activations...")
df = pd.read_sql("SELECT TOP 5 AccountNumber, WalletType FROM History.DigitalWalletActivations WHERE ActivationDate >= '2024-01-01'", conn)
print(f"  OK - {len(df)} rows")

print("Testing wallet transactions...")
df = pd.read_sql("SELECT TOP 5 AccountNumber, TransactionAmount FROM History.DigitalWalletTransactions WHERE LocalTransactionDate >= '2024-01-01'", conn)
print(f"  OK - {len(df)} rows")

print("Testing archive PAN-07...")
df = pd.read_sql("SELECT TOP 5 AccountNumber, AmountIn1 FROM ATMArchive.dbo.RAW_Production2024 WHERE PANEntryMode = '07'", conn)
print(f"  OK - {len(df)} rows")

print("Testing current PAN-07...")
df = pd.read_sql("SELECT TOP 5 AccountNumber, AmountIn1 FROM AtmDialog.Raw_Production WHERE PANEntryMode = '07'", conn)
print(f"  OK - {len(df)} rows")

print("\nAll tests passed!")
conn.close()
