---
description: Rule compliance checkpoint - validate session follows governance rules
allowed-tools: mcp__gov-core__rules_query, mcp__gov-core__health_check, Read, Glob, Grep
---

# Checkpoint Protocol (SESSION-EVID-01-v1 + GAP-DOC-01-v1)

Run rule compliance checkpoint to verify session follows governance rules.

## Compliance Checks

### 1. Session Evidence (SESSION-EVID-01-v1)
- [ ] Session has thought chain documented
- [ ] Artifacts tracked with create/modify/delete actions
- [ ] Metadata recorded (models, tools, tokens)

### 2. Gap Documentation (GAP-DOC-01-v1)
For each discovered gap:
- [ ] GAP entry in GAP-INDEX.md with Status column
- [ ] Evidence file exists in docs/gaps/evidence/
- [ ] Links between index and evidence are correct

### 3. Test Validation (TEST-FIX-01-v1)
For any claimed fixes:
- [ ] Tests exist proving the fix works
- [ ] Tests are passing
- [ ] No skipped tests without documented reason

## Execution Steps

1. **Query Active Rules**:
   ```
   rules_query(priority="CRITICAL", status="ACTIVE")
   ```

2. **Check Session Evidence**:
   - Search for SESSION-YYYY-MM-DD files in docs/
   - Verify current session has evidence

3. **Validate Gap Links**:
   - Read docs/gaps/GAP-INDEX.md
   - For OPEN gaps, verify evidence/ files exist
   - Check evidence file links are valid

4. **Audit Test Coverage**:
   - Check for skipped tests: `grep -r "pytest.mark.skip" tests/`
   - Each skip should have valid reason

## Output Format

```
=== CHECKPOINT ===
Session: SESSION-YYYY-MM-DD-TOPIC

RULE COMPLIANCE:
- SESSION-EVID-01: [PASS/FAIL] - Evidence logged
- GAP-DOC-01: [PASS/FAIL] - X gaps with evidence
- TEST-FIX-01: [PASS/FAIL] - X tests passing

GAPS NEEDING ATTENTION:
- GAP-XXX: Missing evidence file
- GAP-YYY: Status mismatch

RECOMMENDATIONS:
1. [action items if any]
```

## Quick Fix Actions

If compliance issues found:
1. **Missing session evidence**: Create docs/SESSION-{date}-{topic}.md
2. **Missing gap evidence**: Create docs/gaps/evidence/GAP-XXX.md
3. **Broken links**: Update GAP-INDEX.md with correct paths
4. **Skipped tests**: Document reason or fix underlying issue

## Related Rules

- SESSION-EVID-01-v1: Session evidence logging
- GAP-DOC-01-v1: INDEX+EVIDENCE pattern for gaps
- TEST-FIX-01-v1: Verify fixes before claiming done
- DOC-LINK-01-v1: Document linking format
