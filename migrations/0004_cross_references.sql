-- SPEC-006 (2026-11-11): cross-service references between the finance cells (reconciliations).
-- Append-only: do not edit once applied.

-- The relay sends a record's events in insert order (the row lock makes it the commit order).
ALTER TABLE reconciliations.outbox ADD COLUMN seq bigint GENERATED ALWAYS AS IDENTITY;
DROP INDEX reconciliations.outbox_unrelayed;
CREATE INDEX outbox_unrelayed ON reconciliations.outbox (seq) WHERE relayed_at IS NULL;

-- SPEC-006: cross-service references, fed by finance.events.v1.
CREATE TABLE reconciliations.ref_targets (
    workspace_id   uuid NOT NULL,
    target         text NOT NULL,
    record_id      bigint NOT NULL,
    status         text,
    deleted        boolean NOT NULL DEFAULT false,
    record_version bigint NOT NULL DEFAULT 0,
    event_seq      bigint NOT NULL DEFAULT 0,
    updated_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, target, record_id)
);
CREATE TABLE reconciliations.ref_sources (
    workspace_id    uuid NOT NULL,
    source          text NOT NULL,
    source_id       bigint NOT NULL,
    field           text NOT NULL,
    target_resource text NOT NULL,
    target_id       bigint,
    deleted         boolean NOT NULL DEFAULT false,
    record_version  bigint NOT NULL DEFAULT 0,
    event_seq       bigint NOT NULL DEFAULT 0,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, source, source_id, field)
);
CREATE INDEX ref_sources_live ON reconciliations.ref_sources (workspace_id, target_resource, target_id) WHERE NOT deleted;
CREATE TABLE reconciliations.ref_offsets (
    topic       text NOT NULL,
    partition   integer NOT NULL,
    next_offset bigint NOT NULL,
    PRIMARY KEY (topic, partition)
);
ALTER TABLE reconciliations.ref_targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliations.ref_targets FORCE ROW LEVEL SECURITY;
CREATE POLICY workspace_isolation ON reconciliations.ref_targets USING (workspace_id = reconciliations.current_workspace());
CREATE POLICY publisher_sync ON reconciliations.ref_targets TO reconciliations_publisher USING (true) WITH CHECK (true);
GRANT SELECT ON reconciliations.ref_targets TO reconciliations_api;
GRANT SELECT, INSERT, UPDATE ON reconciliations.ref_targets TO reconciliations_publisher;
ALTER TABLE reconciliations.ref_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliations.ref_sources FORCE ROW LEVEL SECURITY;
CREATE POLICY workspace_isolation ON reconciliations.ref_sources USING (workspace_id = reconciliations.current_workspace());
CREATE POLICY publisher_sync ON reconciliations.ref_sources TO reconciliations_publisher USING (true) WITH CHECK (true);
GRANT SELECT ON reconciliations.ref_sources TO reconciliations_api;
GRANT SELECT, INSERT, UPDATE ON reconciliations.ref_sources TO reconciliations_publisher;
GRANT SELECT, INSERT, UPDATE ON reconciliations.ref_offsets TO reconciliations_publisher;

-- Rows written before SPEC-005 announce themselves once, so other cells learn their ids.
ALTER TABLE reconciliations.outbox NO FORCE ROW LEVEL SECURITY;
ALTER TABLE reconciliations.reconciliations NO FORCE ROW LEVEL SECURITY;
INSERT INTO reconciliations.outbox (workspace_id, type, subject, classification, payload, correlation_id) SELECT workspace_id, 'reconciliations.reconciliation.snapshot', 'empire:reconciliations:reconciliation:' || id, 'confidential', jsonb_build_object('account_id', account_id, 'period_start', period_start, 'period_end', period_end, 'source_type', source_type, 'currency', currency, 'status', status, 'version', version, 'deleted', false), 'spec-006-snapshot' FROM reconciliations.reconciliations ORDER BY id;
ALTER TABLE reconciliations.reconciliations FORCE ROW LEVEL SECURITY;
ALTER TABLE reconciliations.outbox FORCE ROW LEVEL SECURITY;
