"""Deep scan batch 179: Services cross-cut layer.

Batch 179 findings: 34 total, 1 confirmed fix, 33 rejected/deferred.
- BUG-LINKMINER-001: client.get_rule() wrong method name → get_rule_by_id().
- BUG-LINKMINER-001b: client.get_decision() does not exist on TypeDB client.
"""
import pytest
from pathlib import Path


# ── Link miner entity validation defense ──────────────


class TestLinkMinerEntityValidationDefense:
    """Verify _validate_entity_exists uses correct TypeDB client methods."""

    def test_rule_uses_get_rule_by_id(self):
        """Rule validation uses client.get_rule_by_id (not get_rule)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/cc_link_miner.py").read_text()
        start = src.index("def _validate_entity_exists")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "get_rule_by_id" in func
        # Must NOT use non-existent get_rule() method
        assert "get_rule(entity_id)" not in func

    def test_task_uses_get_task(self):
        """Task validation uses client.get_task (correct method)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/cc_link_miner.py").read_text()
        start = src.index("def _validate_entity_exists")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "client.get_task(entity_id)" in func

    def test_decision_uses_get_all_decisions(self):
        """Decision validation uses get_all_decisions filter (no get_decision)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/cc_link_miner.py").read_text()
        start = src.index("def _validate_entity_exists")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "get_all_decisions" in func
        # Must NOT use non-existent get_decision() method
        assert "client.get_decision(entity_id)" not in func

    def test_exception_handling_returns_false(self):
        """Exception in entity lookup returns False (not raised)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/cc_link_miner.py").read_text()
        start = src.index("def _validate_entity_exists")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "except Exception:" in func
        assert "exists = False" in func

    def test_cache_prevents_repeated_lookups(self):
        """Entity existence is cached per key to avoid repeated TypeDB queries."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/cc_link_miner.py").read_text()
        start = src.index("def _validate_entity_exists")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "cache[key]" in func


# ── TypeDB client method existence defense ──────────────


class TestTypeDBClientMethodsDefense:
    """Verify TypeDB client has expected methods for entity queries."""

    def test_get_rule_by_id_exists(self):
        """TypeDB rules module has get_rule_by_id method."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/rules/read.py").read_text()
        assert "def get_rule_by_id" in src

    def test_get_task_exists(self):
        """TypeDB tasks module has get_task method."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/tasks/read.py").read_text()
        assert "def get_task" in src

    def test_get_all_decisions_exists(self):
        """TypeDB decisions module has get_all_decisions method."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/typedb/queries/rules/decisions.py").read_text()
        assert "def get_all_decisions" in src


# ── Agent delete consistency defense ──────────────


class TestAgentDeleteConsistencyDefense:
    """Verify agent delete handles TypeDB failure properly."""

    def test_delete_logs_typedb_failure(self):
        """delete_agent logs warning on TypeDB failure (not silent)."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/agents.py").read_text()
        start = src.index("def delete_agent")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert "logger.warning" in func
        assert "TypeDB delete failed" in func

    def test_delete_records_audit(self):
        """delete_agent records audit on deletion."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/agents.py").read_text()
        start = src.index("def delete_agent")
        end = src.index("\ndef ", start + 1) if "\ndef " in src[start + 1:] else len(src)
        func = src[start:end]
        assert 'record_audit("DELETE"' in func


# ── Tasks mutations ordering defense ──────────────


class TestTasksMutationsOrderingDefense:
    """Verify update_task mutation ordering is documented."""

    def test_htask002_auto_assignment_exists(self):
        """H-TASK-002 auto-assignment logic exists in update_task."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/tasks_mutations.py").read_text()
        assert "H-TASK-002" in src
        assert 'agent_id = "code-agent"' in src

    def test_typedb_update_before_fallback(self):
        """TypeDB update happens before fallback store update."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/tasks_mutations.py").read_text()
        # TypeDB client usage should come before _tasks_store updates
        typedb_pos = src.index("client.update_task_status")
        fallback_pos = src.index("_tasks_store[task_id]")
        assert typedb_pos < fallback_pos


# ── Mine session links defense ──────────────


class TestMineSessionLinksDefense:
    """Verify mine_session_links function structure."""

    def test_mine_function_exists(self):
        """mine_session_links function exists."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/cc_link_miner.py").read_text()
        assert "def mine_session_links" in src

    def test_mine_has_dry_run_param(self):
        """mine_session_links has dry_run parameter."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/cc_link_miner.py").read_text()
        start = src.index("def mine_session_links")
        end = src.index("):", start)
        func_sig = src[start:end]
        assert "dry_run" in func_sig

    def test_mine_has_batch_size_param(self):
        """mine_session_links has batch_size parameter."""
        root = Path(__file__).parent.parent.parent
        src = (root / "governance/services/cc_link_miner.py").read_text()
        start = src.index("def mine_session_links")
        end = src.index("):", start)
        func_sig = src[start:end]
        assert "batch_size" in func_sig
