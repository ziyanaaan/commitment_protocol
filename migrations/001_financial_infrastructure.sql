-- ============================================================================
-- PRODUCTION FINANCIAL INFRASTRUCTURE MIGRATION
-- Target: Neon PostgreSQL
-- ============================================================================

-- STEP 0 — ENABLE EXTENSION
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- STEP 1 — CREATE LEDGER TABLE (APPEND-ONLY)
-- ============================================================================

CREATE TABLE ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    user_id UUID,
    commitment_id UUID,
    
    entry_type TEXT NOT NULL CHECK (
        entry_type IN (
            'payment_credit',
            'hold_debit',
            'hold_release',
            'payout_debit',
            'refund_debit',
            'fee_debit',
            'adjustment',
            'reversal'
        )
    ),
    
    amount BIGINT NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL DEFAULT 'INR',
    
    direction TEXT NOT NULL CHECK (
        direction IN ('credit', 'debit')
    ),
    
    reference_table TEXT NOT NULL,
    reference_id UUID NOT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ledger_user ON ledger_entries(user_id);
CREATE INDEX idx_ledger_commitment ON ledger_entries(commitment_id);
CREATE INDEX idx_ledger_created ON ledger_entries(created_at);

-- ============================================================================
-- STEP 2 — CREATE HOLDS TABLE (ESCROW LAYER)
-- ============================================================================

CREATE TABLE holds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    payment_id UUID NOT NULL,
    commitment_id UUID NOT NULL,
    
    total_amount BIGINT NOT NULL CHECK (total_amount > 0),
    released_amount BIGINT NOT NULL DEFAULT 0,
    refunded_amount BIGINT NOT NULL DEFAULT 0,
    
    status TEXT NOT NULL CHECK (
        status IN (
            'active',
            'partially_released',
            'released',
            'consumed',
            'refunded'
        )
    ),
    
    created_at TIMESTAMPTZ DEFAULT now(),
    released_at TIMESTAMPTZ
);

ALTER TABLE holds
ADD CONSTRAINT holds_amount_check
CHECK (released_amount + refunded_amount <= total_amount);

CREATE INDEX idx_holds_commitment ON holds(commitment_id);
CREATE INDEX idx_holds_payment ON holds(payment_id);
CREATE INDEX idx_holds_status ON holds(status);

-- ============================================================================
-- STEP 3 — CREATE PAYOUTS TABLE (MONEY LEAVING PLATFORM)
-- ============================================================================

CREATE TABLE payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    commitment_id UUID NOT NULL,
    user_id UUID NOT NULL,
    
    amount BIGINT NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL DEFAULT 'INR',
    
    status TEXT NOT NULL CHECK (
        status IN (
            'queued',
            'processing',
            'completed',
            'failed',
            'retrying',
            'reversed'
        )
    ),
    
    gateway_payout_id TEXT,
    
    idempotency_key TEXT NOT NULL UNIQUE,
    
    retry_count INT NOT NULL DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_payout_status ON payouts(status);
CREATE INDEX idx_payout_user ON payouts(user_id);
CREATE INDEX idx_payout_commitment ON payouts(commitment_id);

-- ============================================================================
-- STEP 4 — CREATE REFUNDS TABLE
-- ============================================================================

CREATE TABLE refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    payment_id UUID NOT NULL,
    commitment_id UUID NOT NULL,
    
    amount BIGINT NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL DEFAULT 'INR',
    
    status TEXT NOT NULL CHECK (
        status IN (
            'created',
            'pending_gateway',
            'processed',
            'failed'
        )
    ),
    
    gateway_refund_id TEXT,
    reason TEXT,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX idx_refunds_payment ON refunds(payment_id);
CREATE INDEX idx_refunds_commitment ON refunds(commitment_id);
CREATE INDEX idx_refunds_status ON refunds(status);

-- ============================================================================
-- STEP 5 — CREATE WEBHOOK EVENTS TABLE
-- ============================================================================

CREATE TABLE webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    gateway_event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    
    payload JSONB NOT NULL,
    
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_webhook_gateway_event ON webhook_events(gateway_event_id);
CREATE INDEX idx_webhook_processed ON webhook_events(processed);

-- ============================================================================
-- STEP 6 — CREATE ADMIN AUDIT LOGS TABLE
-- ============================================================================

CREATE TABLE admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    admin_id UUID,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    
    metadata JSONB,
    
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_admin_audit_admin ON admin_audit_logs(admin_id);
CREATE INDEX idx_admin_audit_action ON admin_audit_logs(action);
CREATE INDEX idx_admin_audit_created ON admin_audit_logs(created_at);

-- ============================================================================
-- STEP 7 — CREATE SYSTEM SETTINGS TABLE (KILL SWITCHES)
-- ============================================================================

CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    key TEXT NOT NULL UNIQUE,
    value BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,
    
    updated_by UUID,
    updated_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO system_settings (key, value, description) VALUES
    ('payouts_paused', FALSE, 'Kill switch: pause all freelancer payouts'),
    ('refunds_paused', FALSE, 'Kill switch: pause all client refunds'),
    ('all_transfers_paused', FALSE, 'Kill switch: pause all money movement');

-- ============================================================================
-- STEP 8 — MODIFY EXISTING PAYMENTS TABLE
-- ============================================================================

ALTER TABLE payments
ADD COLUMN IF NOT EXISTS gateway_payment_id TEXT UNIQUE,
ADD COLUMN IF NOT EXISTS captured_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS settled_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS available_for_payout_at TIMESTAMPTZ;

-- ============================================================================
-- STEP 9 — CREATE BALANCE SNAPSHOT TABLE (RECONCILIATION)
-- ============================================================================

CREATE TABLE balance_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    snapshot_date DATE NOT NULL UNIQUE,
    
    total_captured BIGINT NOT NULL DEFAULT 0,
    total_held BIGINT NOT NULL DEFAULT 0,
    total_released BIGINT NOT NULL DEFAULT 0,
    total_payouts BIGINT NOT NULL DEFAULT 0,
    total_refunds BIGINT NOT NULL DEFAULT 0,
    total_fees BIGINT NOT NULL DEFAULT 0,
    
    expected_balance BIGINT NOT NULL DEFAULT 0,
    actual_balance BIGINT,
    drift BIGINT,
    
    status TEXT NOT NULL CHECK (
        status IN ('pending', 'reconciled', 'drift_detected')
    ),
    
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_balance_snapshot_date ON balance_snapshots(snapshot_date);

-- ============================================================================
-- STEP 10 — CREATE FAILED OPERATIONS TABLE
-- ============================================================================

CREATE TABLE failed_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    operation_type TEXT NOT NULL CHECK (
        operation_type IN (
            'payout',
            'refund',
            'webhook',
            'settlement',
            'reconciliation'
        )
    ),
    
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    
    error_code TEXT,
    error_message TEXT,
    
    retry_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 3,
    
    status TEXT NOT NULL CHECK (
        status IN (
            'pending',
            'retrying',
            'resolved',
            'abandoned',
            'manual_review'
        )
    ),
    
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    next_retry_at TIMESTAMPTZ
);

CREATE INDEX idx_failed_ops_status ON failed_operations(status);
CREATE INDEX idx_failed_ops_type ON failed_operations(operation_type);
CREATE INDEX idx_failed_ops_created ON failed_operations(created_at);
