"""
Evidence Viewing MCP Tools
==========================
Evidence artifact viewing operations (P9.1 - Strategic Platform).

Per RULE-012: DSP Semantic Code Structure
Per FP + Digital Twin Paradigm: Evidence entity module
"""

import json
import glob
import re
from pathlib import Path
from typing import Optional

from governance.mcp_tools.common import get_typedb_client

# Evidence paths
EVIDENCE_DIR = Path("evidence")
DOCS_DIR = Path("docs")
BACKLOG_DIR = DOCS_DIR / "backlog"

# Import rule quality analyzer (with fallback)
try:
    from governance.rule_quality import (
        RuleQualityAnalyzer,
        analyze_rule_quality,
        get_rule_impact,
        find_rule_issues
    )
    RULE_QUALITY_AVAILABLE = True
except ImportError:
    RULE_QUALITY_AVAILABLE = False


def register_evidence_tools(mcp) -> None:
    """Register evidence-related MCP tools."""

    @mcp.tool()
    def governance_list_sessions(
        limit: int = 20,
        session_type: Optional[str] = None
    ) -> str:
        """
        List all session evidence files.

        Args:
            limit: Maximum number of sessions to return (default 20)
            session_type: Filter by session type (e.g., "PHASE", "DSP", "STRATEGIC")

        Returns:
            JSON array of sessions with ID, date, topic, and summary
        """
        sessions = []

        # Search evidence directory for session files
        pattern = EVIDENCE_DIR / "SESSION-*.md"
        for filepath in sorted(glob.glob(str(pattern)), reverse=True)[:limit]:
            try:
                path = Path(filepath)
                filename = path.name

                # Parse filename: SESSION-YYYY-MM-DD-TOPIC.md
                parts = filename.replace(".md", "").split("-")
                if len(parts) >= 4:
                    date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"
                    topic = "-".join(parts[4:]) if len(parts) > 4 else "general"
                else:
                    date_str = "unknown"
                    topic = filename

                # Apply type filter
                if session_type and session_type.upper() not in topic.upper():
                    continue

                # Read first few lines for summary
                content = path.read_text(encoding="utf-8")
                lines = content.split("\n")
                summary = ""
                for line in lines[:10]:
                    if line.startswith("## Summary") or line.startswith("**Summary"):
                        idx = lines.index(line)
                        if idx + 1 < len(lines):
                            summary = lines[idx + 1].strip()
                        break

                sessions.append({
                    "session_id": filename.replace(".md", ""),
                    "date": date_str,
                    "topic": topic,
                    "summary": summary[:200] if summary else "No summary available",
                    "path": str(filepath)
                })

            except Exception:
                continue

        return json.dumps({
            "sessions": sessions,
            "count": len(sessions),
            "total_available": len(list(glob.glob(str(EVIDENCE_DIR / "SESSION-*.md"))))
        }, indent=2)

    @mcp.tool()
    def governance_get_session(session_id: str) -> str:
        """
        Get full session evidence content.

        Args:
            session_id: Session ID (e.g., "SESSION-2024-12-25-PHASE8")

        Returns:
            JSON object with session metadata and full markdown content
        """
        # Handle both with and without .md extension
        if not session_id.endswith(".md"):
            session_id = session_id + ".md"

        filepath = EVIDENCE_DIR / session_id

        if not filepath.exists():
            # Try without SESSION- prefix
            if not session_id.startswith("SESSION-"):
                filepath = EVIDENCE_DIR / f"SESSION-{session_id}"
            if not filepath.exists():
                return json.dumps({"error": f"Session not found: {session_id}"})

        try:
            content = filepath.read_text(encoding="utf-8")

            # Parse metadata from content
            lines = content.split("\n")
            metadata = {}
            for line in lines[:20]:
                if line.startswith("**Date:**"):
                    metadata["date"] = line.replace("**Date:**", "").strip()
                elif line.startswith("**Session ID:**"):
                    metadata["session_id"] = line.replace("**Session ID:**", "").strip()
                elif line.startswith("**Status:**"):
                    metadata["status"] = line.replace("**Status:**", "").strip()

            return json.dumps({
                "session_id": session_id.replace(".md", ""),
                "path": str(filepath),
                "metadata": metadata,
                "content": content,
                "lines": len(lines)
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to read session: {str(e)}"})

    @mcp.tool()
    def governance_list_decisions() -> str:
        """
        List all strategic decisions from TypeDB and evidence files.

        Returns:
            JSON array of decisions with ID, name, status, and date
        """
        decisions = []

        # Get from TypeDB
        client = get_typedb_client()
        try:
            if client.connect():
                db_decisions = client.get_all_decisions()
                for d in db_decisions:
                    decisions.append({
                        "decision_id": d.id,
                        "name": d.name,
                        "status": d.status,
                        "date": str(d.decision_date) if d.decision_date else None,
                        "source": "typedb"
                    })
                client.close()
        except Exception:
            pass

        # Also scan evidence directory for DECISION-*.md files
        pattern = EVIDENCE_DIR / "DECISION-*.md"
        for filepath in glob.glob(str(pattern)):
            try:
                path = Path(filepath)
                filename = path.name.replace(".md", "")
                # Check if already in list from TypeDB
                if not any(d["decision_id"] == filename for d in decisions):
                    content = path.read_text(encoding="utf-8")
                    # Extract title from first # heading
                    title = filename
                    for line in content.split("\n"):
                        if line.startswith("# "):
                            title = line[2:].strip()
                            break

                    decisions.append({
                        "decision_id": filename,
                        "name": title,
                        "status": "DOCUMENTED",
                        "date": None,
                        "source": "evidence_file"
                    })
            except Exception:
                continue

        return json.dumps({
            "decisions": decisions,
            "count": len(decisions)
        }, indent=2)

    @mcp.tool()
    def governance_get_decision(decision_id: str) -> str:
        """
        Get detailed decision information.

        Args:
            decision_id: Decision ID (e.g., "DECISION-003")

        Returns:
            JSON object with decision details, context, rationale, and impacts
        """
        result = {"decision_id": decision_id}

        # Get from TypeDB
        client = get_typedb_client()
        try:
            if client.connect():
                db_decisions = client.get_all_decisions()
                for d in db_decisions:
                    if d.id == decision_id:
                        result["name"] = d.name
                        result["context"] = d.context
                        result["rationale"] = d.rationale
                        result["status"] = d.status
                        result["date"] = str(d.decision_date) if d.decision_date else None
                        result["source"] = "typedb"

                        # Get impacts
                        impacts = client.get_decision_impacts(decision_id)
                        result["affected_rules"] = impacts
                        break

                client.close()
        except Exception:
            pass

        # Check for evidence file
        evidence_file = EVIDENCE_DIR / f"{decision_id}.md"
        if not evidence_file.exists():
            # Try with suffix
            matches = list(glob.glob(str(EVIDENCE_DIR / f"{decision_id}*.md")))
            if matches:
                evidence_file = Path(matches[0])

        if evidence_file.exists():
            result["evidence_file"] = str(evidence_file)
            result["evidence_content"] = evidence_file.read_text(encoding="utf-8")

        if len(result) == 1:  # Only has decision_id
            return json.dumps({"error": f"Decision {decision_id} not found"})

        return json.dumps(result, indent=2)

    @mcp.tool()
    def governance_list_tasks(
        phase: Optional[str] = None,
        status: Optional[str] = None
    ) -> str:
        """
        List R&D and backlog tasks.

        Args:
            phase: Filter by phase (e.g., "P7", "P9", "FH", "RD")
            status: Filter by status (e.g., "TODO", "DONE", "IN_PROGRESS")

        Returns:
            JSON array of tasks with ID, name, status, and priority
        """
        tasks = []

        # Parse R&D-BACKLOG.md
        backlog_file = BACKLOG_DIR / "R&D-BACKLOG.md"
        if backlog_file.exists():
            content = backlog_file.read_text(encoding="utf-8")

            # Parse task tables
            table_pattern = r"\|\s*([\w.-]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"

            for match in re.finditer(table_pattern, content):
                task_id, name_or_status, status_or_desc, priority_or_notes = match.groups()

                # Clean up
                task_id = task_id.strip()
                name_or_status = name_or_status.strip()
                status_or_desc = status_or_desc.strip()

                # Skip headers and separators
                if task_id in ("ID", "Task", "Pillar", "Factor") or task_id.startswith("-"):
                    continue
                if not re.match(r'^(P\d+\.\d+|RD-\d+|FH-\d+)', task_id):
                    continue

                # Normalize status
                if "✅" in status_or_desc or "DONE" in status_or_desc:
                    task_status = "DONE"
                elif "📋" in status_or_desc or "TODO" in status_or_desc:
                    task_status = "TODO"
                elif "⏸️" in status_or_desc or "BLOCKED" in status_or_desc:
                    task_status = "BLOCKED"
                elif "🔄" in status_or_desc or "IN_PROGRESS" in status_or_desc:
                    task_status = "IN_PROGRESS"
                else:
                    task_status = "TODO"

                # Determine phase from ID
                task_phase = "UNKNOWN"
                if task_id.startswith("P"):
                    task_phase = task_id.split(".")[0]
                elif task_id.startswith("RD-"):
                    task_phase = "RD"
                elif task_id.startswith("FH-"):
                    task_phase = "FH"

                # Apply filters
                if phase and task_phase != phase:
                    continue
                if status and task_status != status:
                    continue

                tasks.append({
                    "task_id": task_id,
                    "name": name_or_status[:100],
                    "status": task_status,
                    "phase": task_phase,
                    "description": status_or_desc[:200] if len(status_or_desc) > 10 else ""
                })

        return json.dumps({
            "tasks": tasks,
            "count": len(tasks),
            "phases": list(set(t["phase"] for t in tasks))
        }, indent=2)

    @mcp.tool()
    def governance_get_task_deps(task_id: str) -> str:
        """
        Get task dependencies (what blocks this task, what this task blocks).

        Args:
            task_id: Task ID (e.g., "P7.1", "P9.1")

        Returns:
            JSON object with blocked_by and blocks arrays
        """
        # Parse R&D backlog for dependency hints
        backlog_file = BACKLOG_DIR / "R&D-BACKLOG.md"

        result = {
            "task_id": task_id,
            "blocked_by": [],
            "blocks": []
        }

        if backlog_file.exists():
            content = backlog_file.read_text(encoding="utf-8")

            # Look for Dependencies: section
            deps_pattern = r"Dependencies:\s*\n((?:[-*]\s*.+\n)+)"
            for match in re.finditer(deps_pattern, content):
                deps_text = match.group(1)
                # Check if our task is mentioned
                if task_id in deps_text:
                    # Extract dependency relationships
                    for line in deps_text.split("\n"):
                        if task_id in line:
                            # Parse "Phase X: Y required" patterns
                            phase_match = re.search(r"Phase\s*(\d+)", line)
                            if phase_match:
                                result["blocked_by"].append(f"P{phase_match.group(1)}")

            # Infer dependencies from phase ordering
            if task_id.startswith("P"):
                phase_num = float(task_id[1:].replace("-", "."))
                # Tasks in earlier phases block later ones
                if phase_num > 7:
                    result["blocked_by"].append("P7 (TypeDB-First)")
                if phase_num > 3:
                    result["blocked_by"].append("P3 (Stabilization)")

        return json.dumps(result, indent=2)

    @mcp.tool()
    def governance_evidence_search(
        query: str,
        top_k: int = 5,
        source_type: Optional[str] = None
    ) -> str:
        """
        Semantic search across all evidence artifacts.

        Args:
            query: Search query (e.g., "authentication security rules")
            top_k: Number of results to return (default 5)
            source_type: Filter by type (session, decision, rule)

        Returns:
            JSON array of matching evidence with relevance scores
        """
        # Try to use vector store for semantic search
        try:
            from governance.vector_store import VectorStore, MockEmbeddings

            store = VectorStore()
            generator = MockEmbeddings(dimension=384)

            # Connect if possible
            if store.connect():
                query_embedding = generator.generate(query)
                results = store.search(query_embedding, top_k=top_k, source_type=source_type)
                store.close()

                return json.dumps({
                    "query": query,
                    "results": [
                        {
                            "source": r.source,
                            "source_type": r.source_type,
                            "score": round(r.score, 4),
                            "content": r.content[:200] + "..." if len(r.content) > 200 else r.content
                        }
                        for r in results
                    ],
                    "count": len(results),
                    "search_method": "semantic_vector"
                }, indent=2)
        except Exception:
            pass

        # Fall back to keyword search
        results = []
        query_lower = query.lower()

        # Search evidence files
        for pattern in [EVIDENCE_DIR / "*.md", DOCS_DIR / "rules/*.md"]:
            for filepath in glob.glob(str(pattern)):
                try:
                    path = Path(filepath)
                    content = path.read_text(encoding="utf-8")
                    if query_lower in content.lower():
                        # Count occurrences as relevance score
                        score = content.lower().count(query_lower)
                        results.append({
                            "source": path.stem,
                            "source_type": "evidence" if "evidence" in str(path) else "rule",
                            "score": score,
                            "path": str(filepath),
                            "content": content[:200] + "..."
                        })
                except Exception:
                    continue

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        return json.dumps({
            "query": query,
            "results": results[:top_k],
            "count": len(results[:top_k]),
            "search_method": "keyword_fallback"
        }, indent=2)

    # Rule quality tools
    @mcp.tool()
    def governance_analyze_rules() -> str:
        """
        Run comprehensive rule quality analysis.

        Detects:
        - Orphaned rules (no dependents)
        - Shallow rules (missing attributes)
        - Over-connected rules (too many dependencies)
        - Under-documented rules (not referenced by docs)
        - Circular dependencies

        Returns:
            JSON health report with issues, severity, impact, and remediation
        """
        if not RULE_QUALITY_AVAILABLE:
            return json.dumps({"error": "RuleQualityAnalyzer not available"})

        return analyze_rule_quality()

    @mcp.tool()
    def governance_rule_impact(rule_id: str) -> str:
        """
        Analyze impact if a rule is modified or deprecated.

        Args:
            rule_id: Rule ID (e.g., "RULE-001")

        Returns:
            JSON with affected rules, impact score, and recommendation
        """
        if not RULE_QUALITY_AVAILABLE:
            return json.dumps({"error": "RuleQualityAnalyzer not available"})

        return get_rule_impact(rule_id)

    @mcp.tool()
    def governance_find_issues(issue_type: Optional[str] = None) -> str:
        """
        Find specific types of rule quality issues.

        Args:
            issue_type: Type of issues to find:
                - "orphaned": Rules with no dependents
                - "shallow": Rules missing attributes
                - "over_connected": Rules with too many dependencies
                - "circular": Circular dependency chains
                - "under_documented": Rules not in any docs
                - None: All issues (default)

        Returns:
            JSON array of issues with severity, impact, and remediation
        """
        if not RULE_QUALITY_AVAILABLE:
            return json.dumps({"error": "RuleQualityAnalyzer not available"})

        return find_rule_issues(issue_type)
