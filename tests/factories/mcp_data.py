"""MCP Test Data Factory.

Per DRY principles: Centralized test data generation for MCP tools.
Per GAP-DATA-001: Test data for both JSON and TOON format validation.

Created: 2026-01-19
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class MCPTestDataFactory:
    """Factory for generating MCP test data structures.

    Usage:
        data = MCPTestDataFactory.rules_query_result(count=5)
        data = MCPTestDataFactory.tasks_list_result()
        data = MCPTestDataFactory.health_check_result(healthy=True)
    """

    @staticmethod
    def rule(
        rule_id: str = "RULE-001",
        name: str = "Test Rule",
        category: str = "GOVERNANCE",
        priority: str = "HIGH",
        status: str = "ACTIVE",
        directive: str = "Test directive text",
    ) -> Dict[str, Any]:
        """Generate a single rule object."""
        return {
            "rule_id": rule_id,
            "name": name,
            "category": category,
            "priority": priority,
            "status": status,
            "directive": directive,
        }

    @staticmethod
    def rules_query_result(
        count: int = 3,
        status_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate rules_query tool result."""
        rules = [
            MCPTestDataFactory.rule(
                rule_id=f"RULE-{i:03d}",
                name=f"Governance Rule {i}",
                status=status_filter or "ACTIVE",
                category=category_filter or "GOVERNANCE",
            )
            for i in range(1, count + 1)
        ]
        return {
            "rules": rules,
            "count": count,
            "filter": {"status": status_filter, "category": category_filter},
        }

    @staticmethod
    def task(
        task_id: str = "P12.1",
        name: str = "Test Task",
        description: str = "Test task description",
        status: str = "TODO",
        phase: str = "P12",
        priority: str = "MEDIUM",
    ) -> Dict[str, Any]:
        """Generate a single task object."""
        return {
            "task_id": task_id,
            "name": name,
            "description": description,
            "status": status,
            "phase": phase,
            "priority": priority,
        }

    @staticmethod
    def tasks_list_result(count: int = 3) -> Dict[str, Any]:
        """Generate tasks_list tool result."""
        tasks = [
            MCPTestDataFactory.task(
                task_id=f"P12.{i}",
                name=f"Task {i}",
            )
            for i in range(1, count + 1)
        ]
        return {"tasks": tasks, "count": count}

    @staticmethod
    def gap(
        gap_id: str = "GAP-001",
        title: str = "Test Gap",
        priority: str = "MEDIUM",
        status: str = "OPEN",
    ) -> Dict[str, Any]:
        """Generate a single gap object."""
        return {
            "gap_id": gap_id,
            "title": title,
            "priority": priority,
            "status": status,
        }

    @staticmethod
    def gaps_list_result(count: int = 3) -> Dict[str, Any]:
        """Generate gaps list result."""
        gaps = [
            MCPTestDataFactory.gap(gap_id=f"GAP-{i:03d}", title=f"Gap {i}")
            for i in range(1, count + 1)
        ]
        return {"gaps": gaps, "count": count}

    @staticmethod
    def session(
        session_id: str = "SESSION-2026-01-19-TEST",
        topic: str = "Test Session",
        status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        """Generate a single session object."""
        return {
            "session_id": session_id,
            "topic": topic,
            "status": status,
            "created_at": datetime.now().isoformat(),
        }

    @staticmethod
    def health_check_result(healthy: bool = True) -> Dict[str, Any]:
        """Generate health_check tool result."""
        if healthy:
            return {
                "status": "healthy",
                "typedb": "connected",
                "chromadb": "connected",
                "timestamp": datetime.now().isoformat(),
            }
        return {
            "status": "unhealthy",
            "error": "TypeDB connection failed",
            "action_required": "START_SERVICES",
            "recovery_hint": "podman compose --profile cpu up -d typedb",
        }

    @staticmethod
    def agent(
        agent_id: str = "AGENT-001",
        name: str = "Test Agent",
        agent_type: str = "PLATFORM",
        trust_score: float = 0.85,
    ) -> Dict[str, Any]:
        """Generate a single agent object."""
        return {
            "agent_id": agent_id,
            "name": name,
            "agent_type": agent_type,
            "trust_score": trust_score,
        }

    @staticmethod
    def chroma_query_result(count: int = 2) -> Dict[str, Any]:
        """Generate ChromaDB query result for claude-mem."""
        return {
            "ids": [[f"mem-sim-ai-20260119-{i:03d}" for i in range(count)]],
            "documents": [[f"Memory document {i}" for i in range(count)]],
            "metadatas": [[{"project": "sim-ai", "type": "session_context"} for _ in range(count)]],
            "distances": [[0.1 * i for i in range(count)]],
            "count": count,
        }

    @staticmethod
    def chroma_health_result(healthy: bool = True) -> Dict[str, Any]:
        """Generate ChromaDB health result for claude-mem."""
        if healthy:
            return {
                "status": "healthy",
                "host": "localhost",
                "port": 8001,
                "collection": "claude_memories",
                "document_count": 42,
            }
        return {
            "status": "unhealthy",
            "error": "Cannot connect to ChromaDB",
            "host": "localhost",
            "port": 8001,
            "action_required": "START_SERVICES",
            "recovery_hint": "podman compose --profile cpu up -d chromadb",
        }

    @staticmethod
    def error_result(error_message: str = "Test error") -> Dict[str, Any]:
        """Generate standard error result."""
        return {"error": error_message}

    @staticmethod
    def success_result(
        message: str = "Operation completed", **extra
    ) -> Dict[str, Any]:
        """Generate standard success result."""
        return {"success": True, "message": message, **extra}
