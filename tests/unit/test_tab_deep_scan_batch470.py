"""Batch 466-470 — Routes layer logger sanitization defense tests.

Validates BUG-466 through BUG-470: All logger.error/warning calls in
governance/routes/ use {type(e).__name__} instead of {e} to prevent
exception detail leakage into log aggregation dashboards.

Coverage: 25 route files, 138 total fixes across 5 batches.
"""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.parent
ROUTES = SRC / "governance" / "routes"

# Helper: find all logger.error/warning f-string calls with {e}/{pe} etc.
_RAW_EXC_PATTERN = re.compile(
    r'logger\.(error|warning)\(f".*\{(e|ae|le|se|ue|pe)\}',
)

_TYPE_PATTERN = re.compile(
    r'logger\.(error|warning)\(f".*\{type\((e|ae|le|se|ue|pe)\)\.__name__\}',
)


def _scan_file(filepath: Path) -> list:
    """Return list of line numbers with raw {e} in logger calls."""
    violations = []
    for i, line in enumerate(filepath.read_text().splitlines(), 1):
        if _RAW_EXC_PATTERN.search(line):
            violations.append(i)
    return violations


# ── Batch 466: routes/agents ──────────────────────────────────────────

class TestBatch466AgentsCrud:
    """BUG-466-ACR-001..007: routes/agents/crud.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "agents" / "crud.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_bug_markers_present(self):
        src = (ROUTES / "agents" / "crud.py").read_text()
        assert "BUG-466-ACR-001" in src


class TestBatch466AgentsObservability:
    """BUG-466-AOB-001..009: routes/agents/observability.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "agents" / "observability.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_bug_markers_present(self):
        src = (ROUTES / "agents" / "observability.py").read_text()
        assert "BUG-466-AOB-001" in src


class TestBatch466AgentsHelpers:
    """BUG-466-AHL-001: routes/agents/helpers.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "agents" / "helpers.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


# ── Batch 467: routes/sessions ────────────────────────────────────────

class TestBatch467SessionsCrud:
    """BUG-467-SCR-001..012: routes/sessions/crud.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "sessions" / "crud.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_bug_markers_present(self):
        src = (ROUTES / "sessions" / "crud.py").read_text()
        assert "BUG-467-SCR-001" in src


class TestBatch467SessionsDetail:
    """BUG-467-SDT-001..005: routes/sessions/detail.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "sessions" / "detail.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch467SessionsRelations:
    """BUG-467-SRL-001..003: routes/sessions/relations.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "sessions" / "relations.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


# ── Batch 468: routes/rules ───────────────────────────────────────────

class TestBatch468RulesCrud:
    """BUG-468-RCR-001..016: routes/rules/crud.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "rules" / "crud.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_bug_markers_present(self):
        src = (ROUTES / "rules" / "crud.py").read_text()
        assert "BUG-468-RCR-001" in src


class TestBatch468Decisions:
    """BUG-468-DEC-001..012: routes/rules/decisions.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "rules" / "decisions.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


# ── Batch 469: routes/tasks+chat+tests ────────────────────────────────

class TestBatch469TasksCrud:
    """BUG-469-TCR-001..013: routes/tasks/crud.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "tasks" / "crud.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_bug_markers_present(self):
        src = (ROUTES / "tasks" / "crud.py").read_text()
        assert "BUG-469-TCR-001" in src


class TestBatch469ChatCommands:
    """BUG-469-CMD-001..007: routes/chat/commands.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "chat" / "commands.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch469ChatEndpoints:
    """BUG-469-CHT-001..005: routes/chat/endpoints.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "chat" / "endpoints.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch469SessionBridge:
    """BUG-469-BRG-001..006: routes/chat/session_bridge.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "chat" / "session_bridge.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch469Delegation:
    """BUG-469-DEL-001..002: routes/chat/endpoints_delegation.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "chat" / "endpoints_delegation.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch469HeuristicRunner:
    """BUG-469-HRN-001..004: routes/tests/heuristic_runner.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "tests" / "heuristic_runner.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch469RunnerStore:
    """BUG-469-RST-001..002: routes/tests/runner_store.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "tests" / "runner_store.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch469RunnerExec:
    """BUG-469-RXE-001..012: routes/tests/runner_exec.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "tests" / "runner_exec.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_bug_markers_present(self):
        src = (ROUTES / "tests" / "runner_exec.py").read_text()
        assert "BUG-469-RXE-001" in src


# ── Batch 470: remaining routes ───────────────────────────────────────

class TestBatch470Workflow:
    """BUG-470-WFL-001..006: routes/tasks/workflow.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "tasks" / "workflow.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_bug_markers_present(self):
        src = (ROUTES / "tasks" / "workflow.py").read_text()
        assert "BUG-470-WFL-001" in src


class TestBatch470Verification:
    """BUG-470-VER-001: routes/tasks/verification.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "tasks" / "verification.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch470Execution:
    """BUG-470-EXE-001: routes/tasks/execution.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "tasks" / "execution.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch470Evidence:
    """BUG-470-EVD-001..002: routes/evidence.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "evidence.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch470Proposals:
    """BUG-470-PRP-001: routes/proposals.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "proposals.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch470Infra:
    """BUG-470-INF-001: routes/infra.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "infra.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch470ProjectsCrud:
    """BUG-470-PRJ-001..004: routes/projects/crud.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "projects" / "crud.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"

    def test_exc_info_present(self):
        src = (ROUTES / "projects" / "crud.py").read_text()
        assert src.count("exc_info=True") >= 4


class TestBatch470HeuristicChecksCc:
    """BUG-470-HCC-001: routes/tests/heuristic_checks_cc.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "tests" / "heuristic_checks_cc.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch470HeuristicChecksSession:
    """BUG-470-HCS-001: routes/tests/heuristic_checks_session.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "tests" / "heuristic_checks_session.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


class TestBatch470Parser:
    """BUG-470-PAR-001: routes/tests/parser.py sanitized."""

    def test_no_raw_exception_in_logger(self):
        f = ROUTES / "tests" / "parser.py"
        assert not _scan_file(f), f"Raw {{e}} found in {f.name}"


# ── Meta: Full routes layer sweep ─────────────────────────────────────

class TestRoutesLayerFullSweep:
    """Verify the entire routes/ directory has zero raw {e} in logger calls."""

    def test_zero_violations_across_all_route_files(self):
        violations = {}
        for py_file in sorted(ROUTES.rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue
            found = _scan_file(py_file)
            if found:
                violations[str(py_file.relative_to(SRC))] = found
        assert not violations, f"Raw {{e}} still present in: {violations}"
