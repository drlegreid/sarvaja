"""Unit tests for TaskTestFactory.

SRVJ-FEAT-005: Verify factory creates, tracks, and cleans up tasks.
All HTTP calls mocked — no live services needed.
"""

import pytest
from unittest.mock import MagicMock, patch

from tests.shared.task_test_factory import (
    TaskTestFactory,
    CreatedTask,
    purge_test_artifacts,
    FACTORY_PREFIX,
    ALL_TEST_PREFIXES,
)


def _mock_client(post_status=201, delete_status=204, get_items=None):
    """Build a mock httpx.Client with configurable responses."""
    client = MagicMock()

    post_resp = MagicMock()
    post_resp.status_code = post_status
    post_resp.json.return_value = {"task_id": "E2E-MOCK0001"}
    post_resp.text = "error" if post_status != 201 else ""
    client.post.return_value = post_resp

    del_resp = MagicMock()
    del_resp.status_code = delete_status
    client.delete.return_value = del_resp

    if get_items is not None:
        get_resp = MagicMock()
        get_resp.status_code = 200
        get_resp.json.return_value = {"items": get_items}
        client.get.return_value = get_resp

    client.is_closed = False
    return client


# =============================================================================
# TaskTestFactory — create
# =============================================================================


class TestFactoryCreate:
    """Factory.create() generates IDs and tracks them."""

    def test_create_generates_prefixed_id(self):
        factory = TaskTestFactory(client=_mock_client())
        t = factory.create(summary="E2E > Test > Create > ID")
        assert t.task_id.startswith(f"{FACTORY_PREFIX}-")
        assert len(t.task_id) == 12  # "E2E-" + 8 hex

    def test_create_tracks_id(self):
        factory = TaskTestFactory(client=_mock_client())
        factory.create()
        factory.create()
        assert len(factory.created_ids) == 2

    def test_create_custom_task_id(self):
        factory = TaskTestFactory(client=_mock_client())
        t = factory.create(task_id="E2E-CUSTOM-001")
        assert t.task_id == "E2E-CUSTOM-001"
        assert "E2E-CUSTOM-001" in factory.created_ids

    def test_create_returns_created_task(self):
        factory = TaskTestFactory(client=_mock_client())
        t = factory.create()
        assert isinstance(t, CreatedTask)
        assert isinstance(t.response, dict)

    def test_create_sends_correct_payload(self):
        client = _mock_client()
        factory = TaskTestFactory(client=client)
        factory.create(
            summary="E2E > Test > Payload > Check",
            task_type="bug",
            priority="HIGH",
            workspace_id="WS-123",
        )
        call_args = client.post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert payload["summary"] == "E2E > Test > Payload > Check"
        assert payload["task_type"] == "bug"
        assert payload["priority"] == "HIGH"
        assert payload["workspace_id"] == "WS-123"
        assert payload["phase"] == "P10"

    def test_create_raises_on_non_201(self):
        factory = TaskTestFactory(client=_mock_client(post_status=500))
        with pytest.raises(RuntimeError, match="Factory create failed"):
            factory.create()

    def test_create_does_not_track_on_failure(self):
        factory = TaskTestFactory(client=_mock_client(post_status=422))
        with pytest.raises(RuntimeError):
            factory.create()
        assert len(factory.created_ids) == 0

    def test_create_kwargs_forwarded(self):
        client = _mock_client()
        factory = TaskTestFactory(client=client)
        factory.create(extra_field="value")
        payload = client.post.call_args.kwargs.get("json") or client.post.call_args[1].get("json")
        assert payload["extra_field"] == "value"


# =============================================================================
# TaskTestFactory — cleanup
# =============================================================================


class TestFactoryCleanup:
    """Factory.cleanup() deletes all tracked tasks."""

    def test_cleanup_deletes_all_tracked(self):
        factory = TaskTestFactory(client=_mock_client())
        factory._created = ["E2E-AAA", "E2E-BBB", "E2E-CCC"]
        stats = factory.cleanup()
        assert stats["deleted"] == 3
        assert stats["failed"] == 0
        assert factory.created_ids == []

    def test_cleanup_handles_404(self):
        factory = TaskTestFactory(client=_mock_client(delete_status=404))
        factory._created = ["E2E-GONE"]
        stats = factory.cleanup()
        assert stats["deleted"] == 1

    def test_cleanup_handles_500(self):
        factory = TaskTestFactory(client=_mock_client(delete_status=500))
        factory._created = ["E2E-FAIL"]
        stats = factory.cleanup()
        assert stats["failed"] == 1
        assert len(stats["errors"]) == 1

    def test_cleanup_handles_exception(self):
        client = _mock_client()
        client.delete.side_effect = Exception("connection refused")
        factory = TaskTestFactory(client=client)
        factory._created = ["E2E-ERR"]
        stats = factory.cleanup()
        assert stats["failed"] == 1

    def test_cleanup_clears_tracking_list(self):
        factory = TaskTestFactory(client=_mock_client())
        factory._created = ["E2E-X"]
        factory.cleanup()
        assert factory._created == []

    def test_cleanup_empty_is_noop(self):
        factory = TaskTestFactory(client=_mock_client())
        stats = factory.cleanup()
        assert stats["deleted"] == 0
        assert stats["failed"] == 0


# =============================================================================
# TaskTestFactory — lifecycle
# =============================================================================


class TestFactoryLifecycle:
    """Factory open/close lifecycle."""

    def test_close_closes_owned_client(self):
        client = _mock_client()
        factory = TaskTestFactory(client=client)
        factory._owns_client = True
        factory.close()
        client.close.assert_called_once()

    def test_close_skips_injected_client(self):
        client = _mock_client()
        factory = TaskTestFactory(client=client)
        # _owns_client is False when client is injected
        factory.close()
        client.close.assert_not_called()

    def test_auto_creates_client_when_none(self):
        factory = TaskTestFactory()
        assert factory._client is None
        # Accessing .client triggers creation
        c = factory.client
        assert c is not None
        assert factory._owns_client is True
        c.close()

    def test_created_ids_returns_copy(self):
        factory = TaskTestFactory(client=_mock_client())
        factory._created = ["E2E-X"]
        ids = factory.created_ids
        ids.append("E2E-Y")  # Mutate the copy
        assert "E2E-Y" not in factory._created


# =============================================================================
# purge_test_artifacts
# =============================================================================


class TestPurgeTestArtifacts:
    """purge_test_artifacts() sweeps matching tasks from API."""

    def test_purge_deletes_matching_prefixes(self):
        items = [
            {"task_id": "E2E-QUAL-RT-001"},
            {"task_id": "RF-QUAL-TEST-001"},
            {"task_id": "INTTEST-ABC"},
            {"task_id": "CRUD-XYZ"},
            {"task_id": "SRVJ-FEAT-001"},  # Should NOT be deleted
        ]
        client = _mock_client(get_items=items)
        # Second call returns empty to stop pagination
        first_resp = client.get.return_value
        empty_resp = MagicMock()
        empty_resp.status_code = 200
        empty_resp.json.return_value = {"items": []}
        client.get.side_effect = [first_resp, empty_resp]

        with patch("tests.shared.task_test_factory.httpx.Client") as MockClient:
            MockClient.return_value.__enter__ = MagicMock(return_value=client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            stats = purge_test_artifacts()

        assert stats["deleted"] == 4
        delete_calls = [c.args[0] for c in client.delete.call_args_list]
        assert "/tasks/SRVJ-FEAT-001" not in delete_calls

    def test_purge_custom_prefixes(self):
        items = [{"task_id": "CUSTOM-001"}, {"task_id": "OTHER-001"}]
        client = _mock_client(get_items=items)
        first_resp = client.get.return_value
        empty_resp = MagicMock()
        empty_resp.status_code = 200
        empty_resp.json.return_value = {"items": []}
        client.get.side_effect = [first_resp, empty_resp]

        with patch("tests.shared.task_test_factory.httpx.Client") as MockClient:
            MockClient.return_value.__enter__ = MagicMock(return_value=client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)
            stats = purge_test_artifacts(prefixes=["CUSTOM-"])

        assert stats["deleted"] == 1


# =============================================================================
# ALL_TEST_PREFIXES coverage
# =============================================================================


class TestPrefixes:
    """Verify prefix list is comprehensive."""

    def test_all_known_test_prefixes_included(self):
        expected = {"E2E-", "E2E-QUAL-", "RF-QUAL-", "INTTEST-", "CRUD-", "TEST-"}
        assert expected.issubset(set(ALL_TEST_PREFIXES))

    def test_factory_prefix_is_e2e(self):
        assert FACTORY_PREFIX == "E2E"
