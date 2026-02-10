"""
RF Library for Orchestrator Continuous Workflow E2E Tests.

Per TEST-TDD-01-v1: RED phase — library written before implementation.
Per TEST-BDD-01-v1: Keywords map to BDD Given/When/Then steps.
Per WORKFLOW-ORCH-01-v1: Orchestrator Spec→Impl→Validate loop.
"""

from typing import Dict, Any, List, Optional
from robot.api.deco import keyword


class OrchestratorE2ELibrary:
    """Robot Framework library for orchestrator workflow E2E tests."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    @keyword("Create Orchestrator State")
    def create_orchestrator_state(
        self, max_cycles: int = 10, dry_run: bool = True
    ) -> Dict[str, Any]:
        """Create initial orchestrator state with empty backlog."""
        from governance.workflows.orchestrator.state import create_initial_state
        return create_initial_state(max_cycles=max_cycles, dry_run=dry_run)

    @keyword("Create Orchestrator State With Backlog")
    def create_orchestrator_state_with_backlog(
        self, *task_specs: str
    ) -> Dict[str, Any]:
        """Create state with pre-populated backlog.

        Args:
            task_specs: Strings like "GAP-001:HIGH", "TASK-002:CRITICAL"
        """
        from governance.workflows.orchestrator.state import (
            create_initial_state,
            add_to_backlog,
        )
        state = create_initial_state(dry_run=True)
        for spec in task_specs:
            parts = spec.split(":")
            task_id = parts[0]
            priority = parts[1] if len(parts) > 1 else "MEDIUM"
            state = add_to_backlog(
                state, task_id=task_id, priority=priority,
                description=f"Test task {task_id}",
            )
        return state

    @keyword("Create State With Selected Task")
    def create_state_with_selected_task(
        self, task_id: str, description: str
    ) -> Dict[str, Any]:
        """Create state as if backlog_node already selected a task."""
        from governance.workflows.orchestrator.state import (
            create_initial_state,
            add_to_backlog,
        )
        from governance.workflows.orchestrator.nodes import backlog_node
        state = create_initial_state(dry_run=True)
        state = add_to_backlog(
            state, task_id=task_id, priority="HIGH",
            description=description,
        )
        return backlog_node(state)

    @keyword("Create State With Specification")
    def create_state_with_specification(self) -> Dict[str, Any]:
        """Create state as if spec_node already produced a specification."""
        from governance.workflows.orchestrator.nodes import (
            backlog_node,
            spec_node,
        )
        state = self.create_orchestrator_state_with_backlog("GAP-TEST-001:HIGH")
        state = backlog_node(state)
        return spec_node(state)

    @keyword("Create State With Implementation")
    def create_state_with_implementation(
        self, discover_gaps: bool = False
    ) -> Dict[str, Any]:
        """Create state as if implement_node already ran."""
        from governance.workflows.orchestrator.nodes import (
            backlog_node,
            spec_node,
            implement_node,
        )
        state = self.create_orchestrator_state_with_backlog("GAP-TEST-001:HIGH")
        state = backlog_node(state)
        state = spec_node(state)
        state = implement_node(state)
        if discover_gaps:
            state["_simulate_gap_discovery"] = True
        return state

    @keyword("Create State After Validation With Gaps")
    def create_state_after_validation_with_gaps(self) -> Dict[str, Any]:
        """Create state after validation discovered gaps."""
        from governance.workflows.orchestrator.nodes import (
            backlog_node,
            spec_node,
            implement_node,
            validate_node,
        )
        state = self.create_orchestrator_state_with_backlog("GAP-TEST-001:HIGH")
        state = backlog_node(state)
        state = spec_node(state)
        state = implement_node(state)
        state["_simulate_gap_discovery"] = True
        return validate_node(state)

    # === Node Execution Keywords ===

    @keyword("Run Backlog Node")
    def run_backlog_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the backlog node on given state."""
        from governance.workflows.orchestrator.nodes import backlog_node
        result = backlog_node(state)
        state.update(result)
        return state

    @keyword("Run Gate Node")
    def run_gate_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the gate node on given state."""
        from governance.workflows.orchestrator.nodes import gate_node
        result = gate_node(state)
        state.update(result)
        return state

    @keyword("Run Spec Node")
    def run_spec_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the spec node on given state."""
        from governance.workflows.orchestrator.nodes import spec_node
        result = spec_node(state)
        state.update(result)
        return state

    @keyword("Run Implement Node")
    def run_implement_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the implement node on given state."""
        from governance.workflows.orchestrator.nodes import implement_node
        result = implement_node(state)
        state.update(result)
        return state

    @keyword("Run Validate Node")
    def run_validate_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the validate node on given state."""
        from governance.workflows.orchestrator.nodes import validate_node
        result = validate_node(state)
        state.update(result)
        return state

    @keyword("Run Inject Node")
    def run_inject_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the inject node on given state."""
        from governance.workflows.orchestrator.nodes import inject_node
        result = inject_node(state)
        state.update(result)
        return state

    # === Workflow Execution Keywords ===

    @keyword("Run Single Cycle")
    def run_single_cycle(
        self, task_id: str, description: str
    ) -> Dict[str, Any]:
        """Run a single spec→impl→validate cycle for one task."""
        from governance.workflows.orchestrator.graph import run_single_cycle
        return run_single_cycle(
            task_id=task_id, description=description, dry_run=True,
        )

    @keyword("Run Single Cycle With Failure")
    def run_single_cycle_with_failure(
        self, task_id: str, fail_validation: bool = False
    ) -> Dict[str, Any]:
        """Run a single cycle that simulates a failure."""
        from governance.workflows.orchestrator.graph import run_single_cycle
        return run_single_cycle(
            task_id=task_id,
            description=f"Test task {task_id}",
            dry_run=True,
            _simulate_validation_failure=fail_validation,
        )

    @keyword("Run Orchestrator Loop")
    def run_orchestrator_loop(
        self, *task_specs: str, max_cycles: int = 10
    ) -> Dict[str, Any]:
        """Run the full orchestrator loop with given backlog."""
        from governance.workflows.orchestrator.graph import run_orchestrator
        from governance.workflows.orchestrator.state import (
            create_initial_state,
            add_to_backlog,
        )
        state = create_initial_state(max_cycles=int(max_cycles), dry_run=True)
        for spec in task_specs:
            parts = spec.split(":")
            task_id = parts[0]
            priority = parts[1] if len(parts) > 1 else "MEDIUM"
            state = add_to_backlog(
                state, task_id=task_id, priority=priority,
                description=f"Test task {task_id}",
            )
        return run_orchestrator(state)

    @keyword("Cleanup Orchestrator Test Data")
    def cleanup_orchestrator_test_data(self) -> Dict[str, Any]:
        """Clean up any test artifacts."""
        return {"cleaned": True}
