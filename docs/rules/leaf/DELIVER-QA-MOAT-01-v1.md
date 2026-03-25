# DELIVER-QA-MOAT-01-v1: Quality As Competitive Moat

| Field | Value |
|-------|-------|
| **Rule ID** | DELIVER-QA-MOAT-01-v1 |
| **Category** | quality |
| **Priority** | CRITICAL |
| **Status** | ACTIVE |
| **Applicability** | MANDATORY |
| **Created** | 2026-03-25 |

## Directive

Copy-cats can copy features. They cannot copy discipline. Quality is the moat.

## Principles

1. **No feature is done without 3-tier validation** — unit, API, Playwright CRUD with state change
2. **No claim without evidence** — screenshots uploaded, not referenced; tests run, not assumed
3. **Container restart before certification** — if code changed, restart and re-verify; stale state is a lie
4. **QA is the pinnacle of delivery** — not an afterthought, not a checkbox; the final gate that earns trust
5. **Polish compounds** — each session of discipline builds on the last; shortcuts compound into debt

## Anti-Patterns

| Shortcut | Reality |
|----------|---------|
| "Tests pass, ship it" | Did you restart the container? |
| "Screenshots captured" | Are they on GitHub or just your disk? |
| "Works on my machine" | Playwright didn't click it, so it doesn't work |
| "I'll add tests later" | You won't. Write them now or they don't exist |
| "Good enough for now" | Now is all your users see |

## Enforcement

Every delivery session must end with:
1. All 3 tiers green **post-restart**
2. Evidence **uploaded** to GitHub (per GOV-ISSUE-EVIDENCE-01-v1)
3. Commit message states tier results explicitly
