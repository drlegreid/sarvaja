"""
Delegation Convenience Methods (Mixin) + Factory Functions.

Per DOC-SIZE-01-v1: Extracted from delegation.py (578 lines).
Shortcut methods for common delegation patterns.
"""

import uuid
from typing import Any, Dict, List

from .engine import AgentRole
from .delegation_models import (
    DelegationContext,
    DelegationPriority,
    DelegationRequest,
    DelegationResult,
    DelegationType,
)


class DelegationShortcutsMixin:
    """Mixin providing convenience delegation methods.

    Expects host class to provide:
        self.delegate(request: DelegationRequest) -> DelegationResult
    """

    async def delegate_research(
        self,
        task_id: str,
        source_agent_id: str,
        query: str,
        gathered_context: Dict[str, Any] = None,
    ) -> DelegationResult:
        """Convenience: Delegate research to Research Agent."""
        context = DelegationContext(
            delegation_id=f"DEL-RES-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            source_agent_id=source_agent_id,
            task_description=query,
            gathered_context=gathered_context or {},
        )
        request = DelegationRequest(
            task_id=task_id,
            delegation_type=DelegationType.RESEARCH,
            target_role=AgentRole.RESEARCH,
            context=context,
        )
        return await self.delegate(request)

    async def delegate_implementation(
        self,
        task_id: str,
        source_agent_id: str,
        spec: str,
        context: Dict[str, Any] = None,
        constraints: List[str] = None,
    ) -> DelegationResult:
        """Convenience: Delegate implementation to Coding Agent."""
        delegation_context = DelegationContext(
            delegation_id=f"DEL-IMP-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            source_agent_id=source_agent_id,
            task_description=spec,
            gathered_context=context or {},
            constraints=constraints or [],
        )
        request = DelegationRequest(
            task_id=task_id,
            delegation_type=DelegationType.IMPLEMENTATION,
            target_role=AgentRole.CODING,
            context=delegation_context,
        )
        return await self.delegate(request)

    async def delegate_validation(
        self,
        task_id: str,
        source_agent_id: str,
        item_to_validate: Dict[str, Any],
        rules: List[str] = None,
    ) -> DelegationResult:
        """Convenience: Delegate validation to Rules Curator."""
        context = DelegationContext(
            delegation_id=f"DEL-VAL-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            source_agent_id=source_agent_id,
            task_description="Validate against governance rules",
            gathered_context={"item": item_to_validate},
            constraints=rules or [],
        )
        request = DelegationRequest(
            task_id=task_id,
            delegation_type=DelegationType.VALIDATION,
            target_role=AgentRole.CURATOR,
            context=context,
        )
        return await self.delegate(request)

    async def escalate(
        self,
        task_id: str,
        source_agent_id: str,
        reason: str,
        context: Dict[str, Any] = None,
    ) -> DelegationResult:
        """Escalate a task to the orchestrator for re-routing."""
        delegation_context = DelegationContext(
            delegation_id=f"DEL-ESC-{uuid.uuid4().hex[:8].upper()}",
            task_id=task_id,
            source_agent_id=source_agent_id,
            task_description=f"ESCALATION: {reason}",
            gathered_context=context or {},
            priority=DelegationPriority.HIGH,
        )
        request = DelegationRequest(
            task_id=task_id,
            delegation_type=DelegationType.ESCALATION,
            target_role=AgentRole.ORCHESTRATOR,
            context=delegation_context,
        )
        return await self.delegate(request)


# =============================================================================
# Standalone Factory Functions
# =============================================================================

def create_delegation_context(
    task_id: str,
    source_agent_id: str,
    description: str,
    **kwargs,
) -> DelegationContext:
    """Create a delegation context with auto-generated ID."""
    return DelegationContext(
        delegation_id=f"DEL-{uuid.uuid4().hex[:8].upper()}",
        task_id=task_id,
        source_agent_id=source_agent_id,
        task_description=description,
        **kwargs,
    )


def create_research_request(
    task_id: str,
    source_agent_id: str,
    query: str,
) -> DelegationRequest:
    """Create a research delegation request."""
    context = create_delegation_context(
        task_id=task_id,
        source_agent_id=source_agent_id,
        description=query,
    )
    return DelegationRequest(
        task_id=task_id,
        delegation_type=DelegationType.RESEARCH,
        target_role=AgentRole.RESEARCH,
        context=context,
    )


def create_implementation_request(
    task_id: str,
    source_agent_id: str,
    spec: str,
    context: Dict[str, Any] = None,
) -> DelegationRequest:
    """Create an implementation delegation request."""
    delegation_context = create_delegation_context(
        task_id=task_id,
        source_agent_id=source_agent_id,
        description=spec,
        gathered_context=context or {},
    )
    return DelegationRequest(
        task_id=task_id,
        delegation_type=DelegationType.IMPLEMENTATION,
        target_role=AgentRole.CODING,
        context=delegation_context,
    )
