"""
Test Data Factories
===================
Per TEST-001: Test framework reusability.
Per RD-TESTING-STRATEGY: Tests REUSE implementation objects.

Factories use implementation models as source of truth.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import uuid

# Import from implementation - NOT duplicate
from governance.models import (
    RuleCreate,
    RuleResponse,
    TaskCreate,
    TaskResponse,
    SessionCreate,
    SessionResponse,
    DecisionCreate,
    DecisionResponse,
    AgentResponse,
)


class RuleFactory:
    """
    Factory for creating rule test data.

    Uses governance.models.RuleCreate/RuleResponse as source of truth.
    """

    _counter = 0

    @classmethod
    def create_request(cls, **overrides) -> RuleCreate:
        """Create a RuleCreate request model."""
        cls._counter += 1
        defaults = {
            "rule_id": f"RULE-TEST-{cls._counter:03d}",
            "name": f"Test Rule {cls._counter}",
            "category": "testing",
            "priority": "MEDIUM",
            "directive": f"Test directive {cls._counter}",
            "status": "DRAFT",
        }
        data = {**defaults, **overrides}
        return RuleCreate(**data)

    @classmethod
    def create_response(cls, **overrides) -> RuleResponse:
        """Create a RuleResponse model (mock API response)."""
        cls._counter += 1
        defaults = {
            "id": f"RULE-TEST-{cls._counter:03d}",
            "semantic_id": None,
            "name": f"Test Rule {cls._counter}",
            "category": "testing",
            "priority": "MEDIUM",
            "status": "ACTIVE",
            "directive": f"Test directive {cls._counter}",
            "created_date": datetime.now().isoformat(),
        }
        data = {**defaults, **overrides}
        return RuleResponse(**data)

    @classmethod
    def create_dict(cls, **overrides) -> Dict[str, Any]:
        """Create a rule dict (for API payloads)."""
        return cls.create_request(**overrides).model_dump()


class TaskFactory:
    """
    Factory for creating task test data.

    Uses governance.models.TaskCreate/TaskResponse as source of truth.
    """

    _counter = 0

    @classmethod
    def create_request(cls, **overrides) -> TaskCreate:
        """Create a TaskCreate request model."""
        cls._counter += 1
        defaults = {
            "task_id": f"TASK-TEST-{cls._counter:03d}",
            "description": f"Test Task {cls._counter}",
            "phase": "TEST",
            "status": "TODO",
        }
        data = {**defaults, **overrides}
        return TaskCreate(**data)

    @classmethod
    def create_response(cls, **overrides) -> TaskResponse:
        """Create a TaskResponse model (mock API response)."""
        cls._counter += 1
        defaults = {
            "task_id": f"TASK-TEST-{cls._counter:03d}",
            "description": f"Test Task {cls._counter}",
            "phase": "TEST",
            "status": "TODO",
            "created_at": datetime.now().isoformat(),
        }
        data = {**defaults, **overrides}
        return TaskResponse(**data)

    @classmethod
    def create_dict(cls, **overrides) -> Dict[str, Any]:
        """Create a task dict (for API payloads)."""
        return cls.create_request(**overrides).model_dump()


class SessionFactory:
    """
    Factory for creating session test data.

    Uses governance.models.SessionCreate/SessionResponse as source of truth.
    """

    _counter = 0

    @classmethod
    def create_request(cls, **overrides) -> SessionCreate:
        """Create a SessionCreate request model."""
        cls._counter += 1
        date_str = datetime.now().strftime("%Y-%m-%d")
        defaults = {
            "session_id": f"SESSION-{date_str}-TEST-{cls._counter:03d}",
            "description": f"Test Session {cls._counter}",
        }
        data = {**defaults, **overrides}
        return SessionCreate(**data)

    @classmethod
    def create_response(cls, **overrides) -> SessionResponse:
        """Create a SessionResponse model (mock API response)."""
        cls._counter += 1
        date_str = datetime.now().strftime("%Y-%m-%d")
        defaults = {
            "session_id": f"SESSION-{date_str}-TEST-{cls._counter:03d}",
            "start_time": datetime.now().isoformat(),
            "status": "active",
        }
        data = {**defaults, **overrides}
        return SessionResponse(**data)


class DecisionFactory:
    """
    Factory for creating decision test data.

    Uses governance.models.DecisionCreate/DecisionResponse as source of truth.
    """

    _counter = 0

    @classmethod
    def create_request(cls, **overrides) -> DecisionCreate:
        """Create a DecisionCreate request model."""
        cls._counter += 1
        defaults = {
            "decision_id": f"DECISION-TEST-{cls._counter:03d}",
            "name": f"Test Decision {cls._counter}",
            "context": f"Test context {cls._counter}",
            "rationale": f"Test rationale {cls._counter}",
            "status": "PENDING",
        }
        data = {**defaults, **overrides}
        return DecisionCreate(**data)

    @classmethod
    def create_response(cls, **overrides) -> DecisionResponse:
        """Create a DecisionResponse model (mock API response)."""
        cls._counter += 1
        defaults = {
            "id": f"DECISION-TEST-{cls._counter:03d}",
            "name": f"Test Decision {cls._counter}",
            "context": f"Test context {cls._counter}",
            "rationale": f"Test rationale {cls._counter}",
            "status": "APPROVED",
            "decision_date": datetime.now().isoformat(),
            "linked_rules": [],
        }
        data = {**defaults, **overrides}
        return DecisionResponse(**data)


class AgentFactory:
    """
    Factory for creating agent test data.

    Uses governance.models.AgentResponse as source of truth.
    """

    _counter = 0

    @classmethod
    def create_response(cls, **overrides) -> AgentResponse:
        """Create an AgentResponse model (mock API response)."""
        cls._counter += 1
        defaults = {
            "agent_id": f"agent-test-{cls._counter:03d}",
            "name": f"Test Agent {cls._counter}",
            "agent_type": "test-agent",
            "status": "active",
            "tasks_executed": 0,
            "trust_score": 0.8,
            "capabilities": ["test"],
        }
        data = {**defaults, **overrides}
        return AgentResponse(**data)


# Convenience function for generating unique IDs
def generate_id(prefix: str = "TEST") -> str:
    """Generate a unique test ID."""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
