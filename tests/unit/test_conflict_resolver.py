"""
Unit tests for Sync Conflict Resolver.

Per DOC-SIZE-01-v1: Tests for agent/sync_agent/resolver.py.
Tests: ConflictResolver — strategies, resolve method.
"""

from datetime import datetime

from agent.sync_agent.resolver import ConflictResolver
from agent.sync_agent.models import Change


def _make_change(collection="skills", timestamp=None, **kwargs):
    """Create a Change with defaults."""
    ts = timestamp or datetime(2026, 1, 15, 12, 0, 0)
    return Change(
        collection=collection,
        doc_id=kwargs.get("doc_id", "D-1"),
        action=kwargs.get("action", "upsert"),
        data=kwargs.get("data", {}),
        timestamp=ts,
    )


# ── STRATEGIES constant ───────────────────────────────


class TestStrategies:
    def test_strategies_defined(self):
        assert "skills" in ConflictResolver.STRATEGIES
        assert "sessions" in ConflictResolver.STRATEGIES
        assert "rules" in ConflictResolver.STRATEGIES
        assert "memories" in ConflictResolver.STRATEGIES

    def test_strategy_values(self):
        assert ConflictResolver.STRATEGIES["skills"] == "merge_latest"
        assert ConflictResolver.STRATEGIES["sessions"] == "local_wins"
        assert ConflictResolver.STRATEGIES["rules"] == "remote_wins"
        assert ConflictResolver.STRATEGIES["memories"] == "merge_dedupe"


# ── resolve ────────────────────────────────────────────


class TestResolve:
    def test_skills_merge_latest_local_wins(self):
        resolver = ConflictResolver()
        local = _make_change("skills", datetime(2026, 1, 15, 12, 0, 0))
        remote = _make_change("skills", datetime(2026, 1, 14, 12, 0, 0))

        result = resolver.resolve(local, remote)
        assert result is local

    def test_skills_merge_latest_remote_wins(self):
        resolver = ConflictResolver()
        local = _make_change("skills", datetime(2026, 1, 14, 12, 0, 0))
        remote = _make_change("skills", datetime(2026, 1, 15, 12, 0, 0))

        result = resolver.resolve(local, remote)
        assert result is remote

    def test_rules_remote_wins(self):
        resolver = ConflictResolver()
        local = _make_change("rules", datetime(2026, 1, 15, 12, 0, 0))
        remote = _make_change("rules", datetime(2026, 1, 14, 12, 0, 0))

        # Even though local is newer, rules always picks remote
        result = resolver.resolve(local, remote)
        assert result is remote

    def test_sessions_local_wins(self):
        resolver = ConflictResolver()
        local = _make_change("sessions", datetime(2026, 1, 14, 12, 0, 0))
        remote = _make_change("sessions", datetime(2026, 1, 15, 12, 0, 0))

        # Even though remote is newer, sessions always picks local
        result = resolver.resolve(local, remote)
        assert result is local

    def test_memories_merge_dedupe_defaults_local(self):
        resolver = ConflictResolver()
        local = _make_change("memories")
        remote = _make_change("memories")

        # merge_dedupe falls through to local_wins
        result = resolver.resolve(local, remote)
        assert result is local

    def test_unknown_collection_defaults_local(self):
        resolver = ConflictResolver()
        local = _make_change("unknown_collection")
        remote = _make_change("unknown_collection")

        result = resolver.resolve(local, remote)
        assert result is local
