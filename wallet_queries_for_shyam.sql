-- Wallet & Digital Banking Queries for Shyam
-- Run on DWHA, 2024+ data, open accounts only

-- Wallet activations
SELECT
    RTRIM(w.AccountNumber) AS AccountNumber,
    w.WalletType,
    w.ActivationDate
FROM History.DigitalWalletActivations w
INNER JOIN History.Account a ON w.AccountNumber = a.AccountNumber
WHERE w.ActivationDate >= '2024-01-01'
  AND a.CloseDate IS NULL
ORDER BY w.ActivationDate DESC


-- Digital banking enrollment dates
SELECT
    RTRIM(ParentAccount) AS AccountNumber,
    MIN(CREATIONDATE) AS DigitalBankingActivated
FROM SymWarehouse.TrackingAccount.v64_OnlineBankingTracking
WHERE CREATIONDATE IS NOT NULL
GROUP BY ParentAccount
ORDER BY DigitalBankingActivated DESC


-- PAN-07 contactless txns (2024 archive)
SELECT
    RTRIM(p.AccountNumber) AS AccountNumber,
    p.LocalTransactionDate,
    p.AmountIn1 AS Amount
FROM ATMArchive.dbo.RAW_Production2024 p
INNER JOIN History.Account a ON p.AccountNumber = a.AccountNumber
WHERE p.PANEntryMode = '07'
  AND p.LocalTransactionDate >= '2024-01-01'
  AND a.CloseDate IS NULL
ORDER BY p.LocalTransactionDate DESC


-- PAN-07 contactless txns (2025+ current)
SELECT
    RTRIM(p.AccountNumber) AS AccountNumber,
    p.LocalTransactionDate,
    p.AmountIn1 AS Amount
FROM AtmDialog.Raw_Production p
INNER JOIN History.Account a ON p.AccountNumber = a.AccountNumber
WHERE p.PANEntryMode = '07'
  AND p.LocalTransactionDate >= '2025-01-01'
  AND a.CloseDate IS NULL
ORDER BY p.LocalTransactionDate DESC


-- Mobile wallet transactions (apple/google/samsung pay)
SELECT
    RTRIM(w.AccountNumber) AS AccountNumber,
    w.WalletType,
    w.LocalTransactionDate,
    w.TransactionAmount
FROM History.DigitalWalletTransactions w
INNER JOIN History.Account a ON w.AccountNumber = a.AccountNumber
WHERE w.LocalTransactionDate >= '2024-01-01'
  AND a.CloseDate IS NULL
ORDER BY w.LocalTransactionDate DESC
