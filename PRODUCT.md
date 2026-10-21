# Product

<!-- impeccable:product-schema 1 -->

## Platform

api

## Users

- The Solo Empire owner, through `life-dashboard-web` (which reaches the cell through
  `EMPIRE_RECONCILIATIONS_API`), `finance-portfolio-web` (reads
  `/api/finance/v1/reconciliations`), the cell's own MCP server (`reconciliations-mcp`) and the
  hosted tool hub (`platform-mcp-remote-worker`).
- Automations with an `empire-platform` token, within the permissions
  `reconciliations.reconciliation:read|write|delete`.
- The cell points at an account by its plain id `account_id` (`finance-accounts-api`). Other
  consumers [ต้องยืนยัน].

## Product Purpose

The record of checking an account against a statement or export for a period: which account,
which period, where the figures came from (bank statement, wallet export, invoice register,
manual), the expected, reconciled and difference amounts, and whether the check is open, matched,
an exception or closed.

Success: each period check is recorded with a valid period and a known source, and an open or
exception check is visible until it is matched or closed.

## Positioning

One capability, one service: its own API (Railway), its own database (Neon) with row-level
security per workspace, and authorization, executions and audit through `empire-platform`. It is
workspace-scoped, so the same service can serve other tenants without code changes.

## Operating Context

- Production: `https://reconciliations-api-production.up.railway.app` (`/health`), deployed by
  merging to `main` after CI.
- Data starts empty (created 2026-10-12 from the retired `finance_*` tables' fields); imports keep
  old ids in `legacy_id`.
- Monitored by `platform-uptime-worker`; errors go to Sentry when `SENTRY_DSN` is set.

## Capabilities and Constraints

- `/v1/reconciliations`: list (filters `account_id`, `status`, `source_type`; ordered by id,
  `order=desc` reverses), stats (`group_by` one of those filters), get, get-by-legacy-id, create
  (with `Idempotency-Key`), patch (with `expected_version`), delete.
- Rules: `period_start`, `period_end` and `source_type` are required; `source_type` is
  bank_statement, wallet_export, invoice_register, manual or other; `status` is open, matched,
  exception or closed (default open); `currency` defaults to THB (at most 12 characters);
  `reconciled_at` is a timestamp; unknown fields are refused.
- `period_end` cannot be before `period_start` (422 `invalid_value` naming both fields, on create
  and on patch); the same day for both is allowed.
- Amounts (`expected_amount`, `reconciled_amount`, `difference_amount`) may be negative and are
  not checked against each other: the cell stores the difference it is given.
- No uniqueness rule: an account can have several checks for the same period. `account_id` is
  not a foreign key and is not checked against the accounts service.
- An import (`legacy_id`) keeps the old id and may carry the original `created_at`/`updated_at`.
- Out of scope: fetching or parsing statements, matching individual transactions, and computing
  the difference.

## Measures

Proposed (nothing collects them yet):

- Reconciliations in status `open` or `exception` older than 30 days.
- Accounts with no `matched` or `closed` reconciliation in the last 35 days.
- 5xx rate and p95 latency on `/v1/reconciliations` (uptime worker and Sentry).
