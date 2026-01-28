# MCP-DOC-01-v1: Tool Documentation Standard

| Field | Value |
|-------|-------|
| **Rule ID** | MCP-DOC-01-v1 |
| **Category** | OPERATIONAL |
| **Priority** | MEDIUM |
| **Status** | ACTIVE |
| **Created** | 2026-01-18 |

## Directive

MCP tool docstrings MUST include: summary, args, returns, example, and related rules.

## Required Sections

| Section | Required | Description |
|---------|----------|-------------|
| Summary | YES | One-line description |
| Args | YES | Parameter descriptions |
| Returns | YES | Return value description |
| Example | YES | Usage example |
| Related | NO | Related rules/gaps |

## Docstring Template

```python
@mcp.tool()
def task_get(task_id: str) -> str:
    """
    Get task details by ID.

    Args:
        task_id: Task identifier (e.g., "P10.1", "GAP-UI-001")

    Returns:
        JSON with task details including status, name, phase, evidence.
        Returns error JSON if task not found.

    Example:
        task_get("P10.1")
        # {"task_id": "P10.1", "name": "...", "status": "DONE"}

    Related:
        - TASK-TECH-01-v1: Task documentation standard
    """
```

## Docstring Quality Tiers

| Tier | Criteria | Compliance |
|------|----------|------------|
| L1 | Has summary | Minimum |
| L2 | Summary + Args + Returns | Acceptable |
| L3 | All sections + Example | Required |

## Verification

```bash
# Check docstring presence
grep -A3 "@mcp.tool" governance/mcp_tools/*.py | grep '"""'

# Check for Args section
grep -A10 "@mcp.tool" governance/mcp_tools/*.py | grep "Args:"
```

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Empty docstrings | Provide L2+ documentation |
| Vague summaries ("Does stuff") | Be specific ("Get task by ID") |
| Missing return description | Document success and error cases |
| No examples | Include working example |

## Rationale

- Self-documenting tools reduce onboarding time
- Examples prevent trial-and-error usage
- Consistent format enables automated doc generation

## Related

- GAP-MCP-DIRECTIVE-001 (Missing operational directives)
- DOC-SIZE-01-v1 (Documentation standards)

## Test Coverage

**1 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/pydantic_tools.robot` | unit |

```bash
# Run all tests validating this rule
robot --include MCP-DOC-01-v1 tests/robot/
```

---

*Per GAP-MCP-DIRECTIVE-001: MCP operational directives*
