# finance-reconciliations-api
The Reconciliations cell: its own API (Railway, serverless) and its own Neon
database, first generated from `cell.yaml` (one of the ten finance
services split on 2026-10-12). It
reuses empire-platform for identity, authorization, executions and audit over
HTTP with the caller's token.

| | |
|---|---|
| API | Railway project `finance-reconciliations-api`, service `reconciliations-api` (Serverless) |
| Data | Neon project `finance-reconciliations-api`, database `reconciliations` |
| Registry | solo-empire `repository-catalog/registries/online-systems.yaml` (`reconciliations`) |

## API

Every resource has list, stats, get, get-by-legacy-id, create, patch and delete
(see `cellkit/app.py`). Permissions are `reconciliations.<resource>:read|write|delete`.

| Path | Resource | Filters |
|---|---|---|
| `/v1/reconciliations` | reconciliation | `account_id`, `status`, `source_type` |

## Develop and operate

```bash
uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/pytest -q
NEON_API_KEY=... .venv/bin/reconciliations-db provision
npm install && railway config apply && railway up --ci --service reconciliations-api
railway scale --service reconciliations-api asia-southeast1-eqsg3a=1 us-east4-eqdc4a=0   # next to Neon and the platform
```

Railway variables: `RECONCILIATIONS_DB_MODE=hosted`, `RECONCILIATIONS_DB_URL_API`,
`RECONCILIATIONS_JWT_PUBLIC_KEY_PEM`, `RECONCILIATIONS_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`.
