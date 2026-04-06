-- Migration: Change commitment table to use public_id instead of integer id
-- for client and freelancer references

-- Step 1: Add new varchar columns
ALTER TABLE commitments ADD COLUMN client_public_id VARCHAR(40);
ALTER TABLE commitments ADD COLUMN freelancer_public_id VARCHAR(40);

-- Step 2: Migrate existing data (join with users table to get public_id)
UPDATE commitments c
SET client_public_id = u.public_id
FROM users u
WHERE c.client_id = u.id;

UPDATE commitments c
SET freelancer_public_id = u.public_id
FROM users u
WHERE c.freelancer_id = u.id;

-- Step 3: Drop old integer columns
ALTER TABLE commitments DROP COLUMN client_id;
ALTER TABLE commitments DROP COLUMN freelancer_id;

-- Step 4: Rename new columns to the original names
ALTER TABLE commitments RENAME COLUMN client_public_id TO client_id;
ALTER TABLE commitments RENAME COLUMN freelancer_public_id TO freelancer_id;

-- Step 5: Make columns NOT NULL and add index
ALTER TABLE commitments ALTER COLUMN client_id SET NOT NULL;
ALTER TABLE commitments ALTER COLUMN freelancer_id SET NOT NULL;

CREATE INDEX idx_commitments_client_id ON commitments(client_id);
CREATE INDEX idx_commitments_freelancer_id ON commitments(freelancer_id);
