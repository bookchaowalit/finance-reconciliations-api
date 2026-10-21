"""Shared helpers for the reconciliations domain tests."""

from typing import Any

RECONCILIATIONS = "/v1/reconciliations"


def create(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {
        "period_start": "2026-09-01",
        "period_end": "2026-09-30",
        "source_type": "bank_statement",
        **fields,
    }
    return client.post(RECONCILIATIONS, headers=owner, json=body)
