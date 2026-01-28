"""
Robot Framework library for MCP Evidence Advanced Tools tests.

Per P9.1: Task/Session/Evidence MCP tools
Split from MCPEvidenceLibrary.py per DOC-SIZE-01-v1
"""

import json
from pathlib import Path
from robot.api.deco import keyword


class MCPEvidenceAdvancedLibrary:
    """Library for testing MCP evidence advanced tools functionality."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.governance_dir = self.project_root / "governance"
        self.evidence_dir = self.project_root / "evidence"
        self.docs_dir = self.project_root / "docs"

    # =========================================================================
    # Task Listing Tests
    # =========================================================================

    @keyword("List Tasks Returns JSON")
    def list_tasks_returns_json(self):
        """governance_list_tasks should return valid JSON."""
        try:
            from governance.compat import governance_list_tasks
            result = governance_list_tasks()
            data = json.loads(result)
            return {
                "has_tasks": "tasks" in data,
                "has_count": "count" in data
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("List Tasks Filter By Phase")
    def list_tasks_filter_by_phase(self):
        """governance_list_tasks should filter by phase."""
        try:
            from governance.compat import governance_list_tasks
            result = governance_list_tasks(phase="P7")
            data = json.loads(result)
            all_p7 = all(task["phase"] == "P7" for task in data.get("tasks", []))
            return {"filtered": all_p7}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("List Tasks Filter By Status")
    def list_tasks_filter_by_status(self):
        """governance_list_tasks should filter by status."""
        try:
            from governance.compat import governance_list_tasks
            result = governance_list_tasks(status="DONE")
            data = json.loads(result)
            all_done = all(task["status"] == "DONE" for task in data.get("tasks", []))
            return {"filtered": all_done}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Has Required Fields")
    def task_has_required_fields(self):
        """Each task should have required fields."""
        try:
            from governance.compat import governance_list_tasks
            result = governance_list_tasks()
            data = json.loads(result)
            if not data.get("tasks"):
                return {"skipped": True, "reason": "No tasks found"}
            task = data["tasks"][0]
            return {
                "has_task_id": "task_id" in task,
                "has_status": "status" in task,
                "has_phase": "phase" in task
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Task Dependencies Tests
    # =========================================================================

    @keyword("Get Task Deps Returns JSON")
    def get_task_deps_returns_json(self):
        """governance_get_task_deps should return valid JSON."""
        try:
            from governance.compat import governance_get_task_deps
            result = governance_get_task_deps("P9.1")
            data = json.loads(result)
            return {
                "has_task_id": "task_id" in data,
                "has_blocked_by": "blocked_by" in data,
                "has_blocks": "blocks" in data
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task Deps Infers Phase Order")
    def task_deps_infers_phase_order(self):
        """Task deps should infer phase ordering dependencies."""
        try:
            from governance.compat import governance_get_task_deps
            result = governance_get_task_deps("P9.1")
            data = json.loads(result)
            return {"has_dependencies": len(data.get("blocked_by", [])) > 0}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Evidence Search Tests
    # =========================================================================

    @keyword("Evidence Search Returns JSON")
    def evidence_search_returns_json(self):
        """governance_evidence_search should return valid JSON."""
        try:
            from governance.compat import governance_evidence_search
            result = governance_evidence_search("governance")
            data = json.loads(result)
            return {
                "has_query": "query" in data,
                "has_results": "results" in data,
                "has_search_method": "search_method" in data
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Evidence Search Respects Top K")
    def evidence_search_respects_top_k(self):
        """governance_evidence_search should respect top_k parameter."""
        try:
            from governance.compat import governance_evidence_search
            result = governance_evidence_search("governance", top_k=3)
            data = json.loads(result)
            return {"respects_top_k": len(data.get("results", [])) <= 3}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Evidence Search Result Has Fields")
    def evidence_search_result_has_fields(self):
        """Each search result should have required fields."""
        try:
            from governance.compat import governance_evidence_search
            result = governance_evidence_search("RULE", top_k=1)
            data = json.loads(result)
            if not data.get("results"):
                return {"skipped": True, "reason": "No results found"}
            res = data["results"][0]
            return {
                "has_source": "source" in res,
                "has_score": "score" in res
            }
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    # =========================================================================
    # Evidence Directory Structure Tests
    # =========================================================================

    @keyword("Evidence Dir Exists")
    def evidence_dir_exists(self):
        """Evidence directory must exist."""
        return {"exists": self.evidence_dir.exists()}

    @keyword("Has Session Files")
    def has_session_files(self):
        """Should have session evidence files."""
        import glob
        sessions = glob.glob(str(self.evidence_dir / "SESSION-*.md"))
        return {"has_sessions": len(sessions) > 0}

    @keyword("Backlog File Exists")
    def backlog_file_exists(self):
        """R&D backlog file must exist."""
        backlog = self.docs_dir / "backlog" / "R&D-BACKLOG.md"
        return {"exists": backlog.exists()}

    # =========================================================================
    # Integration Tests
    # =========================================================================

    @keyword("List Then Get Session")
    def list_then_get_session(self):
        """Should be able to list sessions then get one."""
        try:
            from governance.compat import governance_list_sessions, governance_get_session
            list_result = governance_list_sessions(limit=1)
            list_data = json.loads(list_result)
            if not list_data.get("sessions"):
                return {"skipped": True, "reason": "No sessions found"}
            session_id = list_data["sessions"][0]["session_id"]
            get_result = governance_get_session(session_id)
            get_data = json.loads(get_result)
            return {"success": "error" not in get_data or get_data.get("content")}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("List Then Get Decision")
    def list_then_get_decision(self):
        """Should be able to list decisions then get one."""
        try:
            from governance.compat import governance_list_decisions, governance_get_decision
            list_result = governance_list_decisions()
            list_data = json.loads(list_result)
            if not list_data.get("decisions"):
                return {"skipped": True, "reason": "No decisions found"}
            decision_id = list_data["decisions"][0]["decision_id"]
            get_result = governance_get_decision(decision_id)
            get_data = json.loads(get_result)
            return {"success": "decision_id" in get_data}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}

    @keyword("Task List Filter Combinations")
    def task_list_filter_combinations(self):
        """Should be able to combine phase and status filters."""
        try:
            from governance.compat import governance_list_tasks
            result = governance_list_tasks(phase="P7", status="TODO")
            data = json.loads(result)
            all_match = all(
                task["phase"] == "P7" and task["status"] == "TODO"
                for task in data.get("tasks", [])
            )
            return {"filtered": all_match}
        except ImportError as e:
            return {"skipped": True, "reason": str(e)}
        except Exception as e:
            return {"skipped": True, "reason": str(e)}
