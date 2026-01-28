"""
Robot Framework Library for Evidence Backfill MCP Tools.
Per A4: Evidence backfill (session→evidence linking).

Created: 2026-01-28 | Per BACKFILL-OPS-01-v1, SESSION-EVID-01-v1.
"""

from robot.api.deco import keyword


class EvidenceBackfillLibrary:
    """Library for testing evidence backfill tools and scanner."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Scanner Import Tests
    # =========================================================================

    @keyword("Evidence Scanner Module Imports")
    def scanner_module_imports(self):
        """Verify evidence_scanner module imports."""
        try:
            from governance.evidence_scanner import (
                scan_all_evidence_files,
                scan_evidence_session_links,
                EVIDENCE_PATTERNS,
            )
            return {
                "imported": True,
                "pattern_count": len(EVIDENCE_PATTERNS),
                "patterns": list(EVIDENCE_PATTERNS.keys()),
            }
        except ImportError as e:
            return {"imported": False, "error": str(e)}

    @keyword("Evidence Backfill Tools Import")
    def backfill_tools_import(self):
        """Verify evidence_backfill MCP tools import."""
        try:
            from governance.mcp_tools.evidence_backfill import (
                register_evidence_backfill_tools,
            )
            return {"imported": True, "callable": callable(register_evidence_backfill_tools)}
        except ImportError as e:
            return {"imported": False, "error": str(e)}

    # =========================================================================
    # Pattern Tests
    # =========================================================================

    @keyword("Evidence Patterns Cover All Types")
    def patterns_cover_all_types(self):
        """Verify all evidence file types have patterns."""
        try:
            from governance.evidence_scanner import EVIDENCE_PATTERNS
            expected = {"SESSION-*.md", "DSM-*.md", "TEST-RUN-*.md", "DECISION-*.md"}
            actual = set(EVIDENCE_PATTERNS.keys())
            missing = expected - actual
            return {
                "count": len(actual),
                "covers_expected": len(missing) == 0,
                "missing": list(missing),
                "all_patterns": list(actual),
            }
        except ImportError as e:
            return {"error": str(e)}

    @keyword("Extract Task Refs From Content")
    def extract_task_refs_from_content(self):
        """Verify task reference extraction from sample content."""
        try:
            from governance.evidence_scanner import extract_task_refs

            content = """
            Completed P12.1 and P12.2 tasks.
            RD-001 research done. FH-001 hash implemented.
            Fixed GAP-UI-001 via UI-AUDIT-001.
            """
            refs = extract_task_refs(content)
            return {
                "count": len(refs),
                "refs": sorted(refs),
                "has_phase": "P12.1" in refs,
                "has_rd": "RD-001" in refs,
                "has_fh": "FH-001" in refs,
            }
        except ImportError as e:
            return {"error": str(e)}

    @keyword("Extract Rule Refs From Content")
    def extract_rule_refs_from_content(self):
        """Verify rule reference extraction from sample content."""
        try:
            from governance.evidence_scanner import extract_rule_refs

            content = """
            Per SESSION-EVID-01-v1: Evidence standards.
            Per RULE-001: Governance compliance.
            Applied TEST-GUARD-01-v1.
            """
            refs = extract_rule_refs(content)
            return {
                "count": len(refs),
                "refs": sorted(refs),
                "has_semantic": "SESSION-EVID-01-V1" in refs or "SESSION-EVID-01-v1" in refs,
                "has_legacy": "RULE-001" in refs,
            }
        except ImportError as e:
            return {"error": str(e)}

    @keyword("Extract Gap Refs From Content")
    def extract_gap_refs_from_content(self):
        """Verify gap reference extraction from sample content."""
        try:
            from governance.evidence_scanner import extract_gap_refs

            content = """
            Resolved GAP-UI-001 and GAP-MCP-002.
            Working on GAP-TEST-003.
            """
            refs = extract_gap_refs(content)
            return {
                "count": len(refs),
                "refs": sorted(refs),
                "has_gaps": len(refs) >= 3,
            }
        except ImportError as e:
            return {"error": str(e)}

    # =========================================================================
    # Scanner Function Tests
    # =========================================================================

    @keyword("Scan All Evidence Files Returns Results")
    def scan_all_evidence_returns_results(self):
        """Verify scan_all_evidence_files finds evidence files."""
        try:
            from governance.evidence_scanner import scan_all_evidence_files

            results = scan_all_evidence_files()
            return {
                "count": len(results),
                "has_results": len(results) > 0,
                "first_session_id": results[0].session_id if results else None,
                "first_file": results[0].file_path if results else None,
            }
        except Exception as e:
            return {"error": str(e)}

    @keyword("Scan Evidence Session Links Returns Result")
    def scan_evidence_session_links_result(self):
        """Verify scan_evidence_session_links returns EvidenceLinkResult."""
        try:
            from governance.evidence_scanner import scan_evidence_session_links

            result = scan_evidence_session_links()
            return {
                "scanned": result.scanned,
                "has_details": len(result.details) > 0,
                "first_detail": result.details[0] if result.details else None,
            }
        except Exception as e:
            return {"error": str(e)}

    # =========================================================================
    # MCP Tool Registration Tests
    # =========================================================================

    @keyword("Backfill Registers Five Tools")
    def backfill_registers_five_tools(self):
        """Verify register_evidence_backfill_tools registers 5 tools."""
        try:
            from governance.mcp_tools.evidence_backfill import (
                register_evidence_backfill_tools,
            )
        except ImportError:
            return {"skipped": True, "reason": "Module not available"}

        registered = []

        class MockMCP:
            def tool(self_mcp):
                def decorator(func):
                    registered.append(func.__name__)
                    return func
                return decorator

        register_evidence_backfill_tools(MockMCP())

        expected = [
            "backfill_scan_task_sessions",
            "backfill_execute_task_sessions",
            "backfill_scan_evidence_sessions",
            "backfill_execute_evidence_sessions",
            "backfill_scan_all_evidence",
        ]
        return {
            "registered": registered,
            "count": len(registered),
            "expected_count": len(expected),
            "all_present": set(expected) == set(registered),
            "missing": list(set(expected) - set(registered)),
        }

    @keyword("Format Evidence Link Summary Returns Dict")
    def format_evidence_link_summary_dict(self):
        """Verify format_evidence_link_summary returns expected structure."""
        try:
            from governance.evidence_scanner import (
                EvidenceLinkResult,
                format_evidence_link_summary,
            )

            result = EvidenceLinkResult(
                scanned=5, linked=3, skipped=1,
                errors=["test error"],
                details=[{"evidence_path": "test.md", "session_id": "TEST"}],
            )
            summary = format_evidence_link_summary(result)
            return {
                "is_dict": isinstance(summary, dict),
                "has_scanned": "scanned_files" in summary,
                "has_linked": "linked" in summary,
                "has_errors": "errors" in summary,
                "scanned_value": summary.get("scanned_files"),
            }
        except Exception as e:
            return {"error": str(e)}
