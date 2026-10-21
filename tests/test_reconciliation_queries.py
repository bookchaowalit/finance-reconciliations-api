"""Listing, grouping and the lifecycle of a reconciliation."""

from reconciliations_helpers import RECONCILIATIONS, create


def ids(response):
    assert response.status_code == 200, response.text
    return [item["id"] for item in response.json()["items"]]


def test_list_filters_by_account_id(client, owner):
    mine = create(client, owner, account_id=21).json()
    create(client, owner, account_id=22)
    create(client, owner)
    listed = client.get(RECONCILIATIONS, headers=owner, params={"account_id": 21})
    assert ids(listed) == [mine["id"]]


def test_list_filters_by_status_and_source_type(client, owner):
    wanted = create(client, owner, status="exception", source_type="manual").json()
    create(client, owner, status="exception", source_type="wallet_export")
    create(client, owner, status="open", source_type="manual")
    listed = client.get(
        RECONCILIATIONS,
        headers=owner,
        params={"status": "exception", "source_type": "manual"},
    )
    assert ids(listed) == [wanted["id"]]


def test_a_filter_can_list_several_values(client, owner):
    open_one = create(client, owner, status="open").json()
    exception = create(client, owner, status="exception").json()
    create(client, owner, status="closed")
    listed = client.get(
        RECONCILIATIONS,
        headers=owner,
        params=[("status", "open"), ("status", "exception")],
    )
    assert sorted(ids(listed)) == sorted([open_one["id"], exception["id"]])


def test_an_unknown_filter_is_refused(client, owner):
    listed = client.get(RECONCILIATIONS, headers=owner, params={"currency": "THB"})
    assert listed.status_code == 422


def test_list_is_ordered_by_id(client, owner):
    first = create(client, owner, period_start="2026-09-01", period_end="2026-09-30")
    second = create(client, owner, period_start="2026-01-01", period_end="2026-01-31")
    first_id, second_id = first.json()["id"], second.json()["id"]
    assert ids(client.get(RECONCILIATIONS, headers=owner)) == [first_id, second_id]
    newest_first = client.get(RECONCILIATIONS, headers=owner, params={"order": "desc"})
    assert ids(newest_first) == [second_id, first_id]


def test_stats_count_reconciliations_per_status(client, owner):
    create(client, owner, status="matched")
    create(client, owner, status="matched")
    create(client, owner)
    stats = client.get(
        f"{RECONCILIATIONS}/stats", headers=owner, params={"group_by": "status"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"] == {"matched": 2, "open": 1}


def test_stats_count_reconciliations_per_source_and_account(client, owner):
    create(client, owner, source_type="manual", account_id=1)
    create(client, owner, source_type="manual", account_id=2)
    create(client, owner, source_type="wallet_export", account_id=2)
    by_source = client.get(
        f"{RECONCILIATIONS}/stats", headers=owner, params={"group_by": "source_type"}
    )
    assert by_source.json()["groups"] == {"manual": 2, "wallet_export": 1}
    by_account = client.get(
        f"{RECONCILIATIONS}/stats",
        headers=owner,
        params={"group_by": "account_id", "source_type": "manual"},
    )
    assert by_account.json()["groups"] == {"1": 1, "2": 1}


def test_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    for field in ("period_start", "currency", "difference_amount", "source_ref"):
        stats = client.get(
            f"{RECONCILIATIONS}/stats", headers=owner, params={"group_by": field}
        )
        assert stats.status_code == 422, field


def test_matching_a_reconciliation_bumps_its_version(client, owner):
    reconciliation = create(client, owner, expected_amount=500).json()
    path = f"{RECONCILIATIONS}/{reconciliation['id']}"
    matched = client.patch(
        path,
        headers=owner,
        json={
            "status": "matched",
            "reconciled_amount": 500,
            "difference_amount": 0,
            "reconciled_at": "2026-10-01T09:30:00+00:00",
        },
    )
    assert matched.status_code == 200, matched.text
    assert matched.json()["status"] == "matched"
    assert matched.json()["difference_amount"] == 0
    assert matched.json()["reconciled_at"] is not None
    assert matched.json()["version"] == 2


def test_a_patch_that_changes_nothing_keeps_the_version(client, owner):
    reconciliation = create(client, owner, expected_amount=500, status="open").json()
    path = f"{RECONCILIATIONS}/{reconciliation['id']}"
    same = client.patch(
        path, headers=owner, json={"status": "open", "expected_amount": 500}
    )
    assert same.status_code == 200, same.text
    assert same.json()["version"] == 1


def test_a_stale_expected_version_is_refused(client, owner):
    reconciliation = create(client, owner).json()
    path = f"{RECONCILIATIONS}/{reconciliation['id']}"
    client.patch(path, headers=owner, json={"status": "exception"})
    stale = client.patch(
        path, headers=owner, json={"status": "closed", "expected_version": 1}
    )
    assert stale.status_code == 409, stale.text
    assert client.get(path, headers=owner).json()["status"] == "exception"


def test_deleting_a_reconciliation_removes_it(client, owner):
    reconciliation = create(client, owner).json()
    path = f"{RECONCILIATIONS}/{reconciliation['id']}"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404
    assert ids(client.get(RECONCILIATIONS, headers=owner)) == []


def test_a_reconciliation_that_does_not_exist_is_404(client, owner):
    assert client.get(f"{RECONCILIATIONS}/999999999", headers=owner).status_code == 404
    patched = client.patch(
        f"{RECONCILIATIONS}/999999999", headers=owner, json={"status": "closed"}
    )
    assert patched.status_code == 404
    deleted = client.delete(f"{RECONCILIATIONS}/999999999", headers=owner)
    assert deleted.status_code == 404
