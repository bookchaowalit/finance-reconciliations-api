"""Defaults and duplicates of a reconciliation."""

from datetime import UTC, datetime

from reconciliations_helpers import RECONCILIATIONS, create


def test_new_reconciliation_defaults_to_open_thb(client, owner):
    response = create(client, owner)
    assert response.status_code == 201, response.text
    reconciliation = response.json()
    assert reconciliation["status"] == "open"
    assert reconciliation["currency"] == "THB"
    assert reconciliation["version"] == 1
    assert reconciliation["account_id"] is None
    assert reconciliation["reconciled_at"] is None
    assert reconciliation["expected_amount"] is None


def test_defaults_can_be_overridden(client, owner):
    reconciliation = create(
        client, owner, status="matched", currency="USD", account_id=5
    ).json()
    assert reconciliation["status"] == "matched"
    assert reconciliation["currency"] == "USD"
    assert reconciliation["account_id"] == 5


def test_amounts_keep_their_decimal_value(client, owner):
    reconciliation = create(
        client,
        owner,
        expected_amount=10250.75,
        reconciled_amount=10200.25,
        difference_amount=50.5,
    ).json()
    assert reconciliation["expected_amount"] == 10250.75
    assert reconciliation["reconciled_amount"] == 10200.25
    assert reconciliation["difference_amount"] == 50.5


def test_an_account_can_be_reconciled_for_the_same_period_twice(client, owner):
    first = create(client, owner, account_id=3)
    second = create(client, owner, account_id=3)
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] != second.json()["id"]


def test_account_id_is_not_checked_against_the_accounts_service(client, owner):
    response = create(client, owner, account_id=987654321)
    assert response.status_code == 201, response.text
    assert response.json()["account_id"] == 987654321


def test_an_import_keeps_the_old_id(client, owner):
    imported = create(client, owner, legacy_id=2718, source_ref="stmt-2026-09.pdf")
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 2718
    found = client.get(f"{RECONCILIATIONS}/legacy/2718", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["source_ref"] == "stmt-2026-09.pdf"
    assert create(client, owner, legacy_id=2718).status_code == 409


def test_an_import_may_carry_its_original_timestamps(client, owner):
    imported = create(
        client,
        owner,
        legacy_id=2719,
        created_at="2021-04-05T06:07:08+00:00",
        updated_at="2021-05-06T07:08:09+00:00",
    )
    assert imported.status_code == 201, imported.text
    created = datetime.fromisoformat(imported.json()["created_at"])
    assert created == datetime(2021, 4, 5, 6, 7, 8, tzinfo=UTC)
    refused = create(client, owner, created_at="2021-04-05T06:07:08+00:00")
    assert refused.status_code == 422, refused.text
