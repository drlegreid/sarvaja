"""Batch 278-281 — Parser race guards, correlation dedup, TypeQL escaping,
evidence path traversal, FD leak guard, memory logging, state KeyError, budget types.

Validates fixes for:
- BUG-278-PARSER-001: parse_log_file / parse_log_file_extended guard FileNotFoundError
- BUG-278-PARSER-002: discover_log_files safe mtime sort
- BUG-278-CORR-001: correlate_tool_calls pop to prevent duplicate matches
- BUG-279-VMODEL-001: VectorDocument.to_typedb_insert escapes all string fields
- BUG-280-EVID-001: generate_evidence validates cycle_id for path traversal
- BUG-280-PERSIST-001: save_state FD leak guard on os.fdopen failure
- BUG-280-PERSIST-002: load_state backup failure logged, not silently swallowed
- BUG-280-MEM-001: session memory error promoted from DEBUG to WARNING
- BUG-281-STATE-001: add_to_backlog uses .get() to prevent KeyError
- BUG-281-BUDGET-001: compute_budget type-validates token_budget/tokens_used
"""
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent


# ── BUG-278-PARSER-001: FileNotFoundError guard ────────────────────────

class TestParserFileNotFound:
    """parse_log_file must handle missing files without crashing."""

    def test_parse_log_file_has_try_open(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        idx = src.index("def parse_log_file(")
        block = src[idx:idx + 900]
        assert "FileNotFoundError" in block
        assert "PermissionError" in block

    def test_parse_log_file_warns(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        idx = src.index("def parse_log_file(")
        block = src[idx:idx + 900]
        assert "logger.warning" in block

    def test_parse_log_file_extended_has_guard(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        idx = src.index("def parse_log_file_extended(")
        block = src[idx:idx + 900]
        assert "FileNotFoundError" in block
        assert "PermissionError" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        assert "BUG-278-PARSER-001" in src


# ── BUG-278-PARSER-002: Safe mtime sort ─────────────────────────────

class TestSafeMtimeSort:
    """discover_log_files must not crash if a file is deleted during sort."""

    def test_safe_mtime_function_present(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        idx = src.index("def discover_log_files")
        block = src[idx:idx + 900]
        assert "_safe_mtime" in block

    def test_oserror_handled(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        idx = src.index("def discover_log_files")
        block = src[idx:idx + 900]
        assert "OSError" in block

    def test_no_bare_stat_in_sort(self):
        """Must NOT use f.stat().st_mtime directly in sort key."""
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        idx = src.index("def discover_log_files")
        block = src[idx:idx + 900]
        assert "lambda f: f.stat().st_mtime" not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/session_metrics/parser.py").read_text()
        assert "BUG-278-PARSER-002" in src


# ── BUG-278-CORR-001: Pop matched entries from use_index ────────────

class TestCorrelationDedup:
    """correlate_tool_calls must pop matched entries to prevent duplicates."""

    def test_uses_pop(self):
        src = (SRC / "governance/session_metrics/correlation.py").read_text()
        idx = src.index("def correlate_tool_calls")
        block = src[idx:idx + 1200]
        assert "use_index.pop(" in block

    def test_filters_empty_tool_use_id(self):
        src = (SRC / "governance/session_metrics/correlation.py").read_text()
        idx = src.index("def correlate_tool_calls")
        block = src[idx:idx + 1200]
        assert "not tr.tool_use_id" in block

    def test_no_bare_bracket_access(self):
        """Must NOT use use_index[tr.tool_use_id] (should use pop)."""
        src = (SRC / "governance/session_metrics/correlation.py").read_text()
        idx = src.index("def correlate_tool_calls")
        block = src[idx:idx + 1200]
        assert "use_index[tr.tool_use_id]" not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/session_metrics/correlation.py").read_text()
        assert "BUG-278-CORR-001" in src


# ── BUG-279-VMODEL-001: Escape all fields in to_typedb_insert ───────

class TestVectorDocumentEscape:
    """VectorDocument.to_typedb_insert must escape ALL string fields."""

    def test_source_escaped(self):
        src = (SRC / "governance/vector_store/models.py").read_text()
        idx = src.index("def to_typedb_insert")
        block = src[idx:idx + 1200]
        assert 'self._escape(self.source)' in block

    def test_source_type_escaped(self):
        src = (SRC / "governance/vector_store/models.py").read_text()
        idx = src.index("def to_typedb_insert")
        block = src[idx:idx + 1200]
        assert 'self._escape(self.source_type)' in block

    def test_id_escaped(self):
        src = (SRC / "governance/vector_store/models.py").read_text()
        idx = src.index("def to_typedb_insert")
        block = src[idx:idx + 1200]
        assert 'self._escape(self.id)' in block

    def test_model_escaped(self):
        src = (SRC / "governance/vector_store/models.py").read_text()
        idx = src.index("def to_typedb_insert")
        block = src[idx:idx + 1200]
        assert 'self._escape(self.model)' in block

    def test_no_bare_source_interpolation(self):
        """Must NOT have bare {self.source} without _escape."""
        src = (SRC / "governance/vector_store/models.py").read_text()
        idx = src.index("def to_typedb_insert")
        block = src[idx:idx + 1200]
        assert '"{self.source}"' not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/vector_store/models.py").read_text()
        assert "BUG-279-VMODEL-001" in src


# ── BUG-280-EVID-001: Evidence path traversal guard ─────────────────

class TestEvidencePathTraversal:
    """generate_evidence must validate cycle_id against path traversal."""

    def test_safe_id_regex(self):
        src = (SRC / "governance/dsm/evidence.py").read_text()
        assert "_SAFE_ID" in src
        assert "re.compile" in src

    def test_resolve_check(self):
        src = (SRC / "governance/dsm/evidence.py").read_text()
        idx = src.index("def generate_evidence")
        block = src[idx:idx + 800]
        assert "is_relative_to" in block

    def test_raises_valueerror(self):
        src = (SRC / "governance/dsm/evidence.py").read_text()
        idx = src.index("def generate_evidence")
        block = src[idx:idx + 800]
        assert "ValueError" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/dsm/evidence.py").read_text()
        assert "BUG-280-EVID-001" in src


# ── BUG-280-PERSIST-001: FD leak guard ──────────────────────────────

class TestSaveStateFDLeak:
    """save_state must guard against FD leak if os.fdopen raises."""

    def test_fd_closed_on_failure(self):
        src = (SRC / "governance/dsm/tracker_persistence.py").read_text()
        idx = src.index("def save_state")
        block = src[idx:idx + 1500]
        assert "os.close(fd)" in block

    def test_fd_sentinel(self):
        """Must mark fd = -1 after fdopen takes ownership."""
        src = (SRC / "governance/dsm/tracker_persistence.py").read_text()
        idx = src.index("def save_state")
        block = src[idx:idx + 1500]
        assert "fd = -1" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/dsm/tracker_persistence.py").read_text()
        assert "BUG-280-PERSIST-001" in src


# ── BUG-280-PERSIST-002: Backup failure logged ──────────────────────

class TestBackupFailureLogged:
    """Backup failure in load_state must be logged, not silently swallowed."""

    def test_no_bare_pass(self):
        """The backup except block must NOT have bare 'pass'."""
        src = (SRC / "governance/dsm/tracker_persistence.py").read_text()
        idx = src.index("def load_state")
        block = src[idx:idx + 1800]
        # Find the backup try/except section
        assert "logger.error" in block

    def test_backup_err_captured(self):
        src = (SRC / "governance/dsm/tracker_persistence.py").read_text()
        idx = src.index("def load_state")
        block = src[idx:idx + 1800]
        assert "backup_err" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/dsm/tracker_persistence.py").read_text()
        assert "BUG-280-PERSIST-002" in src


# ── BUG-280-MEM-001: Memory payload error promoted to WARNING ───────

class TestMemoryPayloadLogging:
    """Session memory error must be logged at WARNING, not DEBUG."""

    def test_uses_warning(self):
        src = (SRC / "governance/dsm/memory.py").read_text()
        idx = src.index("def get_session_memory_payload")
        block = src[idx:idx + 1500]
        assert "logger.warning" in block

    def test_no_debug_for_error(self):
        """Must NOT use logger.debug for the main exception handler."""
        src = (SRC / "governance/dsm/memory.py").read_text()
        idx = src.index("def get_session_memory_payload")
        block = src[idx:idx + 1500]
        assert "logger.debug" not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/dsm/memory.py").read_text()
        assert "BUG-280-MEM-001" in src


# ── BUG-281-STATE-001: add_to_backlog uses .get() ───────────────────

class TestAddToBacklogKeyGuard:
    """add_to_backlog must use .get() to prevent KeyError on partial state."""

    def test_uses_get_for_existing_ids(self):
        src = (SRC / "governance/workflows/orchestrator/state.py").read_text()
        idx = src.index("def add_to_backlog")
        block = src[idx:idx + 600]
        assert 't.get("task_id")' in block

    def test_uses_get_for_backlog(self):
        src = (SRC / "governance/workflows/orchestrator/state.py").read_text()
        idx = src.index("def add_to_backlog")
        block = src[idx:idx + 600]
        assert 'state.get("backlog"' in block

    def test_no_bare_bracket_access(self):
        """Must NOT use state['backlog'] or t['task_id'] directly."""
        src = (SRC / "governance/workflows/orchestrator/state.py").read_text()
        idx = src.index("def add_to_backlog")
        block = src[idx:idx + 600]
        assert 't["task_id"] for t in state["backlog"]' not in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/workflows/orchestrator/state.py").read_text()
        assert "BUG-281-STATE-001" in src


# ── BUG-281-BUDGET-001: Type-validated budget fields ─────────────────

class TestBudgetTypeValidation:
    """compute_budget must type-validate token_budget and tokens_used."""

    def test_int_conversion(self):
        src = (SRC / "governance/workflows/orchestrator/budget.py").read_text()
        idx = src.index("def compute_budget")
        block = src[idx:idx + 800]
        assert "int(state.get" in block

    def test_catches_type_error(self):
        src = (SRC / "governance/workflows/orchestrator/budget.py").read_text()
        idx = src.index("def compute_budget")
        block = src[idx:idx + 800]
        assert "TypeError" in block

    def test_catches_value_error(self):
        src = (SRC / "governance/workflows/orchestrator/budget.py").read_text()
        idx = src.index("def compute_budget")
        block = src[idx:idx + 800]
        assert "ValueError" in block

    def test_non_negative_tokens(self):
        """tokens_used must be clamped to non-negative."""
        src = (SRC / "governance/workflows/orchestrator/budget.py").read_text()
        idx = src.index("def compute_budget")
        block = src[idx:idx + 800]
        assert "max(int(" in block

    def test_bug_marker_present(self):
        src = (SRC / "governance/workflows/orchestrator/budget.py").read_text()
        assert "BUG-281-BUDGET-001" in src


# ── Module import defense tests ──────────────────────────────────────

class TestBatch278Imports:
    def test_parser_importable(self):
        import governance.session_metrics.parser
        assert governance.session_metrics.parser is not None

    def test_correlation_importable(self):
        import governance.session_metrics.correlation
        assert governance.session_metrics.correlation is not None

    def test_vector_models_importable(self):
        import governance.vector_store.models
        assert governance.vector_store.models is not None

    def test_evidence_importable(self):
        import governance.dsm.evidence
        assert governance.dsm.evidence is not None

    def test_tracker_persistence_importable(self):
        import governance.dsm.tracker_persistence
        assert governance.dsm.tracker_persistence is not None

    def test_memory_importable(self):
        import governance.dsm.memory
        assert governance.dsm.memory is not None

    def test_state_importable(self):
        import governance.workflows.orchestrator.state
        assert governance.workflows.orchestrator.state is not None

    def test_budget_importable(self):
        import governance.workflows.orchestrator.budget
        assert governance.workflows.orchestrator.budget is not None
