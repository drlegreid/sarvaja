"""
E2E Explorer - LLM-Driven Exploratory Testing via Playwright MCP
=================================================================
Uses LLM heuristics to explore UI, then generates deterministic Robot Framework tests.

Architecture:
1. LLM explores UI via Playwright MCP (heuristic-driven)
2. Records interactions as deterministic test steps
3. Generates Robot Framework test cases
4. LLM only used for failure analysis (not runtime)

Per Phase 7: E2E Testing with Exploratory Heuristics
"""

import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum


# =============================================================================
# EXPLORATION DATA STRUCTURES
# =============================================================================

class ActionType(str, Enum):
    """Types of UI actions that can be recorded."""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    WAIT = "wait"
    ASSERT_VISIBLE = "assert_visible"
    ASSERT_TEXT = "assert_text"
    ASSERT_COUNT = "assert_count"
    SCREENSHOT = "screenshot"
    SNAPSHOT = "snapshot"


@dataclass
class ExplorationStep:
    """A single step in the exploration session."""
    action: ActionType
    target: str  # Selector or URL
    value: Optional[str] = None  # Value for type/select
    description: str = ""  # LLM-generated description
    success: bool = True
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_robot_keyword(self) -> str:
        """Convert step to Robot Framework keyword."""
        match self.action:
            case ActionType.NAVIGATE:
                return f"    Go To    {self.target}"
            case ActionType.CLICK:
                return f"    Click    {self.target}    # {self.description}"
            case ActionType.TYPE:
                return f"    Fill Text    {self.target}    {self.value}"
            case ActionType.SELECT:
                return f"    Select Options By    {self.target}    value    {self.value}"
            case ActionType.WAIT:
                return f"    Wait For Elements State    {self.target}    visible"
            case ActionType.ASSERT_VISIBLE:
                return f"    Wait For Elements State    {self.target}    visible"
            case ActionType.ASSERT_TEXT:
                return f"    Get Text    {self.target}    ==    {self.value}"
            case ActionType.ASSERT_COUNT:
                return f"    Get Element Count    {self.target}    >=    {self.value}"
            case ActionType.SCREENSHOT:
                return f"    Take Screenshot    {self.target}"
            case ActionType.SNAPSHOT:
                return f"    # Snapshot: {self.description}"
            case _:
                return f"    # Unknown action: {self.action}"


@dataclass
class ExplorationSession:
    """A complete exploration session."""
    name: str
    url: str
    steps: list[ExplorationStep] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    heuristics_used: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    def add_step(self, step: ExplorationStep):
        """Add a step to the session."""
        self.steps.append(step)

    def complete(self):
        """Mark session as complete."""
        self.completed_at = datetime.utcnow().isoformat()

    def to_robot_test(self) -> str:
        """Generate Robot Framework test case from session."""
        lines = [
            f"*** Test Cases ***",
            f"",
            f"{self.name}",
            f"    [Documentation]    Auto-generated from exploration session",
            f"    [Tags]    generated    exploratory",
        ]

        for step in self.steps:
            if step.success:
                lines.append(step.to_robot_keyword())

        return "\n".join(lines)


# =============================================================================
# EXPLORATION HEURISTICS
# =============================================================================

EXPLORATION_HEURISTICS = {
    "page_structure": """
Explore the page structure:
1. Take a snapshot of the page
2. Identify main sections (header, nav, main, footer)
3. Count interactive elements (buttons, inputs, links)
4. Record findings
""",

    "form_discovery": """
Discover and test forms:
1. Find all form elements
2. Identify required fields
3. Try submitting empty form (expect validation)
4. Fill form with valid data
5. Submit and verify response
""",

    "navigation_flow": """
Explore navigation:
1. Find all navigation links
2. Click each major section
3. Verify page loads
4. Check for 404s or errors
5. Return to starting page
""",

    "error_handling": """
Test error handling:
1. Submit invalid data
2. Trigger edge cases
3. Check for user-friendly error messages
4. Verify recovery paths
""",

    "accessibility_quick": """
Quick accessibility check:
1. Tab through interactive elements
2. Check focus visibility
3. Look for ARIA labels
4. Check color contrast
""",
}


# =============================================================================
# ROBOT FRAMEWORK GENERATOR
# =============================================================================

class RobotGenerator:
    """Generates Robot Framework test files from exploration sessions."""

    TEMPLATE = '''*** Settings ***
Documentation    {documentation}
Library          Browser    auto_closing_level=KEEP
Suite Setup      Initialize Browser
Suite Teardown   Close Browser    ALL

*** Variables ***
${{BASE_URL}}    {base_url}

*** Keywords ***
Initialize Browser
    New Browser    chromium    headless=true
    New Context    viewport={{'width': 1280, 'height': 720}}
    New Page    ${{BASE_URL}}

{test_cases}
'''

    def __init__(self, base_url: str = "http://localhost:7777"):
        self.base_url = base_url
        self.sessions: list[ExplorationSession] = []

    def add_session(self, session: ExplorationSession):
        """Add exploration session for test generation."""
        self.sessions.append(session)

    def generate(self, output_path: str) -> str:
        """Generate Robot Framework test file."""
        test_cases = []

        for session in self.sessions:
            test_cases.append(session.to_robot_test())

        content = self.TEMPLATE.format(
            documentation=f"Auto-generated from {len(self.sessions)} exploration sessions",
            base_url=self.base_url,
            test_cases="\n\n".join(test_cases),
        )

        with open(output_path, "w") as f:
            f.write(content)

        return content


# =============================================================================
# LLM EXPLORATION PROMPTS
# =============================================================================

EXPLORATION_SYSTEM_PROMPT = """You are an E2E test explorer using Playwright MCP tools.

Your goal: Explore the UI using heuristics and record deterministic test steps.

Available tools:
- mcp__playwright__browser_navigate: Navigate to URL
- mcp__playwright__browser_snapshot: Get page accessibility tree
- mcp__playwright__browser_click: Click element
- mcp__playwright__browser_type: Type text
- mcp__playwright__browser_evaluate: Run JS
- mcp__playwright__browser_take_screenshot: Capture screenshot

Exploration heuristics:
1. Start with snapshot to understand page structure
2. Identify interactive elements (buttons, inputs, forms)
3. Test happy path first
4. Then test edge cases
5. Record every successful interaction

Output format for each step:
{
    "action": "click|type|navigate|assert_visible|...",
    "target": "selector or URL",
    "value": "optional value",
    "description": "what this step does"
}
"""

FAILURE_ANALYSIS_PROMPT = """Analyze this test failure:

Test: {test_name}
Step: {failed_step}
Error: {error_message}
Screenshot: {screenshot_path}

Provide:
1. Root cause analysis
2. Suggested fix
3. Whether this is a test issue or app bug
"""


# =============================================================================
# EXPLORATION RUNNER (for use with Agno agents)
# =============================================================================

class ExplorationRunner:
    """Runs exploration sessions using LLM + Playwright MCP."""

    def __init__(self, base_url: str = "http://localhost:7777"):
        self.base_url = base_url
        self.current_session: Optional[ExplorationSession] = None
        self.generator = RobotGenerator(base_url)

    def start_session(self, name: str, url: str = None) -> ExplorationSession:
        """Start a new exploration session."""
        self.current_session = ExplorationSession(
            name=name,
            url=url or f"{self.base_url}/ui"
        )
        return self.current_session

    def record_step(
        self,
        action: ActionType,
        target: str,
        value: str = None,
        description: str = "",
        success: bool = True,
        error: str = None
    ):
        """Record an exploration step."""
        if not self.current_session:
            raise ValueError("No active session. Call start_session first.")

        step = ExplorationStep(
            action=action,
            target=target,
            value=value,
            description=description,
            success=success,
            error=error
        )
        self.current_session.add_step(step)
        return step

    def end_session(self) -> ExplorationSession:
        """End current session and return it."""
        if not self.current_session:
            raise ValueError("No active session.")

        self.current_session.complete()
        self.generator.add_session(self.current_session)

        session = self.current_session
        self.current_session = None
        return session

    def generate_tests(self, output_path: str) -> str:
        """Generate Robot Framework tests from all sessions."""
        return self.generator.generate(output_path)

    def get_exploration_prompt(self, heuristic: str) -> str:
        """Get exploration prompt for a specific heuristic."""
        if heuristic in EXPLORATION_HEURISTICS:
            return f"{EXPLORATION_SYSTEM_PROMPT}\n\nCurrent heuristic:\n{EXPLORATION_HEURISTICS[heuristic]}"
        return EXPLORATION_SYSTEM_PROMPT


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def example_exploration():
    """Example of how to use the exploration framework."""
    runner = ExplorationRunner("http://localhost:7777")

    # Start session
    session = runner.start_session("Task Console Smoke Test", "/ui")

    # Record steps (these would come from LLM + Playwright MCP)
    runner.record_step(
        ActionType.NAVIGATE,
        "http://localhost:7777/ui",
        description="Open Task Console"
    )

    runner.record_step(
        ActionType.SNAPSHOT,
        "",
        description="Capture initial page state"
    )

    runner.record_step(
        ActionType.ASSERT_VISIBLE,
        "form, .task-form",
        description="Verify task form is visible"
    )

    runner.record_step(
        ActionType.TYPE,
        "textarea#prompt",
        value="Test task from exploration",
        description="Fill in task prompt"
    )

    runner.record_step(
        ActionType.CLICK,
        "button:has-text('Submit')",
        description="Submit the task"
    )

    runner.record_step(
        ActionType.ASSERT_VISIBLE,
        ".task-item",
        description="Verify task appears in list"
    )

    # End session
    runner.end_session()

    # Generate Robot Framework test
    robot_test = runner.generate_tests("tests/e2e/generated/smoke_test.robot")
    print(robot_test)

    return runner


if __name__ == "__main__":
    example_exploration()
