# Exploratory Testing Patterns & Workflows

> **Companion to**: [RULES-EXPLORATORY-TESTING.md](RULES-EXPLORATORY-TESTING.md)
> **Context**: Sarvaja governance platform (Trame/Vuetify UI, FastAPI, Playwright MCP, REST MCP)
> **Sources**: dev.to/johnonline35 (Verdex), Medium/rahulbhardwaj (AI-Healing)

---

## 1. Progressive Disclosure for Trame/Vuetify (H-UI-004)

### The Problem

Accessibility trees omit non-semantic containers. A `VCard` with `data-testid="task-card"` appears
as bare `generic` in the snapshot. AI generates brittle `.nth(N)` selectors because structural
anchors (`data-testid`, `class`, `id`) are invisible in the accessibility tree.

### The 4-Level Workflow (Adapted for Sarvaja)

**Level 1 — Semantic Overview**: `browser_snapshot` (~2k tokens)
- Shows roles, names, interactive elements
- Vuetify components become generic/button/textbox nodes
- Use to identify target elements and their ref IDs

**Level 2 — Container Discovery**: Navigate DOM from ref
- Find stable boundaries: `data-testid`, `v-card`, `v-dialog` wrappers
- In Trame views, look for `attrs={"data-testid": "..."}` patterns
- Our convention: `data-testid` on VCard, VDialog, VDataTable, VBtn

**Level 3 — Pattern Recognition**: Identify repeating structures
- Task list → rows with same structure (task_id, status, agent chips)
- Rule list → cards with directive, status badge, action buttons
- Session list → rows with session_id, agent, timestamp

**Level 4 — Anchor Extraction**: Find unique differentiators
- Task rows: unique `task_id` text (e.g., "EPIC-CLEANUP-001")
- Rule cards: unique `rule_id` or directive text
- Agent chips: unique `agent_id`

### Token Budget (Per Selector)

| Approach | Tokens | Quality |
|----------|--------|---------|
| Full DOM dump | 50k+ | Information overload, hallucinations |
| Progressive 4-level | ~2-5k | Focused, accurate |
| Blind `.nth()` guess | 0 | Brittle, breaks on DOM changes |

**Research**: Information overload degrades LLM performance (arxiv.org/abs/2307.03172).
Context rot occurs when relevant info is buried in long contexts (research.trychroma.com/context-rot).

---

## 2. Container → Content → Role Pattern (H-UI-002)

### The Pattern

```
Container scope  → Content filter    → Role selector
getByTestId(X)   → filter({hasText}) → getByRole("button")
```

### Sarvaja Examples

```javascript
// Task list: click "Edit" on specific task
getByTestId("task-row").filter({hasText: "EPIC-CLEANUP-001"}).getByRole("button", {name: "Edit"})

// Rule card: expand specific rule
getByTestId("rule-card").filter({hasText: "GOV-RULE-01"}).getByRole("button", {name: "Expand"})

// Session detail: click tool call tab
getByTestId("session-detail").getByRole("tab", {name: "Tool Calls"})

// Agent dashboard: select agent
getByTestId("agent-card").filter({hasText: "code-agent"}).getByRole("button")
```

### Without data-testid (Fallback)

When no test ID exists, use structure + content:

```javascript
// Fallback: structure scope → content filter → role
page.locator("section > div").filter({hasText: "MacBook Pro"}).getByRole("button", {name: "Add"})
```

This is less stable but still better than `.nth()`.

### Anti-Patterns to Reject

```javascript
// REJECT: Positional selectors
getByRole('button').nth(8)

// REJECT: Unknown-depth parent traversal
getByRole('heading', {name: 'Task'}).locator('..').locator('..').getByRole('button')

// REJECT: Ambiguous role-only selectors in repeating contexts
getByRole('button', {name: 'Delete'})  // which Delete button?
```

---

## 3. AI Self-Healing Cycle (H-UI-005)

### Three-Agent Architecture (From Medium Article)

| Agent | Role | Our Equivalent |
|-------|------|----------------|
| **Planner** | Explores app, produces test plan | Claude Code + `browser_snapshot` |
| **Generator** | Transforms plan into test files | Claude Code + `.robot` generation |
| **Healer** | Executes tests, repairs failures | Claude Code + Playwright MCP re-snapshot |

### 5-Step Healing Protocol

```
1. RUN:     Execute test suite (Robot Framework / pytest)
2. CAPTURE: MCP logs structured failure data (selector, error, page state)
3. ANALYZE: AI agent scans failure + re-snapshots page
4. PROPOSE: Agent suggests fix (new selector, wait, retry)
5. LEARN:   Record healing event as session evidence
```

### Healing Decision Matrix

| Confidence | Action | Record |
|------------|--------|--------|
| >80% | Auto-update selector | `session_test_result(status="HEALED")` |
| 50-80% | Propose fix, await human review | `session_test_result(status="REVIEW")` |
| <50% | Flag as potential real bug | `session_test_result(status="BUG_CANDIDATE")` |

### Intent-Based Selector Recovery

Old approach: Hardcoded fallback chains (`if selector fails, try X, then Y`).
New approach: AI infers **intent** of the selector and finds semantic match.

Example: If `getByTestId("task-status")` fails after a refactor:
1. Re-snapshot the page
2. AI sees a chip/badge element near task rows containing "DONE"/"OPEN"
3. AI generates: `getByTestId("task-row").filter({hasText: "TASK-001"}).locator("[role=status]")`
4. Record the healing event

---

## 4. Sarvaja-Specific Check Execution (via MCP)

### Data Integrity Checks (REST MCP)

All heuristic checks should be run via `mcp__rest-api__test_request`:

```
# H-TASK-001: Check task descriptions
mcp__rest-api__test_request(method="GET", endpoint="/api/tasks?limit=200")
→ Validate: all non-CLOSED tasks have description.length > 10

# H-API-001: Endpoint health
mcp__rest-api__test_request(method="GET", endpoint="/api/health")
→ Validate: statusCode == 200

# H-CROSS-001: Service layer coverage
mcp__rest-api__test_request(method="GET", endpoint="/api/mcp/readiness")
→ Validate: service_layer.* == "SERVICE_LAYER" for all 4 domains
```

**Why REST MCP over server-side httpx**: The server-side runner (`POST /api/tests/heuristic/run`)
calls `localhost:8082` from inside the container, causing self-referential timeouts on API checks.
REST MCP calls from Claude Code host bypass this limitation.

### UI Checks (Playwright MCP)

```
# H-UI-001: Selector stability scan
browser_navigate("http://localhost:8081")
browser_snapshot
→ Scan snapshot for .nth() patterns in any test file references

# H-UI-003: data-testid coverage (automated file scan)
→ Scan agent/governance_ui/views/**/*.py for VCard/VDialog/VBtn without data-testid
```

---

## 5. LLM-Facing API Design Principles (From Verdex)

### Do: Return Raw Structural Facts

```json
{"tag": "div", "attrs": {"data-testid": "task-card"}, "depth": 2}
```

### Don't: Add Interpretation Layers

```json
{"type": "task-card", "role": "list-item", "confidence": 0.85}
```

**Why**: Heuristics bake in assumptions that break on edge cases. LLMs can self-correct
from raw facts but cannot override baked-in interpretations.

**Principle**: Keep capability in tools, strategy in configuration.
Tools provide deterministic building blocks; the LLM composes them contextually.

---

## 6. Known Limitations

- Progressive disclosure (Verdex) requires strong LLMs (Claude Sonnet 4+ or equivalent)
- Self-healing confidence thresholds (80%/50%) are heuristic, not theoretically justified
- Trame/Vuetify renders components server-side — accessibility tree may differ from client-rendered SPAs
- `data-testid` convention requires consistent adoption across all view files
- Token budget (~5k per selector) is empirical, not guaranteed

---

## Sources (with Local Copies)

| Source | URL | Local Copy |
|--------|-----|------------|
| Verdex (dev.to) | [Link](https://dev.to/johnonline35/why-ai-cant-write-good-playwright-tests-and-how-to-fix-it-knn) | `docs/rules/Why AI Can't Write Good Playwright Tests*.html` |
| AI-Healing (Medium) | [Link](https://medium.com/@rahulbhardwaj8851046/rethinking-ui-test-automation-the-rise-of-ai-healing-with-playwright-mcp-bd420882930f) | `docs/rules/🤖 Rethinking UI Test Automation*.html` |
| Context rot research | [Link](https://research.trychroma.com/context-rot) | — |
| Attention degradation | [Link](https://arxiv.org/abs/2307.03172) | — |
