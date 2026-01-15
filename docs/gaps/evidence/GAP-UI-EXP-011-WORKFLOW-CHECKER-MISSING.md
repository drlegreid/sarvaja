# GAP-UI-EXP-011: Workflow Checker File Missing

**Status:** RESOLVED
**Priority:** HIGH
**Category:** functionality
**Discovered:** 2026-01-14 via Playwright exploratory testing
**Resolved:** 2026-01-14

## Problem Statement

The Workflow Compliance view failed with ERROR status because it could not find the workflow checker file at `/app/.claude/hooks/checkers/workflow_checker.py`.

## Root Cause

The `.claude` directory was not mounted as a volume in the Docker/Podman container. The `docker-compose.yml` volumes only included:
- `./agent:/app/agent:ro`
- `./governance:/app/governance:ro`
- `./docs:/app/docs:ro`
- `./evidence:/app/evidence:rw`

The `.claude/hooks/checkers/workflow_checker.py` file existed locally but was not accessible inside the container.

## Fix Applied

Added `.claude` directory to the container volumes in `docker-compose.yml`:

```yaml
volumes:
  - ./agent:/app/agent:ro
  - ./governance:/app/governance:ro
  - ./docs:/app/docs:ro
  - ./evidence:/app/evidence:rw
  - ./.claude:/app/.claude:ro  # GAP-UI-EXP-011: Mount hooks/checkers for workflow compliance
```

## Verification

Playwright test confirmed the Workflow view now shows actual compliance status:
- Compliance Status: VIOLATIONS (real check result, not FileNotFoundError)
- Checks Passed: 1
- Issues Found: 2
- Actual violation: "RULE-024 CLAUDE.md not found - context recovery impaired"

The workflow checker is now running and reporting real compliance issues, not a file-not-found error.

## Files Modified

| File | Changes |
|------|---------|
| `docker-compose.yml` | Added `./.claude:/app/.claude:ro` volume mount |

## Related

- Rules: RULE-028 (Change Validation Protocol)
- GAP-UI-EXP-006: Similar container path issue (resolved same session)
- Session: SESSION-2026-01-14-GAP-COMPLETION

---
*Per GAP-DOC-01-v1: Full technical details in evidence file*
