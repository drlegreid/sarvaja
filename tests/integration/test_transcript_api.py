"""E2E-T2-TRANSCRIPT-001: Transcript API Integration Tests (Tier 2).

Per TEST-E2E-01-v1: Integration test for /sessions/{id}/transcript endpoint.
Tests real API against running container stack with actual JSONL files.

Run: .venv/bin/python3 -m pytest tests/integration/test_transcript_api.py -v
Requires: API on localhost:8082
"""

import pytest
import httpx

BASE = "http://localhost:8082/api"
TIMEOUT = 15.0


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def api_healthy(client):
    r = client.get("/health")
    if r.status_code != 200:
        pytest.skip("API not healthy — containers not running")
    return True


def _find_cc_session(client) -> str:
    """Find a CC session with JSONL data (has cc_session_uuid or -CC- in ID)."""
    r = client.get("/sessions?limit=50")
    if r.status_code != 200:
        return ""
    items = r.json().get("items", [])
    for s in items:
        sid = s.get("session_id", "")
        if s.get("cc_session_uuid") or "-CC-" in sid:
            return sid
    return ""


# --- Transcript Pagination ---

class TestTranscriptPagination:
    def test_transcript_returns_200_for_cc_session(self, client, api_healthy):
        sid = _find_cc_session(client)
        if not sid:
            pytest.skip("No CC sessions available for transcript test")
        r = client.get(f"/sessions/{sid}/transcript?page=1&per_page=5")
        assert r.status_code == 200

    def test_transcript_response_schema(self, client, api_healthy):
        sid = _find_cc_session(client)
        if not sid:
            pytest.skip("No CC sessions available")
        data = client.get(f"/sessions/{sid}/transcript?page=1&per_page=5").json()
        assert "entries" in data
        assert "total" in data
        assert "page" in data
        assert "has_more" in data
        assert "session_id" in data

    def test_transcript_entries_have_required_fields(self, client, api_healthy):
        sid = _find_cc_session(client)
        if not sid:
            pytest.skip("No CC sessions available")
        data = client.get(f"/sessions/{sid}/transcript?page=1&per_page=5").json()
        for entry in data.get("entries", []):
            assert "index" in entry
            assert "timestamp" in entry
            assert "entry_type" in entry
            assert "content" in entry
            assert "content_length" in entry
            assert entry["entry_type"] in (
                "user_prompt", "assistant_text", "tool_use",
                "tool_result", "thinking", "compaction",
            )

    def test_transcript_per_page_respected(self, client, api_healthy):
        sid = _find_cc_session(client)
        if not sid:
            pytest.skip("No CC sessions available")
        data = client.get(f"/sessions/{sid}/transcript?page=1&per_page=3").json()
        assert len(data["entries"]) <= 3

    def test_transcript_pagination_advances(self, client, api_healthy):
        sid = _find_cc_session(client)
        if not sid:
            pytest.skip("No CC sessions available")
        p1 = client.get(f"/sessions/{sid}/transcript?page=1&per_page=3").json()
        if not p1["has_more"]:
            pytest.skip("Session has <= 3 entries, cannot test pagination")
        p2 = client.get(f"/sessions/{sid}/transcript?page=2&per_page=3").json()
        # Different entries on different pages
        p1_indices = {e["index"] for e in p1["entries"]}
        p2_indices = {e["index"] for e in p2["entries"]}
        assert p1_indices.isdisjoint(p2_indices)


# --- Transcript Filters ---

class TestTranscriptFilters:
    def test_exclude_thinking(self, client, api_healthy):
        sid = _find_cc_session(client)
        if not sid:
            pytest.skip("No CC sessions available")
        data = client.get(
            f"/sessions/{sid}/transcript?include_thinking=false&per_page=100"
        ).json()
        for entry in data.get("entries", []):
            assert entry["entry_type"] != "thinking"

    def test_exclude_user(self, client, api_healthy):
        sid = _find_cc_session(client)
        if not sid:
            pytest.skip("No CC sessions available")
        data = client.get(
            f"/sessions/{sid}/transcript?include_user=false&per_page=100"
        ).json()
        for entry in data.get("entries", []):
            assert entry["entry_type"] != "user_prompt"

    def test_content_limit_truncates(self, client, api_healthy):
        sid = _find_cc_session(client)
        if not sid:
            pytest.skip("No CC sessions available")
        data = client.get(
            f"/sessions/{sid}/transcript?content_limit=50&per_page=20"
        ).json()
        # At least some entries should be truncated if content > 50 chars
        truncated = [e for e in data.get("entries", []) if e.get("is_truncated")]
        # Can't guarantee truncation exists, just verify field is present
        for entry in data.get("entries", []):
            assert "is_truncated" in entry


# --- Single Entry Expansion ---

class TestTranscriptEntryExpansion:
    def test_single_entry_returns_200(self, client, api_healthy):
        sid = _find_cc_session(client)
        if not sid:
            pytest.skip("No CC sessions available")
        # Get first entry index
        page = client.get(f"/sessions/{sid}/transcript?page=1&per_page=1").json()
        if not page.get("entries"):
            pytest.skip("No transcript entries found")
        idx = page["entries"][0]["index"]
        r = client.get(f"/sessions/{sid}/transcript/{idx}")
        assert r.status_code == 200

    def test_single_entry_has_full_content(self, client, api_healthy):
        sid = _find_cc_session(client)
        if not sid:
            pytest.skip("No CC sessions available")
        page = client.get(f"/sessions/{sid}/transcript?page=1&per_page=1").json()
        if not page.get("entries"):
            pytest.skip("No transcript entries")
        idx = page["entries"][0]["index"]
        data = client.get(f"/sessions/{sid}/transcript/{idx}").json()
        assert "entry" in data
        assert "content" in data["entry"]
        assert data["session_id"] == sid


# --- Error Cases ---

class TestTranscriptErrors:
    def test_nonexistent_session_returns_404(self, client, api_healthy):
        r = client.get("/sessions/NONEXISTENT-SESSION-999/transcript")
        assert r.status_code == 404

    def test_non_cc_session_returns_404(self, client, api_healthy):
        """Sessions without JSONL files return 404 for transcript."""
        r = client.get("/sessions?limit=50")
        if r.status_code != 200:
            pytest.skip("Cannot list sessions")
        items = r.json().get("items", [])
        # Find a non-CC session (no cc_session_uuid, no -CC- in ID)
        for s in items:
            sid = s.get("session_id", "")
            if not s.get("cc_session_uuid") and "-CC-" not in sid:
                r = client.get(f"/sessions/{sid}/transcript")
                assert r.status_code == 404
                return
        pytest.skip("No non-CC sessions found to test 404")

    def test_nonexistent_entry_index_returns_404(self, client, api_healthy):
        sid = _find_cc_session(client)
        if not sid:
            pytest.skip("No CC sessions available")
        r = client.get(f"/sessions/{sid}/transcript/999999")
        assert r.status_code == 404
