"""
Robot Framework Library for Composite Traceability MCP Tools.
Per A3: Full governance chain tracing (test → GAP → evidence → session → task → rule).

Created: 2026-01-28 | Per SESSION-EVID-01-v1, GOV-TRANSP-01-v1.
"""

import json
from robot.api.deco import keyword


def _try_import_traceability():
    """Try to import traceability module."""
    try:
        from governance.mcp_tools.traceability import (
            _trace_task, _trace_session, _trace_rule
        )
        return True
    except ImportError:
        return False


def _try_import_client():
    """Try to import TypeDB client."""
    try:
        from governance.mcp_tools.common import get_typedb_client
        return get_typedb_client
    except ImportError:
        return None


class TraceabilityLibrary:
    """Library for testing composite traceability MCP tools."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    # =========================================================================
    # Module Import Tests
    # =========================================================================

    @keyword("Traceability Module Imports Successfully")
    def traceability_module_imports(self):
        """Verify traceability module can be imported."""
        try:
            from governance.mcp_tools.traceability import register_traceability_tools
            return {"imported": True, "has_register": callable(register_traceability_tools)}
        except ImportError as e:
            return {"imported": False, "error": str(e)}

    @keyword("Traceability Has All Tool Functions")
    def traceability_has_all_functions(self):
        """Verify all 5 trace tools are defined."""
        try:
            from governance.mcp_tools import traceability
            functions = [
                "register_traceability_tools",
                "_trace_task", "_trace_session", "_trace_rule",
            ]
            found = {f: hasattr(traceability, f) for f in functions}
            return {"all_found": all(found.values()), "functions": found}
        except ImportError as e:
            return {"all_found": False, "error": str(e)}

    @keyword("Traceability Registered In Init")
    def traceability_registered_in_init(self):
        """Verify traceability is registered in __init__.py."""
        try:
            from governance.mcp_tools import register_traceability_tools
            return {"registered": True, "callable": callable(register_traceability_tools)}
        except ImportError:
            return {"registered": False}

    # =========================================================================
    # Helper Function Tests
    # =========================================================================

    @keyword("Trace Task Helper Returns Dict")
    def trace_task_helper_returns_dict(self):
        """Verify _trace_task returns a dict with expected keys."""
        if not _try_import_traceability():
            return {"skipped": True, "reason": "traceability module not available"}

        get_client = _try_import_client()
        if not get_client:
            return {"skipped": True, "reason": "TypeDB client not available"}

        from governance.mcp_tools.traceability import _trace_task

        client = get_client()
        try:
            if not client.connect():
                return {"skipped": True, "reason": "TypeDB not connected"}

            result = _trace_task(client, "NONEXISTENT-TASK-999")
            expected_keys = {"task_id"}
            has_keys = expected_keys.issubset(set(result.keys()))
            return {"is_dict": isinstance(result, dict), "has_task_id": has_keys}
        except Exception as e:
            return {"error": str(e)}
        finally:
            client.close()

    @keyword("Trace Session Helper Returns Dict")
    def trace_session_helper_returns_dict(self):
        """Verify _trace_session returns a dict with expected keys."""
        if not _try_import_traceability():
            return {"skipped": True, "reason": "traceability module not available"}

        get_client = _try_import_client()
        if not get_client:
            return {"skipped": True, "reason": "TypeDB client not available"}

        from governance.mcp_tools.traceability import _trace_session

        client = get_client()
        try:
            if not client.connect():
                return {"skipped": True, "reason": "TypeDB not connected"}

            result = _trace_session(client, "NONEXISTENT-SESSION-999")
            expected_keys = {"session_id"}
            has_keys = expected_keys.issubset(set(result.keys()))
            return {"is_dict": isinstance(result, dict), "has_session_id": has_keys}
        except Exception as e:
            return {"error": str(e)}
        finally:
            client.close()

    @keyword("Trace Rule Helper Returns Dict")
    def trace_rule_helper_returns_dict(self):
        """Verify _trace_rule returns a dict with expected keys."""
        if not _try_import_traceability():
            return {"skipped": True, "reason": "traceability module not available"}

        get_client = _try_import_client()
        if not get_client:
            return {"skipped": True, "reason": "TypeDB client not available"}

        from governance.mcp_tools.traceability import _trace_rule

        client = get_client()
        try:
            if not client.connect():
                return {"skipped": True, "reason": "TypeDB not connected"}

            result = _trace_rule(client, "NONEXISTENT-RULE-999")
            expected_keys = {"rule_id"}
            has_keys = expected_keys.issubset(set(result.keys()))
            return {"is_dict": isinstance(result, dict), "has_rule_id": has_keys}
        except Exception as e:
            return {"error": str(e)}
        finally:
            client.close()

    # =========================================================================
    # Tool Registration Tests
    # =========================================================================

    @keyword("Register Traceability Tools With Mock")
    def register_with_mock(self):
        """Verify register_traceability_tools registers 5 tools on a mock MCP."""
        try:
            from governance.mcp_tools.traceability import register_traceability_tools
        except ImportError:
            return {"skipped": True, "reason": "traceability module not available"}

        registered = []

        class MockMCP:
            def tool(self_mcp):
                def decorator(func):
                    registered.append(func.__name__)
                    return func
                return decorator

        register_traceability_tools(MockMCP())

        expected = [
            "trace_task_chain", "trace_session_chain",
            "trace_rule_chain", "trace_gap_chain",
            "trace_evidence_chain"
        ]
        return {
            "registered": registered,
            "count": len(registered),
            "expected_count": len(expected),
            "all_present": set(expected) == set(registered),
            "missing": list(set(expected) - set(registered)),
        }

    @keyword("Trace Tools Have Docstrings")
    def trace_tools_have_docstrings(self):
        """Verify all trace tool functions have docstrings."""
        try:
            from governance.mcp_tools.traceability import register_traceability_tools
        except ImportError:
            return {"skipped": True, "reason": "traceability module not available"}

        docs = {}

        class DocCaptureMCP:
            def tool(self_mcp):
                def decorator(func):
                    docs[func.__name__] = bool(func.__doc__)
                    return func
                return decorator

        register_traceability_tools(DocCaptureMCP())
        return {"all_have_docs": all(docs.values()), "tools": docs}

    # =========================================================================
    # Integration Tests (require TypeDB)
    # =========================================================================

    @keyword("Trace Task Chain With Known Task")
    def trace_task_chain_known(self):
        """Test trace_task_chain with a known task from TypeDB."""
        get_client = _try_import_client()
        if not get_client:
            return {"skipped": True, "reason": "TypeDB client not available"}

        client = get_client()
        try:
            if not client.connect():
                return {"skipped": True, "reason": "TypeDB not connected"}

            # Find any task to trace
            tasks = client.get_all_tasks()
            if not tasks:
                return {"skipped": True, "reason": "No tasks in TypeDB"}

            task_id = getattr(tasks[0], "task_id", None)
            if not task_id:
                return {"skipped": True, "reason": "Task has no ID"}

            from governance.mcp_tools.traceability import _trace_task
            result = _trace_task(client, task_id)
            return {
                "success": "error" not in result,
                "task_id": task_id,
                "has_description": bool(result.get("description")),
                "has_status": bool(result.get("status")),
                "rule_count": len(result.get("linked_rules", [])),
                "session_count": len(result.get("linked_sessions", [])),
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            client.close()

    @keyword("Trace Session Chain With Known Session")
    def trace_session_chain_known(self):
        """Test trace_session_chain with a known session from TypeDB."""
        get_client = _try_import_client()
        if not get_client:
            return {"skipped": True, "reason": "TypeDB client not available"}

        client = get_client()
        try:
            if not client.connect():
                return {"skipped": True, "reason": "TypeDB not connected"}

            sessions = client.get_all_sessions()
            if not sessions:
                return {"skipped": True, "reason": "No sessions in TypeDB"}

            session_id = getattr(sessions[0], "session_id", None)
            if not session_id:
                return {"skipped": True, "reason": "Session has no ID"}

            from governance.mcp_tools.traceability import _trace_session
            result = _trace_session(client, session_id)
            return {
                "success": "error" not in result,
                "session_id": session_id,
                "evidence_count": len(result.get("evidence_files", [])),
                "rules_count": len(result.get("rules_applied", [])),
                "task_count": len(result.get("task_ids", [])),
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            client.close()

    @keyword("Trace Rule Chain With Known Rule")
    def trace_rule_chain_known(self):
        """Test trace_rule_chain with a known rule from TypeDB."""
        get_client = _try_import_client()
        if not get_client:
            return {"skipped": True, "reason": "TypeDB client not available"}

        client = get_client()
        try:
            if not client.connect():
                return {"skipped": True, "reason": "TypeDB not connected"}

            rules = client.get_active_rules()
            if not rules:
                return {"skipped": True, "reason": "No active rules in TypeDB"}

            rule_id = getattr(rules[0], "rule_id", None) or getattr(rules[0], "id", None)
            if not rule_id:
                return {"skipped": True, "reason": "Rule has no ID"}

            from governance.mcp_tools.traceability import _trace_rule
            result = _trace_rule(client, rule_id)
            return {
                "success": "error" not in result,
                "rule_id": rule_id,
                "has_name": bool(result.get("name")),
                "has_category": bool(result.get("category")),
                "dep_count": len(result.get("dependencies", [])),
            }
        except Exception as e:
            return {"error": str(e)}
        finally:
            client.close()
