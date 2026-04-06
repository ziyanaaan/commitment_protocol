-- ============================================================================
-- BENEFICIARY ACCOUNTS MIGRATION
-- Target: Neon PostgreSQL
-- Purpose: Store ONLY gateway token references for payouts — NEVER raw bank details
-- ============================================================================

-- STEP 0 — ENABLE EXTENSION
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- STEP 1 — CREATE BENEFICIARY ACCOUNTS TABLE
-- ============================================================================

CREATE TABLE beneficiary_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    user_id UUID NOT NULL,
    
    gateway_contact_id TEXT NOT NULL,
    gateway_fund_account_id TEXT NOT NULL,
    
    account_type TEXT NOT NULL CHECK (
        account_type IN (
            'bank_account',
            'vpa',
            'wallet'
        )
    ),
    
    is_primary BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- STEP 2 — INDEXES
-- ============================================================================

CREATE INDEX idx_beneficiary_user
ON beneficiary_accounts(user_id);

-- ============================================================================
-- STEP 3 — ENFORCE ONLY ONE PRIMARY ACCOUNT PER USER
-- ============================================================================

CREATE UNIQUE INDEX uniq_primary_beneficiary_per_user
ON beneficiary_accounts(user_id)
WHERE is_primary = TRUE;
