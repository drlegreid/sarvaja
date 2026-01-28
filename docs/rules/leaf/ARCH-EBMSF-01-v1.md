# ARCH-EBMSF-01-v1: EBMSF Architecture Standards

**Category:** `architecture` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** TECHNICAL
**Updated:** 2026-01-28

> **Location:** [RULES-ARCHITECTURE.md](../technical/RULES-ARCHITECTURE.md)
> **Tags:** `architecture`, `security`, `code-review`, `ebmsf`, `test-evidence`

---

## Directive

All architecture MUST follow EBMSF (Evidence-Based Multi-Session Framework) standards:

1. **Code Reviews Required** - All changes require peer review before merge
2. **No Hardcoded Secrets** - Credentials MUST be in `.env` or secret management
3. **Evidence-Based Decisions** - Architecture changes require documented rationale
4. **Session Continuity** - Design for multi-session agent collaboration
5. **Test Evidence Structure** - All tests MUST produce verifiable evidence (see below)

---

## Test Evidence Structure (EBMSF-TEST)

Every test (unit, integration, e2e) MUST include these evidence layers:

### 1. Business Intent (WHY)
What business requirement or governance rule is being validated.

```robot
[Documentation]    Verify rule creation enforces mandatory fields
...                Per GOV-RULE-01-v1: Rules must have title, category, priority
```

### 2. Technical Intent (WHAT)
The specific technical action being performed and the expected system behavior.

#### 2a. Action (DO)
The concrete operation: API request, UI interaction, or function call.

```robot
# API: method, endpoint, payload
${response}=    POST    ${BASE_URL}/api/rules    ${rule_payload}

# UI: locator, interaction, data
Click Element    css=[data-testid="create-rule-btn"]
Input Text       css=[data-testid="rule-title"]    Test Rule
```

#### 2b. Result (GOT)
The actual system response or outcome captured as evidence.

```robot
# API: capture response code, body, headers
${status}=      Convert To Integer    ${response.status_code}
${body}=        Set Variable    ${response.json()}

# UI: capture element state, text, visibility
${title_text}=    Get Text    css=[data-testid="rule-title-display"]
${is_visible}=    Element Should Be Visible    css=[data-testid="success-toast"]
```

### 3. Assertions with Evidence (PROVE)
Explicit comparison of expected vs actual, capturing both values.

```robot
# GOOD: Explicit expected vs actual
Should Be Equal As Integers    ${status}    201
...    msg=Expected 201 Created but got ${status}
Should Be Equal    ${body}[title]    Test Rule
...    msg=Expected title 'Test Rule' but got '${body}[title]'

# BAD: Vague assertion without evidence
Should Be True    ${result}    # What was expected? What was actual?
```

### Anti-Pattern: Lenient Tests

| Lenient (BAD) | Evidence-Based (GOOD) |
|---------------|----------------------|
| `Should Be True    ${result}` | `Should Be Equal    ${result}    expected_value    msg=Got ${result}` |
| `Should Not Be Empty    ${list}` | `Length Should Be    ${list}    5    msg=Expected 5 items, got ${list.__len__()}` |
| `Status Should Be    200` | `Should Be Equal As Integers    ${status}    200    msg=API returned ${status}: ${body}` |
| No documentation | `[Documentation]    Per RULE-ID: Business intent` |

---

## Validation

- [ ] Code review completed before merge
- [ ] No secrets in committed code
- [ ] Architectural Decision Record (ADR) created for changes
- [ ] Session evidence logged
- [ ] Tests include business intent documentation
- [ ] Tests capture actual results as evidence
- [ ] Assertions compare expected vs actual with descriptive messages

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Skip code reviews | Require approval before merge |
| Commit secrets to git | Use `.env` and `.gitignore` |
| Make undocumented changes | Create ADRs for decisions |
| Design for single session | Consider multi-agent collaboration |
| Write tests without documentation | Include business + technical intent |
| Use `Should Be True` without context | Use typed assertions with `msg=` |
| Skip capturing actual results | Store response/element state as evidence |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
