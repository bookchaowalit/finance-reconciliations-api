"""What reconciliations refuse: missing fields, unknown sources, wrong shapes, backwards periods."""

import pytest
from reconciliations_helpers import RECONCILIATIONS, create


@pytest.mark.parametrize("missing", ["period_start", "period_end", "source_type"])
def test_a_reconciliation_needs_a_period_and_a_source(client, owner, missing):
    body = {
        "period_start": "2026-09-01",
        "period_end": "2026-09-30",
        "source_type": "manual",
    }
    del body[missing]
    response = client.post(RECONCILIATIONS, headers=owner, json=body)
    assert response.status_code == 422, response.text


def test_source_type_must_be_a_known_source(client, owner):
    assert create(client, owner, source_type="telepathy").status_code == 422
    for source in (
        "bank_statement",
        "wallet_export",
        "invoice_register",
        "manual",
        "other",
    ):
        response = create(client, owner, source_type=source)
        assert response.status_code == 201, response.text


def test_status_must_be_a_known_state(client, owner):
    assert create(client, owner, status="pending").status_code == 422
    for state in ("open", "matched", "exception", "closed"):
        response = create(client, owner, status=state)
        assert response.status_code == 201, response.text


def test_currency_code_is_at_most_12_characters(client, owner):
    assert create(client, owner, currency="C" * 13).status_code == 422
    assert create(client, owner, currency="USD").status_code == 201


def test_amounts_must_be_numbers(client, owner):
    for field in ("expected_amount", "reconciled_amount", "difference_amount"):
        assert create(client, owner, **{field: "lots"}).status_code == 422, field


def test_a_difference_may_be_negative(client, owner):
    short = create(client, owner, difference_amount=-125.5)
    assert short.status_code == 201, short.text
    assert short.json()["difference_amount"] == -125.5


def test_dates_must_be_real_dates(client, owner):
    assert create(client, owner, period_start="2026-02-30").status_code == 422
    assert create(client, owner, period_end="end of month").status_code == 422


def test_reconciled_at_must_be_a_timestamp(client, owner):
    assert create(client, owner, reconciled_at="soon").status_code == 422
    done = create(client, owner, reconciled_at="2026-10-01T09:30:00+07:00")
    assert done.status_code == 201, done.text


def test_account_id_must_be_a_whole_number(client, owner):
    assert create(client, owner, account_id="main").status_code == 422
    assert create(client, owner, account_id=2.5).status_code == 422


def test_a_reconciliation_cannot_carry_fields_the_cell_does_not_know(client, owner):
    assert create(client, owner, bank="Kbank").status_code == 422


def test_a_period_cannot_end_before_it_starts(client, owner):
    backwards = create(
        client, owner, period_start="2026-09-30", period_end="2026-09-01"
    )
    assert backwards.status_code == 422, backwards.text
    assert backwards.json()["detail"] == {
        "error": "invalid_value",
        "fields": ["period_end", "period_start"],
    }
    one_day = create(client, owner, period_start="2026-09-30", period_end="2026-09-30")
    assert one_day.status_code == 201, one_day.text


def test_moving_the_period_end_before_its_start_is_refused_on_update(client, owner):
    reconciliation = create(client, owner).json()
    path = f"{RECONCILIATIONS}/{reconciliation['id']}"
    refused = client.patch(path, headers=owner, json={"period_end": "2026-08-31"})
    assert refused.status_code == 422, refused.text
    assert refused.json()["detail"]["fields"] == ["period_end", "period_start"]
    stored = client.get(path, headers=owner).json()
    assert stored["period_end"] == "2026-09-30"
    assert stored["version"] == 1
    # A patch that touches neither date still works.
    matched = client.patch(path, headers=owner, json={"status": "matched"})
    assert matched.status_code == 200, matched.text


def test_moving_the_period_start_after_its_end_is_refused_on_update(client, owner):
    reconciliation = create(client, owner).json()
    path = f"{RECONCILIATIONS}/{reconciliation['id']}"
    refused = client.patch(path, headers=owner, json={"period_start": "2026-10-01"})
    assert refused.status_code == 422, refused.text
    assert client.get(path, headers=owner).json()["period_start"] == "2026-09-01"


def test_both_dates_can_move_together(client, owner):
    reconciliation = create(client, owner).json()
    path = f"{RECONCILIATIONS}/{reconciliation['id']}"
    moved = client.patch(
        path,
        headers=owner,
        json={"period_start": "2026-10-01", "period_end": "2026-10-31"},
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["period_start"] == "2026-10-01"
    assert moved.json()["period_end"] == "2026-10-31"


def test_update_refuses_the_same_bad_values(client, owner):
    reconciliation = create(client, owner).json()
    path = f"{RECONCILIATIONS}/{reconciliation['id']}"
    bad_source = client.patch(path, headers=owner, json={"source_type": "dream"})
    assert bad_source.status_code == 422
    bad_status = client.patch(path, headers=owner, json={"status": "lost"})
    assert bad_status.status_code == 422
    assert client.get(path, headers=owner).json()["version"] == 1


def test_a_required_field_cannot_be_cleared(client, owner):
    reconciliation = create(client, owner).json()
    path = f"{RECONCILIATIONS}/{reconciliation['id']}"
    for field in ("period_start", "period_end", "source_type"):
        cleared = client.patch(path, headers=owner, json={field: None})
        assert cleared.status_code == 422, field
