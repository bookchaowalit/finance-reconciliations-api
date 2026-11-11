-- SPEC-003 (2026-11-11): exact money, ISO 4217 currency, workspace-defined scope (reconciliations).
-- Amounts move from double precision to numeric; currency codes must be three upper-case letters;
-- owner_scope (the owner's own life areas) becomes scope, a free label each workspace defines.
-- Append-only: do not edit once applied.

-- reconciliation
ALTER TABLE reconciliations.reconciliations NO FORCE ROW LEVEL SECURITY;
UPDATE reconciliations.reconciliations SET currency = upper(btrim(currency));
ALTER TABLE reconciliations.reconciliations FORCE ROW LEVEL SECURITY;
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'reconciliations.reconciliations'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'reconciliations.reconciliations'::regclass AND attname = 'expected_amount')] LOOP EXECUTE format('ALTER TABLE reconciliations.reconciliations DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE reconciliations.reconciliations ALTER COLUMN expected_amount TYPE numeric(19,4) USING expected_amount::numeric(19,4);
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'reconciliations.reconciliations'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'reconciliations.reconciliations'::regclass AND attname = 'reconciled_amount')] LOOP EXECUTE format('ALTER TABLE reconciliations.reconciliations DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE reconciliations.reconciliations ALTER COLUMN reconciled_amount TYPE numeric(19,4) USING reconciled_amount::numeric(19,4);
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'reconciliations.reconciliations'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'reconciliations.reconciliations'::regclass AND attname = 'difference_amount')] LOOP EXECUTE format('ALTER TABLE reconciliations.reconciliations DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE reconciliations.reconciliations ALTER COLUMN difference_amount TYPE numeric(19,4) USING difference_amount::numeric(19,4);
DO $$ DECLARE c text; BEGIN FOR c IN SELECT conname FROM pg_constraint WHERE conrelid = 'reconciliations.reconciliations'::regclass AND contype = 'c' AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'reconciliations.reconciliations'::regclass AND attname = 'currency')] LOOP EXECUTE format('ALTER TABLE reconciliations.reconciliations DROP CONSTRAINT %I', c); END LOOP; END $$;
ALTER TABLE reconciliations.reconciliations ADD CONSTRAINT reconciliations_currency_check CHECK (currency ~ '^[A-Z]{3}$');
