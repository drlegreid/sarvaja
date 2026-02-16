"""3-Tier Validation Spec Generator.

Per TEST-SPEC-01-v1: Produces Gherkin-style specs at 3 detail levels:
  Tier 1 - Business Intent (what/why - Feature + user story)
  Tier 2 - Technical Intent (what/how - Scenario with Given/When/Then)
  Tier 3 - Low-Level Details (API requests/responses, UI interactions)

Specs are:
  - Generated from orchestrator validation results
  - Compatible with Robot Framework BDD keywords
  - Tagged with MCP tool references (rest-api or playwright) for dynamic execution
"""

from typing import Any, Dict, List, Optional


def generate_spec(
    task_id: str,
    description: str,
    endpoint: str,
    method: str = "GET",
    request_body: Optional[Dict] = None,
    expected_status: int = 200,
    spec_type: str = "api",
) -> Dict[str, Any]:
    """Generate a 3-tier Gherkin-style spec for a single endpoint/action.

    Args:
        task_id: The originating task/gap ID.
        description: Human-readable description of what to validate.
        endpoint: API path or URL for the test target.
        method: HTTP method (GET/POST/PUT/DELETE) or NAVIGATE for UI.
        request_body: Optional request body for POST/PUT.
        expected_status: Expected HTTP status code.
        spec_type: "api" or "ui" — determines MCP tool.

    Returns:
        Dict with tier_1, tier_2, tier_3 text + metadata.
    """
    mcp_tool = "playwright" if spec_type == "ui" else "rest-api"
    is_post = method.upper() in ("POST", "PUT", "PATCH")
    is_ui = spec_type == "ui"

    # --- Tier 1: Business Intent ---
    tier_1 = _build_tier_1(task_id, description, endpoint, is_ui)

    # --- Tier 2: Technical Intent ---
    tier_2 = _build_tier_2(task_id, description, endpoint, method, is_ui)

    # --- Tier 3: Low-Level Details ---
    tier_3 = _build_tier_3(
        task_id, endpoint, method, request_body,
        expected_status, is_post, is_ui,
    )

    return {
        "task_id": task_id,
        "endpoint": endpoint,
        "method": method,
        "mcp_tool": mcp_tool,
        "spec_type": spec_type,
        "tier_1": tier_1,
        "tier_2": tier_2,
        "tier_3": tier_3,
    }


def _build_tier_1(
    task_id: str, description: str, endpoint: str, is_ui: bool,
) -> str:
    """Build Tier 1: Business Intent (Feature + user story)."""
    domain = "dashboard" if is_ui else "governance API"
    action = "interact with" if is_ui else "call"
    return (
        f"Feature: {description} [{task_id}]\n"
        f"  As a governance administrator\n"
        f"  I want to {action} {endpoint}\n"
        f"  So that {description.lower()} is verified"
    )


def _build_tier_2(
    task_id: str, description: str, endpoint: str,
    method: str, is_ui: bool,
) -> str:
    """Build Tier 2: Technical Intent (Scenario + Given/When/Then)."""
    if is_ui:
        return (
            f"  Scenario: {task_id} - {description}\n"
            f"    Given the dashboard is accessible at {endpoint}\n"
            f"    When I navigate to the page\n"
            f"    Then the page should load without errors\n"
            f"    And the expected elements should be visible"
        )
    return (
        f"  Scenario: {task_id} - {description}\n"
        f"    Given the governance API is running\n"
        f"    When I send {method} to {endpoint}\n"
        f"    Then the response status should indicate success\n"
        f"    And the response body should contain expected data"
    )


def _build_tier_3(
    task_id: str, endpoint: str, method: str,
    request_body: Optional[Dict], expected_status: int,
    is_post: bool, is_ui: bool,
) -> str:
    """Build Tier 3: Low-Level Details (exact HTTP/UI interactions)."""
    if is_ui:
        return (
            f"  # Low-level UI interaction for {task_id}\n"
            f"  # MCP: playwright\n"
            f"  Step 1: Navigate to {endpoint}\n"
            f"  Step 2: Take screenshot for baseline\n"
            f"  Step 3: Click on target elements\n"
            f"  Step 4: Verify page state"
        )

    lines = [
        f"  # Low-level API contract for {task_id}",
        f"  # MCP: rest-api",
        f"  Request: {method} {endpoint}",
    ]
    if is_post:
        lines.append("  Header: Content-Type: application/json")
        if request_body:
            import json
            lines.append(f"  Body: {json.dumps(request_body)}")
    lines.append(f"  Expected: status {expected_status}")
    lines.append(f"  Validate: response body is JSON")
    return "\n".join(lines)


def export_to_robot(spec: Dict[str, Any]) -> str:
    """Export a 3-tier spec as a Robot Framework test file.

    Produces BDD-style RF test with Given/When/Then keywords
    and Documentation from tier_1 business intent.
    """
    task_id = spec["task_id"]
    endpoint = spec.get("endpoint", "")
    method = spec.get("method", "GET")
    is_ui = spec.get("spec_type") == "ui"

    test_name = f"{task_id} Validation"
    library = "Browser" if is_ui else "RequestsLibrary"

    # BUG-SPEC-001: Guard against empty/None tier strings before splitlines()
    tier_1_text = spec.get('tier_1') or ""
    tier_1_lines = tier_1_text.splitlines()
    tier_1_doc = tier_1_lines[0] if tier_1_lines else task_id
    tier_2_text = spec.get('tier_2') or ""
    tier_2_lines = tier_2_text.splitlines()
    tier_2_doc = tier_2_lines[0] if tier_2_lines else task_id

    lines = [
        "*** Settings ***",
        f"Documentation    {tier_1_doc}",
        f"Library          {library}",
        f"Test Tags        {task_id}    spec-tier    TEST-SPEC-01-v1",
        "",
        "*** Test Cases ***",
        "",
        test_name,
        f"    [Documentation]    {tier_2_doc}",
        f"    [Tags]    {task_id}    e2e",
    ]

    if is_ui:
        lines.extend([
            f"    Given Navigate To    {endpoint}",
            f"    When Take Screenshot",
            f"    Then Page Should Contain Expected Elements",
        ])
    else:
        lines.extend([
            f"    Given API Is Running",
            f"    When Send {method} Request    {endpoint}",
            f"    Then Response Status Should Be Success",
        ])

    return "\n".join(lines)


def generate_specs_from_validation(
    validation_result: Dict[str, Any],
    task: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate specs from an orchestrator validation result + task.

    If task has 'endpoints' list, generates one spec per endpoint.
    If task has 'ui_path', generates a UI spec.
    Otherwise generates a default API spec.
    """
    task_id = task["task_id"]
    description = task.get("description", f"Validate {task_id}")
    specs = []

    endpoints = task.get("endpoints", [])
    if endpoints:
        for ep in endpoints:
            spec = generate_spec(
                task_id=task_id,
                description=description,
                endpoint=ep.get("path", "/api/health"),
                method=ep.get("method", "GET"),
                request_body=ep.get("body"),
            )
            specs.append(spec)
    elif task.get("ui_path"):
        spec = generate_spec(
            task_id=task_id,
            description=description,
            endpoint=task["ui_path"],
            method="NAVIGATE",
            spec_type="ui",
        )
        specs.append(spec)
    else:
        # Default: generate a health-check style spec
        spec = generate_spec(
            task_id=task_id,
            description=description,
            endpoint="/api/health",
        )
        specs.append(spec)

    return specs


def generate_batch_specs(
    backlog: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate specs for all tasks in a backlog.

    Returns a flat list of spec dicts, one per task.
    Each spec inherits the task's priority.
    """
    results = []
    for task in backlog:
        spec = generate_spec(
            task_id=task["task_id"],
            description=task.get("description", f"Validate {task['task_id']}"),
            endpoint=task.get("endpoint", "/api/health"),
            method=task.get("method", "GET"),
        )
        spec["priority"] = task.get("priority", "MEDIUM")
        results.append(spec)
    return results
