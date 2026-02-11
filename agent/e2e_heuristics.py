"""
E2E Exploration Heuristics & LLM Prompts.

Per DOC-SIZE-01-v1: Extracted from e2e_explorer.py (387 lines).
Heuristic definitions and LLM prompt templates for exploratory testing.
"""


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
