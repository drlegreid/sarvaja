"""
Exploratory UI Testing Building Blocks.

Per user feedback: Create building blocks for LLM-driven exploratory testing
using Playwright MCP. These are NOT static assertions - they are discovery tools.

Usage (by LLM via Playwright MCP):
    1. Navigate to dashboard
    2. Use check_interactive_elements() to discover what's clickable
    3. Use check_data_displayed() to verify data is showing
    4. Use discover_navigation_flow() to map the UI
    5. Report any issues found as new GAPs

The LLM (Claude) drives these blocks through Playwright MCP tools:
- mcp__playwright__browser_navigate
- mcp__playwright__browser_snapshot
- mcp__playwright__browser_click
- etc.

Created: 2026-01-14
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class IssueType(Enum):
    """Types of issues that can be discovered."""
    MISSING_DATA = "missing_data"           # Expected data not shown
    BROKEN_INTERACTION = "broken_interaction"  # Click/action doesn't work
    NAVIGATION_DEAD_END = "navigation_dead_end"  # Can't navigate further
    MISSING_FEEDBACK = "missing_feedback"    # No loading/error states
    ACCESSIBILITY_ISSUE = "accessibility"     # Missing ARIA, testids
    DATA_INCONSISTENCY = "data_inconsistency"  # UI shows wrong data
    PERFORMANCE_ISSUE = "performance"         # Slow loading
    EMPTY_STATE = "empty_state"               # Table/list is empty


@dataclass
class ExploratoryFinding:
    """A finding from exploratory testing."""
    issue_type: IssueType
    description: str
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    page_url: str = ""
    element_ref: str = ""
    expected: str = ""
    actual: str = ""
    screenshot_path: Optional[str] = None
    suggested_gap_id: Optional[str] = None

    def to_gap_entry(self) -> str:
        """Format as GAP-INDEX entry."""
        return f"| {self.suggested_gap_id or 'GAP-UI-NEW'} | OPEN | {self.description} | {self.severity} | ui | Found by exploratory testing |"


@dataclass
class ExploratorySession:
    """Tracks findings from an exploratory session."""
    session_id: str
    findings: List[ExploratoryFinding] = field(default_factory=list)
    pages_visited: List[str] = field(default_factory=list)
    elements_tested: List[str] = field(default_factory=list)

    def add_finding(self, finding: ExploratoryFinding):
        """Add a finding to the session."""
        self.findings.append(finding)

    def summary(self) -> str:
        """Generate session summary."""
        lines = [
            f"Exploratory Session: {self.session_id}",
            f"Pages visited: {len(self.pages_visited)}",
            f"Elements tested: {len(self.elements_tested)}",
            f"Issues found: {len(self.findings)}",
            "",
            "Findings by severity:",
        ]
        by_severity = {}
        for f in self.findings:
            by_severity.setdefault(f.severity, []).append(f)
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if sev in by_severity:
                lines.append(f"  {sev}: {len(by_severity[sev])}")
        return "\n".join(lines)


# =============================================================================
# BUILDING BLOCKS FOR PLAYWRIGHT MCP EXPLORATORY TESTING
# =============================================================================

class ExploratoryChecks:
    """
    Building blocks for LLM-driven exploratory testing.

    These are NOT automated tests - they are instructions for the LLM
    to execute via Playwright MCP and report findings.

    Usage example (Claude executing):
        1. Call mcp__playwright__browser_navigate(url="http://localhost:8081")
        2. Call mcp__playwright__browser_snapshot()
        3. Use these building blocks to analyze what was found
        4. Report issues as ExploratoryFinding objects
    """

    @staticmethod
    def check_rules_view_instructions() -> str:
        """Instructions for LLM to check Rules view."""
        return """
        EXPLORATORY CHECK: Rules View

        Navigate to Rules view and verify:
        1. Table is populated (not empty)
        2. Rule ID column shows actual IDs (not "undefined")
        3. Clicking a row opens detail view
        4. Create/Edit/Delete buttons are present
        5. Actions trigger appropriate responses

        Report findings:
        - MISSING_DATA if table is empty
        - BROKEN_INTERACTION if clicks don't work
        - DATA_INCONSISTENCY if IDs are wrong

        MCP sequence:
        1. browser_navigate(url="http://localhost:8081")
        2. browser_snapshot() - check for Rules navigation
        3. browser_click(element="Rules nav item")
        4. browser_snapshot() - analyze table state
        """

    @staticmethod
    def check_tasks_view_instructions() -> str:
        """Instructions for LLM to check Tasks view."""
        return """
        EXPLORATORY CHECK: Tasks View

        Navigate to Tasks view and verify:
        1. Task list shows real tasks (not TEST-* pollution)
        2. Status column reflects actual status
        3. Phase filtering works
        4. Task details can be viewed

        Report findings:
        - MISSING_DATA if no tasks shown
        - DATA_INCONSISTENCY if TEST-* tasks visible
        - BROKEN_INTERACTION if filtering fails
        """

    @staticmethod
    def check_agents_view_instructions() -> str:
        """Instructions for LLM to check Agents view."""
        return """
        EXPLORATORY CHECK: Agents View

        Navigate to Agents view and verify:
        1. Agent list shows configured agents
        2. Trust scores are displayed (0.0-1.0 range)
        3. Agent type is shown
        4. Session/Task links work

        Report findings:
        - MISSING_DATA if no agents
        - DATA_INCONSISTENCY if trust scores out of range
        """

    @staticmethod
    def check_sessions_view_instructions() -> str:
        """Instructions for LLM to check Sessions view."""
        return """
        EXPLORATORY CHECK: Sessions View

        Navigate to Sessions view and verify:
        1. Session list shows real sessions
        2. Timestamps are valid ISO format
        3. Session details can be viewed
        4. Evidence links work

        Report findings:
        - MISSING_DATA if empty
        - DATA_INCONSISTENCY if timestamps invalid
        """

    @staticmethod
    def check_crud_flow_instructions(entity: str) -> str:
        """Instructions for LLM to test CRUD flow for an entity."""
        return f"""
        EXPLORATORY CHECK: {entity} CRUD Flow

        Test the complete Create-Read-Update-Delete cycle:

        1. CREATE:
           - Click "New {entity}" or "+" button
           - Fill required fields
           - Submit form
           - Verify {entity} appears in list

        2. READ:
           - Click on {entity} in list
           - Verify details are displayed
           - Check all fields populated

        3. UPDATE:
           - Click Edit button
           - Modify a field
           - Save changes
           - Verify changes persisted

        4. DELETE:
           - Click Delete button
           - Confirm deletion
           - Verify {entity} removed from list

        Report findings at each step:
        - BROKEN_INTERACTION if buttons don't work
        - MISSING_FEEDBACK if no confirmation shown
        - DATA_INCONSISTENCY if changes don't persist
        """

    @staticmethod
    def check_navigation_instructions() -> str:
        """Instructions for navigation discovery."""
        return """
        EXPLORATORY CHECK: Navigation Flow

        Map the complete navigation structure:

        1. Starting from dashboard:
           - List all visible navigation items
           - Click each one
           - Record if it leads somewhere or dead-ends

        2. For each view:
           - Can you go back?
           - Are breadcrumbs shown?
           - Can you reach all other views?

        3. Deep navigation:
           - Click into details
           - Click related links
           - Can you navigate between related entities?

        Report findings:
        - NAVIGATION_DEAD_END if can't proceed
        - MISSING_FEEDBACK if no loading indicator
        - ACCESSIBILITY_ISSUE if missing ARIA labels
        """

    @staticmethod
    def check_error_states_instructions() -> str:
        """Instructions for error state discovery."""
        return """
        EXPLORATORY CHECK: Error States

        Deliberately trigger errors and observe behavior:

        1. Invalid input:
           - Try empty required fields
           - Try invalid formats
           - Is feedback shown?

        2. Network errors:
           - What happens if API is down?
           - Is there a retry option?

        3. Not found:
           - Navigate to non-existent entity
           - Is 404 handled gracefully?

        Report findings:
        - MISSING_FEEDBACK if no error shown
        - BROKEN_INTERACTION if form submits anyway
        """


# =============================================================================
# EXPLORATORY TEST RUNNER (for LLM execution)
# =============================================================================

def create_exploratory_session(session_id: str) -> ExploratorySession:
    """Create a new exploratory session for tracking findings."""
    return ExploratorySession(session_id=session_id)


def get_all_check_instructions() -> Dict[str, str]:
    """Get all available check instructions."""
    return {
        "rules": ExploratoryChecks.check_rules_view_instructions(),
        "tasks": ExploratoryChecks.check_tasks_view_instructions(),
        "agents": ExploratoryChecks.check_agents_view_instructions(),
        "sessions": ExploratoryChecks.check_sessions_view_instructions(),
        "crud_rule": ExploratoryChecks.check_crud_flow_instructions("Rule"),
        "crud_task": ExploratoryChecks.check_crud_flow_instructions("Task"),
        "navigation": ExploratoryChecks.check_navigation_instructions(),
        "errors": ExploratoryChecks.check_error_states_instructions(),
    }


# Example of how findings should be reported
EXAMPLE_FINDINGS = [
    ExploratoryFinding(
        issue_type=IssueType.EMPTY_STATE,
        description="Tasks view shows empty table",
        severity="HIGH",
        page_url="http://localhost:8081/tasks",
        expected="List of tasks from TypeDB",
        actual="Empty table with no rows",
        suggested_gap_id="GAP-UI-EXP-001"
    ),
    ExploratoryFinding(
        issue_type=IssueType.BROKEN_INTERACTION,
        description="Create Rule button does nothing",
        severity="CRITICAL",
        page_url="http://localhost:8081/rules",
        element_ref="button[data-testid='create-rule']",
        expected="Opens rule creation form",
        actual="No response on click",
        suggested_gap_id="GAP-UI-EXP-002"
    ),
]


if __name__ == "__main__":
    # Print all instructions for reference
    print("=" * 60)
    print("EXPLORATORY TESTING BUILDING BLOCKS")
    print("=" * 60)
    print()
    print("Available check instructions:")
    for name, instructions in get_all_check_instructions().items():
        print(f"\n--- {name.upper()} ---")
        print(instructions[:200] + "..." if len(instructions) > 200 else instructions)
