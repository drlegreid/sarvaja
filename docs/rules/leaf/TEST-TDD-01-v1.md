# TEST-TDD-01-v1: Test-Driven Development Standard

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** N/A (new rule)
> **Location:** [RULES-OPERATIONAL.md](../operational/RULES-OPERATIONAL.md)
> **Tags:** `testing`, `tdd`, `quality`, `methodology`

---

## Directive

New features and bug fixes MUST follow Test-Driven Development (TDD) methodology: write failing tests first, then implement code to make them pass, then refactor while maintaining green tests.

---

## Red-Green-Refactor Cycle

```
┌─────────────────────────────────────────────────┐
│  1. RED: Write failing test                     │
│     - Define expected behavior first            │
│     - Test MUST fail initially                  │
│     - Verifies test actually tests something    │
├─────────────────────────────────────────────────┤
│  2. GREEN: Make test pass                       │
│     - Write minimum code to pass                │
│     - No premature optimization                 │
│     - Focus on making it work                   │
├─────────────────────────────────────────────────┤
│  3. REFACTOR: Improve while green               │
│     - Clean up code structure                   │
│     - Extract duplication                       │
│     - Tests MUST stay green                     │
└─────────────────────────────────────────────────┘
```

---

## Application by Test Level

| Level | TDD Application |
|-------|-----------------|
| **Unit** | MANDATORY - Write unit test first |
| **Integration** | RECOMMENDED - Define contract first |
| **E2E** | OPTIONAL - May follow BDD exploration |
| **Bug Fix** | MANDATORY - Reproduce bug in test first |

---

## Test Pyramid

Follow test distribution for sustainable test suite:

```
        /\
       /  \  E2E (10%)
      /────\  - Few, slow, high-fidelity
     /      \
    /        \  Integration (20%)
   /──────────\  - API contracts, DB interactions
  /            \
 /              \  Unit (70%)
/────────────────\  - Fast, isolated, many
```

---

## TDD for Bug Fixes

1. **Reproduce**: Write test that fails with current bug
2. **Verify**: Confirm test actually captures the bug
3. **Fix**: Implement minimal fix
4. **Confirm**: Test now passes
5. **Regress**: Add to regression suite

---

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Write code first, tests after | Tests define the specification |
| Skip RED phase | Always see the test fail first |
| Fix failing test by changing assertion | Fix the code, not the test |
| Write tests that always pass | Tests must be falsifiable |
| Test implementation details | Test behavior/outcomes |

---

## Evidence Requirements

Per TEST-EVID-01-v1, TDD evidence includes:
- Test written BEFORE implementation commit
- Test initially fails (RED evidence)
- Test passes after implementation (GREEN evidence)
- Refactor commits maintain green status

---

## Validation

- [ ] Failing test exists before implementation
- [ ] Test captures expected behavior
- [ ] Implementation makes test pass
- [ ] Refactoring maintains passing tests
- [ ] Test pyramid balance maintained

## Test Coverage

**2 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/kanren_advanced.robot` | unit |
| `tests/robot/unit/kanren_constraints.robot` | unit |

```bash
# Run all tests validating this rule
robot --include TEST-TDD-01-v1 tests/robot/
```

---

*Per GAP-TEST-EVIDENCE-003: TDD/BDD governance rules*
*Per TEST-QUAL-01-v1: Quality over speed*
