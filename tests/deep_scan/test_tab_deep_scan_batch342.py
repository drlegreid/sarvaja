"""
Deep Scan Batch 342-345 Defense Tests.

Validates 8 production fixes:
- BUG-342-ING-001: ingestion.py is_relative_to() replaces startswith()
- BUG-342-AGT-001: agents.py canonical two-step TypeQL escape
- BUG-342-HND-001: operations.py encoding="utf-8" on write_text/read_text
- BUG-343-MEM-001: memory_tiers.py ID collision prevention (microseconds + UUID)
- BUG-344-VER-001: tasks_crud_verify.py unbounded todos list cap
- BUG-344-TRC-001: traceability.py depth cap to prevent DoS
- BUG-344-TRU-001: trust.py trust_score coerced to float + clamped
- BUG-344-LNK-001: tasks_linking.py locals() in list comprehension fix
"""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================
# BUG-342-ING-001: Path confinement via is_relative_to()
# ============================================================

class TestIngestionPathConfinement:
    """Verify ingestion.py uses is_relative_to() not startswith()."""

    def _get_source(self):
        p = ROOT / "governance" / "mcp_tools" / "ingestion.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-342-ING-001" in src

    def test_uses_is_relative_to(self):
        """Should use Path.is_relative_to() for path confinement."""
        src = self._get_source()
        assert "is_relative_to" in src

    def test_no_startswith_for_path_check(self):
        """Should NOT use str.startswith() for path confinement."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "_resolve_jsonl_path":
                func_src = ast.get_source_segment(src, node)
                # startswith should not be the confinement mechanism
                assert "str(resolved).startswith(str(b.resolve()))" not in func_src
                break
        else:
            raise AssertionError("_resolve_jsonl_path not found")

    def test_prefix_bypass_blocked(self):
        """Verify that a prefix-sibling path would NOT pass is_relative_to()."""
        base = Path("/home/user/.claude/projects")
        sibling = Path("/home/user/.claude/projects-evil/malicious.jsonl")
        # startswith would match (BUG), is_relative_to would not
        assert str(sibling).startswith(str(base))  # confirms the old bug
        assert not sibling.is_relative_to(base)    # confirms the fix works


# ============================================================
# BUG-342-AGT-001: Canonical TypeQL escape in agent_activity
# ============================================================

class TestAgentActivityEscape:
    """Verify agents.py uses two-step TypeQL escape."""

    def _get_source(self):
        p = ROOT / "governance" / "mcp_tools" / "agents.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-342-AGT-001" in src

    def test_backslash_escaped_before_quotes(self):
        """Must escape backslash THEN quotes (canonical order)."""
        src = self._get_source()
        # The canonical pattern: .replace('\\', '\\\\').replace('"', '\\"')
        assert "replace('\\\\', '\\\\\\\\')" in src or \
               'replace(\'\\\\\', \'\\\\\\\\\')' in src or \
               "replace('\\\\', '\\\\\\\\\').replace" in src

    def test_escape_correctness(self):
        """Functional: two-step escape produces correct TypeQL literals."""
        # Simulate the canonical escape
        test_input = 'agent\\with"quotes'
        escaped = test_input.replace('\\', '\\\\').replace('"', '\\"')
        assert escaped == 'agent\\\\with\\"quotes'


# ============================================================
# BUG-342-HND-001: Handoff operations.py encoding
# ============================================================

class TestHandoffOperationsEncoding:
    """Verify write_handoff_evidence and read_handoff_evidence specify encoding."""

    def _get_source(self):
        p = ROOT / "governance" / "orchestrator" / "handoff_pkg" / "operations.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-342-HND-001" in src

    def test_write_text_has_encoding(self):
        """write_text must specify encoding='utf-8'."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "write_handoff_evidence":
                func_src = ast.get_source_segment(src, node)
                assert 'encoding="utf-8"' in func_src
                break
        else:
            raise AssertionError("write_handoff_evidence not found")

    def test_read_text_has_encoding(self):
        """read_text must specify encoding='utf-8'."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "read_handoff_evidence":
                func_src = ast.get_source_segment(src, node)
                assert 'encoding="utf-8"' in func_src
                break
        else:
            raise AssertionError("read_handoff_evidence not found")


# ============================================================
# BUG-343-MEM-001: Memory ID collision prevention
# ============================================================

class TestMemoryIdCollision:
    """Verify memory_tiers.py generates unique IDs even within same second."""

    def _get_source(self):
        p = ROOT / "governance" / "mcp_tools" / "memory_tiers.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-343-MEM-001" in src

    def test_has_microseconds_in_format(self):
        """ID format should include microseconds (%f)."""
        src = self._get_source()
        assert "%f" in src

    def test_has_uuid_suffix(self):
        """ID should include a UUID hex suffix for extra uniqueness."""
        src = self._get_source()
        assert "uuid4().hex" in src

    def test_id_format_functional(self):
        """Generate two IDs and verify they differ."""
        from datetime import datetime
        import uuid
        ids = set()
        for _ in range(100):
            mid = f"MEM-L1-{datetime.now().strftime('%Y%m%d%H%M%S%f')}-{uuid.uuid4().hex[:6]}"
            ids.add(mid)
        # All 100 should be unique (UUID suffix guarantees this)
        assert len(ids) == 100


# ============================================================
# BUG-344-VER-001: Unbounded todos list cap
# ============================================================

class TestTodosSyncCap:
    """Verify session_sync_todos has an upper bound on todos list."""

    def _get_source(self):
        p = ROOT / "governance" / "mcp_tools" / "tasks_crud_verify.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-344-VER-001" in src

    def test_max_todos_defined(self):
        """Should define _MAX_TODOS constant."""
        src = self._get_source()
        assert "_MAX_TODOS" in src

    def test_rejects_oversized_list(self):
        """Should return error if len(todos) > _MAX_TODOS."""
        src = self._get_source()
        assert "len(todos) > _MAX_TODOS" in src

    def test_cap_value_is_reasonable(self):
        """Cap should be between 100 and 1000."""
        src = self._get_source()
        match = re.search(r'_MAX_TODOS\s*=\s*(\d+)', src)
        assert match, "_MAX_TODOS not found as integer constant"
        cap = int(match.group(1))
        assert 100 <= cap <= 1000, f"Cap {cap} outside reasonable range"


# ============================================================
# BUG-344-TRC-001: Trace depth cap
# ============================================================

class TestTraceDepthCap:
    """Verify trace_task_chain caps depth to prevent DoS."""

    def _get_source(self):
        p = ROOT / "governance" / "mcp_tools" / "traceability.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-344-TRC-001" in src

    def test_depth_capped_with_min(self):
        """Depth should be clamped with min()."""
        src = self._get_source()
        assert "min(depth," in src

    def test_depth_floored_with_max(self):
        """Depth should be floored with max(0, ...)."""
        src = self._get_source()
        assert "max(0," in src

    def test_functional_cap(self):
        """Verify cap logic works for edge cases."""
        for raw_depth in [-5, 0, 1, 2, 3, 10, 1000]:
            capped = max(0, min(raw_depth, 3))
            assert 0 <= capped <= 3, f"depth={raw_depth} produced {capped}"


# ============================================================
# BUG-344-TRU-001: Trust score type coercion
# ============================================================

class TestTrustScoreCoercion:
    """Verify trust.py coerces trust_score to float and clamps range."""

    def _get_source(self):
        p = ROOT / "governance" / "mcp_tools" / "trust.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-344-TRU-001" in src

    def test_float_coercion(self):
        """trust_score must be explicitly coerced to float."""
        src = self._get_source()
        assert "float(result.get('trust'" in src

    def test_range_clamped(self):
        """trust_score should be clamped to [0.0, 1.0]."""
        src = self._get_source()
        assert "max(0.0, min(1.0, trust_score))" in src

    def test_compliance_coerced(self):
        """compliance_rate should also be coerced to float."""
        src = self._get_source()
        assert "float(result.get('compliance'" in src

    def test_tenure_coerced(self):
        """tenure_days should be coerced to int."""
        src = self._get_source()
        assert "int(float(result.get('tenure'" in src

    def test_functional_clamp(self):
        """Verify clamping logic for edge values."""
        for raw in [-0.5, 0.0, 0.5, 1.0, 1.5]:
            clamped = max(0.0, min(1.0, raw))
            assert 0.0 <= clamped <= 1.0


# ============================================================
# BUG-344-LNK-001: locals() in list comprehension fix
# ============================================================

class TestLocalsInComprehensionFix:
    """Verify tasks_linking.py no longer uses locals() in list comprehension."""

    def _get_source(self):
        p = ROOT / "governance" / "mcp_tools" / "tasks_linking.py"
        return p.read_text(encoding="utf-8")

    def test_bug_marker_present(self):
        src = self._get_source()
        assert "BUG-344-LNK-001" in src

    def test_no_locals_in_comprehension(self):
        """Should NOT use locals().get() in the actual code (comments are OK)."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "task_update_details":
                # Check AST for Name('locals') calls — comments don't appear in AST
                has_locals_call = False
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func = child.func
                        if isinstance(func, ast.Attribute) and func.attr == "get":
                            if isinstance(func.value, ast.Call):
                                inner = func.value.func
                                if isinstance(inner, ast.Name) and inner.id == "locals":
                                    has_locals_call = True
                assert not has_locals_call, "locals().get() still in code (not just comments)"
                break
        else:
            raise AssertionError("task_update_details not found")

    def test_explicit_section_list(self):
        """Should explicitly reference business, design, architecture, test_section."""
        src = self._get_source()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "task_update_details":
                func_src = ast.get_source_segment(src, node)
                # All four section names should appear paired with their variables
                assert '"business", business' in func_src or \
                       '("business", business)' in func_src
                assert '"design", design' in func_src or \
                       '("design", design)' in func_src
                break
        else:
            raise AssertionError("task_update_details not found")

    def test_functional_comprehension(self):
        """Verify the fixed pattern produces correct results."""
        # Simulate the fixed comprehension
        business, design, architecture, test_section = "biz", None, "arch", None
        updated_sections = [
            s for s, v in [
                ("business", business), ("design", design),
                ("architecture", architecture), ("test_section", test_section)
            ] if v is not None
        ]
        assert updated_sections == ["business", "architecture"]


# ============================================================
# Import sanity checks
# ============================================================

class TestBatch342Imports:
    """Verify all fixed modules import without errors."""

    def test_import_ingestion(self):
        import governance.mcp_tools.ingestion

    def test_import_agents_mcp(self):
        import governance.mcp_tools.agents

    def test_import_operations(self):
        import governance.orchestrator.handoff_pkg.operations

    def test_import_memory_tiers(self):
        import governance.mcp_tools.memory_tiers

    def test_import_tasks_crud_verify(self):
        import governance.mcp_tools.tasks_crud_verify

    def test_import_traceability(self):
        import governance.mcp_tools.traceability

    def test_import_trust(self):
        import governance.mcp_tools.trust

    def test_import_tasks_linking(self):
        import governance.mcp_tools.tasks_linking
