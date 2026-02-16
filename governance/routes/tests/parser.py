"""
Test Output Parser and Evidence Generator.

Per TEST-FIX-01-v1: Tests produce traceable evidence files.
Per UI-AUDIT-010: Evidence file linkage for Test Runner.
Per DOC-SIZE-01-v1: Extracted from runner.py to keep modules under 300 lines.

Created: 2026-01-30
"""
import logging
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Evidence directory (try container path first, then local)
EVIDENCE_DIR = Path("/app/evidence") if Path("/app/evidence").exists() else Path("evidence")


def parse_pytest_summary(output: str) -> dict:
    """
    Parse pytest summary line to extract counts.

    Handles formats like:
    - "3 failed, 96 passed, 5 deselected in 2.49s"
    - "96 passed in 2.49s"
    - "3 failed, 96 passed, 5 skipped in 2.49s"
    """
    counts = {"passed": 0, "failed": 0, "skipped": 0, "deselected": 0}

    # Find summary line (usually last few lines)
    for line in reversed(output.split("\n")):
        # Match patterns like "3 failed" or "96 passed"
        if " passed" in line or " failed" in line:
            for key in counts.keys():
                match = re.search(rf"(\d+)\s+{key}", line)
                if match:
                    counts[key] = int(match.group(1))
            break
    return counts


def parse_pytest_output(output: str) -> list:
    """Parse pytest output to extract test results."""
    tests = []

    # Try verbose format first (for -v mode)
    for line in output.split("\n"):
        line = line.strip()
        if " PASSED" in line or " FAILED" in line or " SKIPPED" in line:
            parts = line.split()
            if len(parts) >= 2:
                nodeid = parts[0]
                if " PASSED" in line:
                    outcome = "passed"
                elif " FAILED" in line:
                    outcome = "failed"
                else:
                    outcome = "skipped"
                tests.append({"nodeid": nodeid, "outcome": outcome, "duration": 0.0})

    # If no tests found (quiet mode), parse FAILURES section for failed test names
    if not tests:
        failure_pattern = re.compile(r"_+\s+([\w.:\[\]/\-]+)\s+_+")
        for match in failure_pattern.finditer(output):
            tests.append({"nodeid": match.group(1), "outcome": "failed", "duration": 0.0})

    return tests


def generate_evidence_file(run_id: str, result: dict, category: str = None) -> str:
    """
    Generate an evidence markdown file for a test run.

    Per TEST-FIX-01-v1: Tests produce traceable evidence files.
    Per UI-AUDIT-010: Evidence file linkage for Test Runner.

    Args:
        run_id: Test run ID
        result: Test run result dict
        category: Test category (optional)

    Returns:
        Path to generated evidence file, or None on failure
    """
    try:
        # Ensure evidence directory exists
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

        # Generate filename
        date_str = datetime.now().strftime("%Y-%m-%d")
        cat_suffix = f"-{category.upper()}" if category else ""
        filename = f"TEST-RUN-{date_str}{cat_suffix}-{run_id}.md"
        filepath = EVIDENCE_DIR / filename

        # Determine status emoji and text
        status = result.get("status", "unknown")
        passed = result.get("passed", 0)
        failed = result.get("failed", 0)
        total = result.get("total", 0)

        if status == "completed" and failed == 0:
            status_emoji = "\u2705"
            status_text = "PASSED"
        elif status == "completed":
            status_emoji = "\u26a0\ufe0f"
            status_text = "PARTIAL"
        else:
            status_emoji = "\u274c"
            status_text = "FAILED"

        # Build evidence content
        content = f"""# Test Run Evidence: {run_id}

{status_emoji} **Status:** {status_text}

## Summary

| Metric | Value |
|--------|-------|
| Run ID | `{run_id}` |
| Category | {category or 'all'} |
| Timestamp | {result.get('timestamp', 'N/A')} |
| Duration | {result.get('duration_seconds', 0):.2f}s |
| Total Tests | {total} |
| Passed | {passed} |
| Failed | {failed} |
| Skipped | {result.get('skipped', 0)} |

## Rules Validated

Per TEST-FIX-01-v1: This test run validates the following governance rules:

- **WORKFLOW-SHELL-01-v1**: Self-assessment via containerized tests
- **TEST-GUARD-01-v1**: Test coverage requirements
- **TEST-FIX-01-v1**: Evidence production for completed tasks

## Test Results

"""
        # Add test results
        tests = result.get("tests", [])
        if tests:
            for test in tests[:50]:  # Limit to 50 tests
                outcome = test.get("outcome", "unknown")
                nodeid = test.get("nodeid", "unknown")
                icon = "\u2705" if outcome == "passed" else "\u274c" if outcome == "failed" else "\u23ed\ufe0f"
                content += f"- {icon} `{nodeid}`\n"
        else:
            content += "_No individual test results captured._\n"

        content += f"""
## Command

```bash
{result.get('command', 'N/A')}
```

## Output

<details>
<summary>Full pytest output (click to expand)</summary>

```
{result.get('output', 'No output captured')[:10000]}
```

</details>

---

_Generated by Test Runner API per UI-AUDIT-010_
_Evidence file: `{filename}`_
"""

        # Write file
        filepath.write_text(content)
        return str(filepath)

    except Exception as e:
        # Don't fail the test run if evidence generation fails
        logger.warning(f"Failed to generate evidence file: {e}")
        return None
