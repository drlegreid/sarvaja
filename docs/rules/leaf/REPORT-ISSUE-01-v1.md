# REPORT-ISSUE-01-v1: GitHub Issue Protocol (CERT & STATUS)

**Category:** `governance` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-049
> **Location:** [RULES-GOVERNANCE.md](../governance/RULES-GOVERNANCE.md)
> **Tags:** `reporting`, `github`, `certification`, `status`, `milestone`

---

## Directive

GitHub issues follow two patterns based on scope:

| Type | Purpose | Scope | Attachments |
|------|---------|-------|-------------|
| **CERT** | Strategic milestone certification | Comprehensive | Full evidence |
| **STATUS** | Tactical workflow check (DEV/SLEEP) | Quick update | Minimal |

**CERT validates STATUS:** Certification issues assess delivered items from STATUS reports as part of Definition of Done.

---

## Issue Types

### 1. STATUS Issues (Tactical)

**Purpose:** DEV and SLEEP mode workflow status checks.

**Title Format:** `[STATUS]: {epoch}: {koan_name}`

**Required Content:**
- Status in body: DEV | SLEEP | BLOCKED
- Session summary (1-3 sentences)
- Tasks completed/in-progress
- Blockers (if any)
- Next actions

**Example:**
```
[STATUS]: 1768313000: Three-ULTRAs
```

### 2. CERT Issues (Strategic)

**Purpose:** Certification of strategic milestones with full evidence.

**Title Format:** `[CERT]: {epoch}: {koan_name}`

**Status in body:** COMPLETE | PARTIAL | BLOCKED

**Required Attachments (Definition of Done):**

| Category | Required Evidence |
|----------|-------------------|
| **Tests (All Levels)** | Unit, integration, E2E test results |
| **Living Documentation** | Technical details: request/response payloads |
| **Exploratory Tests** | Screenshots + payloads + intent description |
| **Static Documentation** | Updated docs, README, CHANGELOG |
| **UX Artifacts** | Wireframes, mockups, user flows |
| **Design Artifacts** | Architecture diagrams, sequence diagrams |
| **Software Artifacts** | API specs, schema changes, config updates |

**Validation:** CERT issue MUST reference STATUS issues it validates.

**Example:**
```
[CERT-1768312800] Misread-Intent: COMPLETE
Validates: STATUS-1768310000, STATUS-1768311000, STATUS-1768312000
```

---

## STATUS Template

```markdown
## Status: {TOPIC}

**Epoch:** {timestamp}
**Mode:** DEV | SLEEP
**Koan:** {wisdom_name}

### Progress
- [x] Task 1
- [x] Task 2
- [ ] Task 3 (in progress)

### Blockers
{None | List blockers}

### Next Actions
1. Action 1
2. Action 2

---
*Per REPORT-ISSUE-01-v1*
```

---

## CERT Template

```markdown
## Certification: {MILESTONE}

**Epoch:** {timestamp}
**Koan:** {wisdom_name}
**Status:** COMPLETE | PARTIAL | BLOCKED

### Validates STATUS Issues
- STATUS-{epoch1}: {summary}
- STATUS-{epoch2}: {summary}

### Definition of Done Checklist

#### Tests Delivered
- [ ] Unit tests: {count} passing
- [ ] Integration tests: {count} passing
- [ ] E2E tests: {count} passing
- [ ] Test coverage: {percentage}

#### Living Documentation
- [ ] API request/response examples attached
- [ ] Error scenarios documented
- [ ] Edge cases covered

#### Exploratory Test Results
- [ ] Screenshots attached
- [ ] Payloads documented
- [ ] Intent described for each test

#### Static Documentation
- [ ] README updated
- [ ] CHANGELOG entry added
- [ ] API docs updated

#### UX/Design/Architecture
- [ ] UX artifacts attached (if applicable)
- [ ] Architecture diagrams updated
- [ ] Design decisions documented

### Evidence Attachments
| Type | File | Description |
|------|------|-------------|
| Test Results | test-output.log | pytest results |
| Screenshot | ui-validation.png | Final UI state |
| Payload | api-response.json | Sample response |

### Session Wisdom
> {Zen koan or insight}

---
*Per REPORT-ISSUE-01-v1 | CERT validates STATUS*
```

---

## Workflow

```
DEV Mode:
  STATUS → STATUS → STATUS → ... → CERT
     ↓        ↓        ↓            ↓
  tactical  tactical  tactical  strategic
  updates   updates   updates   validation

SLEEP Mode:
  STATUS (SLEEP) → Review backlog → Resume DEV
```

1. **During DEV:** Post STATUS issues for workflow checkpoints
2. **At Milestone:** Post CERT issue that validates all STATUS issues
3. **During SLEEP:** Post STATUS (SLEEP) with handoff notes

---

## Status Values

### STATUS Issue States
| State | Meaning |
|-------|---------|
| `DEV` | Active development |
| `SLEEP` | Paused, context saved |
| `BLOCKED` | Cannot proceed |

### CERT Issue States
| State | Meaning | Action |
|-------|---------|--------|
| `COMPLETE` | All DoD items met | Close issue |
| `PARTIAL` | Some items met | Keep open |
| `BLOCKED` | Cannot certify | Document blocker |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Use CERT for quick updates | Use STATUS for tactical checks |
| Skip evidence in CERT | Attach all DoD artifacts |
| Close PARTIAL CERT issues | Keep open until COMPLETE |
| Forget to link STATUS in CERT | Reference all validated STATUS issues |

---

## Validation

**STATUS Issues:**
- [ ] Epoch timestamp in title
- [ ] Koan name present
- [ ] Mode specified (DEV/SLEEP/BLOCKED)
- [ ] Next actions listed

**CERT Issues:**
- [ ] References STATUS issues it validates
- [ ] DoD checklist completed
- [ ] Evidence attachments present
- [ ] Tests at all levels documented
- [ ] Exploratory results with screenshots
- [ ] COMPLETE issues closed

---

*Per REPORT-SUMM-01-v1: Session Summary Reporting*
*Per REPORT-HUMOR-01-v1: Session Wisdom (Koan naming)*
