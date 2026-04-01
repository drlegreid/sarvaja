# SRVJ-FEAT-ORCHESTRATOR-01 — Session Orchestrator Design

**Phase**: P1 (Research & Design)
**Status**: COMPLETE
**Date**: 2026-03-31
**Type**: RESEARCH — zero production code

---

## 1. Problem Statement

After 8 phases of AUDIT-TRAIL-01, a clear pattern emerged:

- **Drift**: Sessions abandon methodology by task 7-8 (TDD skipped, tests not run)
- **Context rot**: 40+ feedback rules are read at session start, forgotten mid-session
- **Self-assessment**: The agent marks its own homework — no external enforcement
- **More rules ≠ better compliance**: Enforcement is the bottleneck, not knowledge

The root cause: Claude Code sessions are monolithic, long-running, and self-policed.
No external process validates that the agent actually followed the rules.

## 2. Claude Code CLI Capabilities

### 2.1 Key Flags for Orchestration

| Flag | Purpose | Orchestrator Use |
|------|---------|------------------|
| `--print` | Non-interactive, stdout output | Core execution mode |
| `--output-format json` | Structured JSON output (array) | Parse results programmatically |
| `--session-id <uuid>` | Control session identity | Deterministic session tracking |
| `--resume <id>` | Resume prior session with full context | Multi-turn within a micro-task |
| `--system-prompt <text>` | Override system prompt | Role-specific agent behavior |
| `--append-system-prompt <text>` | Add to default system prompt | Inject rules without losing defaults |
| `--tools <list>` | **Hard constraint** on built-in tools | Role enforcement (read-only researcher) |
| `--allowedTools <list>` | Auto-approve (no user prompt) | Skip permission dialogs |
| `--disallowedTools <list>` | Block specific tools | Prevent destructive actions |
| `--mcp-config <file>` | Load MCP servers | Same governance MCP in orchestrated sessions |
| `--max-budget-usd <n>` | Cost cap per session | Budget enforcement |
| `--permission-mode <mode>` | bypassPermissions / plan / auto | Unattended execution |
| `--no-session-persistence` | Don't save JSONL | Ephemeral validation sessions |
| `--worktree [name]` | Git worktree isolation | Safe implementation sessions |
| `--name <name>` | Session display name | Human-readable session IDs |
| `--json-schema <schema>` | Structured output validation | Force JSON responses |

### 2.2 Execution Model

```
ORCHESTRATOR (Python)
    │
    ├─ Constructs prompt string
    ├─ Pipes to: echo "$PROMPT" | claude --print --output-format json ...
    ├─ Captures stdout as JSON array
    ├─ Parses result block: exit code, cost, duration, session_id
    └─ Runs validation gates before next micro-task
```

**Confirmed working** (tested 2026-03-31):
- `echo "prompt" | claude --print --output-format json` → returns JSON array
- `--session-id` persists session, `--resume` restores full context
- `--tools "Read,Grep"` hard-constrains built-in tools (Bash blocked, agent said TOOL_BLOCKED)
- MCP tools still available even with `--tools` constraint (expected — use `--disallowedTools` for MCP)
- Cost: ~$0.08-0.15 per trivial prompt (cache helps with repeated sessions)

### 2.3 Tool Constraint Behavior

| Mechanism | Scope | Effect |
|-----------|-------|--------|
| `--tools "X,Y"` | Built-in tools only | Hard restrict to listed tools |
| `--allowedTools "X,Y"` | All tools | Auto-approve (no user prompt), doesn't restrict |
| `--disallowedTools "X,Y"` | All tools | Block listed tools |
| `--permission-mode bypassPermissions` | All tools | No prompts at all |

**Implication for agent roles**: Use `--tools` to restrict built-in tools AND `--disallowedTools` to block specific MCP tools per role.

## 3. JSONL Session Schema

### 3.1 Location

```
~/.claude/projects/{project-path-with-dashes}/{uuid}.jsonl
```

Example: `~/.claude/projects/-home-oderid-Documents-Vibe-sarvaja-platform/a686562c-...jsonl`

**137 session files** found in sarvaja project (ranging from 50KB to 529MB).

### 3.2 Message Types

| Type | Frequency | Contains |
|------|-----------|----------|
| `assistant` | ~40% | Model response: text, tool_use, thinking blocks, usage/cost |
| `user` | ~25% | User text, tool_result, IDE context |
| `progress` | ~20% | Hook execution, tool progress |
| `system` | ~5% | API errors, retries, rate limits |
| `queue-operation` | ~3% | enqueue/dequeue events |
| `file-history-snapshot` | ~2% | File backup snapshots per message |
| `custom-title` / `ai-title` | ~1% | Session naming |
| `last-prompt` | ~1% | Last user prompt text |

### 3.3 Key Fields per Type

**assistant message** (richest for validation):
```json
{
  "type": "assistant",
  "message": {
    "model": "claude-opus-4-6",
    "content": [
      {"type": "thinking", "thinking": "..."},
      {"type": "text", "text": "..."},
      {"type": "tool_use", "id": "toolu_...", "name": "Bash", "input": {"command": "..."}}
    ],
    "usage": {
      "input_tokens": N, "output_tokens": N,
      "cache_creation_input_tokens": N, "cache_read_input_tokens": N
    }
  },
  "timestamp": "ISO-8601",
  "sessionId": "uuid",
  "version": "2.1.81",
  "gitBranch": "master"
}
```

**user message with tool_result**:
```json
{
  "type": "user",
  "message": {
    "content": [
      {"type": "tool_result", "tool_use_id": "toolu_...", "content": "...output..."}
    ]
  },
  "permissionMode": "bypassPermissions",
  "entrypoint": "claude-vscode"
}
```

**JSON output (--print --output-format json)** returns array:
```json
[
  {"type": "system", "subtype": "init", "tools": [...], "mcp_servers": [...]},
  {"type": "assistant", "message": {...}},
  {"type": "rate_limit_event", "rate_limit_info": {...}},
  {"type": "result", "subtype": "success", "result": "...",
   "total_cost_usd": 0.14, "duration_ms": 4024,
   "session_id": "uuid", "usage": {...}}
]
```

### 3.4 What's Extractable for Validation

| Signal | Source | Extraction |
|--------|--------|------------|
| Tool calls made | `assistant.message.content[type=tool_use].name` | Tool sequence |
| Test execution | tool_use where name=Bash, input contains "pytest" | Detect test runs |
| Files modified | tool_use where name=Edit/Write | Track file changes |
| Thinking blocks | `assistant.message.content[type=thinking]` | Reasoning audit |
| MCP calls | tool_use where name starts with "mcp__" | Governance compliance |
| Cost per turn | `assistant.message.usage` | Budget tracking |
| Total cost | `result.total_cost_usd` | Session budget |
| Success/failure | `result.subtype` | Pass/fail |
| Tool results | `user.message.content[type=tool_result]` | Actual output data |

## 4. Orchestrator Architecture

### 4.1 Component Diagram

```
┌──────────────────────────────────────────────────────┐
│                SESSION ORCHESTRATOR                   │
│                  (Python script)                      │
│                                                       │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐            │
│  │  Plan    │  │ Prompt   │  │ State    │            │
│  │  Loader  │→│ Builder  │→│ Machine  │            │
│  └─────────┘  └──────────┘  └──────────┘            │
│       ↑                          │                    │
│       │                    ┌─────┴─────┐             │
│       │                    ▼           ▼             │
│  ┌─────────┐         ┌────────┐  ┌─────────┐       │
│  │ JSONL   │←────────│ CLI    │  │Validator │       │
│  │ Parser  │         │ Runner │  │ Engine   │       │
│  └─────────┘         └────────┘  └─────────┘       │
│       │                    │           │             │
│       └────────────────────┘           │             │
│                                        ▼             │
│                               ┌──────────────┐      │
│                               │ Audit Trail  │      │
│                               └──────────────┘      │
└──────────────────────────────────────────────────────┘
        │                            │
        ▼                            ▼
   Claude Code CLI             External Checks
   (--print mode)              (git, pytest, robot)
```

### 4.2 State Machine

```
PLAN_LOADED → TASK_READY → PROMPT_BUILT → SESSION_RUNNING
      ↑                                        │
      │                                   ┌────┴────┐
      │                                   ▼         ▼
      │                              VALIDATING   SESSION_FAILED
      │                                   │         │
      │                              ┌────┴────┐    │
      │                              ▼         ▼    │
      └─────────────────────── TASK_PASSED  TASK_FAILED
                                                    │
                                              ESCALATED
```

### 4.3 Module Breakdown

| Module | Responsibility | Complexity |
|--------|---------------|------------|
| `plan_loader.py` | Parse EPIC → phases → micro-tasks from markdown | S |
| `prompt_builder.py` | Construct role-specific prompts with task + context | M |
| `cli_runner.py` | Invoke `claude --print`, capture JSON, handle errors | S |
| `jsonl_parser.py` | Parse JSONL for tool calls, costs, files changed | M |
| `validator.py` | Run external checks (pytest exit code, git diff, etc.) | M |
| `state.py` | Track task status, session history, orchestrator decisions | S |
| `audit.py` | Log orchestrator decisions, validation results | S |
| `main.py` | CLI entry point, main loop | S |

**Total estimated complexity: MEDIUM** (8 files, no external deps beyond stdlib + subprocess)

### 4.4 Relationship to Existing Code

The project already has `governance/workflows/orchestrator/` (MockStateGraph, budget, spec_tiers).
That code runs **in-process** — the agent orchestrates itself.

The **session orchestrator** is fundamentally different:
- **External** to the Claude Code process
- **Between sessions**, not within them
- **Validates output** rather than trusting self-assessment
- **Controls the CLI** rather than being controlled by it

These are complementary, not competing:
- Existing orchestrator = task prioritization + spec generation (keep as-is)
- Session orchestrator = external enforcement + session lifecycle (new)

## 5. Validation Gates

### 5.1 Gate Types

| Gate | How | What It Proves |
|------|-----|----------------|
| **Exit Code** | `result.subtype == "success"` from JSON output | Session didn't crash |
| **Unit Tests** | `python3 -m pytest tests/unit/ -q; echo $?` | Code compiles, logic correct |
| **Robot E2E** | `robot --outputdir ... tests/e2e/; parse output.xml` | UI works end-to-end |
| **Git Diff** | `git diff --name-only HEAD~1` | Expected files were modified |
| **File Exists** | `os.path.exists(expected_file)` | Artifacts were created |
| **JSONL Audit** | Parse session JSONL for tool call order | Methodology followed |
| **Cost Check** | `result.total_cost_usd < budget` | Budget not exceeded |
| **No Regressions** | Compare test count before/after | Nothing broken |

### 5.2 Methodology Compliance (JSONL Audit)

Parse the session JSONL to detect methodology violations:

```python
# Extract tool call sequence from JSONL
tool_sequence = extract_tool_calls(jsonl_path)
# e.g. ["Read", "Read", "Grep", "Write", "Edit", "Bash(pytest)", "Edit"]

# TDD check: test execution should appear BEFORE implementation
def check_tdd_order(tools):
    """Tests should run before significant edits (RED phase)."""
    first_test = next((i for i, t in enumerate(tools) if "pytest" in t), None)
    first_edit = next((i for i, t in enumerate(tools) if t in ("Edit", "Write")), None)
    if first_edit is not None and first_test is not None:
        return first_test < first_edit  # Test before edit = TDD
    return first_test is not None  # At least tests were run

# Container restart check
def check_container_restart(tools):
    """Per feedback_container_restart: restart after Python changes."""
    has_python_edit = any("Edit" in t or "Write" in t for t in tools)
    has_restart = any("podman restart" in t for t in tools)
    return not has_python_edit or has_restart

# 3-tier check
def check_three_tiers(tools):
    """Per feedback_full_tier_validation: all 3 tiers mandatory."""
    has_unit = any("pytest" in t for t in tools)
    has_api = any("rest-api" in t or "curl" in t for t in tools)
    has_e2e = any("playwright" in t or "robot" in t for t in tools)
    return has_unit and has_api and has_e2e
```

### 5.3 Gate Configuration

Gates are per-role, not per-task:

| Role | Required Gates | Optional Gates |
|------|---------------|----------------|
| Researcher | exit_code, cost | — |
| Test Writer | exit_code, unit_tests, cost | file_exists |
| Implementer | exit_code, unit_tests, git_diff, no_regressions, cost | tdd_order |
| Validator | exit_code, unit_tests, robot_e2e, three_tiers, cost | methodology |
| Planner | exit_code, cost | — |

## 6. Micro-Task Prompt Templates

### 6.1 Template Structure

Every prompt has 4 sections:

```
## ROLE
You are a {role}. {role_constraints}

## CONTEXT
Task: {task_id} — {task_name}
Phase: {phase} of {epic_id}
Previous session outcome: {prev_outcome}
Files relevant: {file_list}

## INSTRUCTIONS
{numbered_steps — max 3}

## COMPLETION CRITERIA
You are DONE when:
{checklist — verifiable from outside}
```

### 6.2 Role Templates

**Researcher** (read-only):
```
## ROLE
You are a read-only researcher. You read code, search, and report findings.
You MUST NOT create, edit, or delete any files.

## INSTRUCTIONS
1. {research_question}
2. Report findings as structured JSON using --json-schema

## COMPLETION CRITERIA
- Findings document produced
- No files modified (git diff is clean)
```

**Test Writer** (tests only):
```
## ROLE
You are a test writer. You write tests that FAIL (RED phase of TDD).
You MUST NOT modify production code (only files under tests/).

## INSTRUCTIONS
1. Read {source_file} to understand the interface
2. Write failing tests in {test_file}
3. Run tests to confirm they FAIL as expected

## COMPLETION CRITERIA
- Test file created/modified under tests/
- Tests run and produce expected failures
- No production code modified
```

**Implementer** (make tests pass):
```
## ROLE
You are an implementer. You make existing failing tests pass.
You MUST NOT write new tests or modify test files.

## INSTRUCTIONS
1. Run tests to see current failures: {test_command}
2. Modify production code to make tests pass
3. Run tests again to confirm GREEN
4. Restart container: podman restart {container}

## COMPLETION CRITERIA
- All previously failing tests now pass
- No test files modified
- Container restarted after changes
```

**Validator** (honest reporter):
```
## ROLE
You are a validator. You run ALL tests and report honestly.
You MUST NOT fix anything. Report exactly what you find.

## INSTRUCTIONS
1. Run unit tests: {unit_command}
2. Run Robot E2E: {robot_command}
3. Check API health: {api_checks}
4. Report results as structured JSON

## COMPLETION CRITERIA
- All 3 tiers executed
- Results reported (pass/fail counts, specific failures)
- No code changes made
```

**Planner** (adjust plan):
```
## ROLE
You are a planner. You review results and produce the next micro-task prompt.
You MUST NOT write code. You produce prompts only.

## INSTRUCTIONS
1. Review validation results: {validation_json}
2. Assess: is the task complete or does it need another iteration?
3. If complete: produce summary. If not: produce next prompt.

## COMPLETION CRITERIA
- Decision documented: ADVANCE or ITERATE
- Next prompt produced (if ITERATE)
- Summary produced (if ADVANCE)
```

### 6.3 Tool Constraints per Role

| Role | `--tools` | `--disallowedTools` |
|------|-----------|---------------------|
| Researcher | `Read,Grep,Glob` | `Edit,Write,Bash` |
| Test Writer | `Read,Grep,Glob,Edit,Write,Bash` | — |
| Implementer | `Read,Grep,Glob,Edit,Write,Bash` | — |
| Validator | `Read,Grep,Glob,Bash` | `Edit,Write` |
| Planner | `Read,Grep,Glob` | `Edit,Write,Bash` |

Note: MCP tools are harder to constrain. Use `--disallowedTools` for specific MCP tool names, or use `--strict-mcp-config` with a minimal MCP config per role.

## 7. Plan File Format

### 7.1 Structure

```yaml
# plans/EPIC-EXAMPLE-01.yaml
epic_id: EPIC-EXAMPLE-01
name: "Example Feature"
phases:
  - id: P1
    name: "Research"
    micro_tasks:
      - id: P1.1
        role: researcher
        prompt: "Investigate how X works in {file}"
        gates: [exit_code, cost]
        budget_usd: 0.50
      - id: P1.2
        role: researcher
        prompt: "Document findings about Y"
        gates: [exit_code, cost]
        budget_usd: 0.50
  - id: P2
    name: "Write Tests"
    micro_tasks:
      - id: P2.1
        role: test_writer
        prompt: "Write failing tests for {feature}"
        gates: [exit_code, unit_tests, cost]
        budget_usd: 1.00
  - id: P3
    name: "Implement"
    micro_tasks:
      - id: P3.1
        role: implementer
        prompt: "Make tests pass for {feature}"
        gates: [exit_code, unit_tests, git_diff, no_regressions, cost]
        budget_usd: 2.00
  - id: P4
    name: "Validate"
    micro_tasks:
      - id: P4.1
        role: validator
        prompt: "Run all tests, report honestly"
        gates: [exit_code, unit_tests, robot_e2e, three_tiers, cost]
        budget_usd: 1.00
```

### 7.2 State File (Auto-generated)

```yaml
# .orchestrator/EPIC-EXAMPLE-01.state.yaml
epic_id: EPIC-EXAMPLE-01
current_phase: P2
current_task: P2.1
status: running
history:
  - task: P1.1
    status: passed
    session_id: "uuid-1"
    cost_usd: 0.23
    duration_ms: 45000
    gates: {exit_code: true, cost: true}
  - task: P1.2
    status: passed
    session_id: "uuid-2"
    cost_usd: 0.31
    duration_ms: 52000
    gates: {exit_code: true, cost: true}
total_cost_usd: 0.54
total_duration_ms: 97000
escalations: []
```

## 8. Execution Flow

```
orchestrator run plans/EPIC-EXAMPLE-01.yaml

  1. Load plan → parse YAML
  2. Load or create state file
  3. Find next pending micro-task
  4. Build prompt from template + task config
  5. Execute:
     echo "$PROMPT" | claude --print \
       --output-format json \
       --session-id $(uuidgen) \
       --system-prompt "$ROLE_PROMPT" \
       --tools "$ROLE_TOOLS" \
       --max-budget-usd $TASK_BUDGET \
       --permission-mode bypassPermissions \
       --mcp-config .mcp.json \
       --name "EPIC-EXAMPLE-01/P2.1"
  6. Parse JSON output → extract result, cost, session_id
  7. Run validation gates:
     a. Check exit code from result block
     b. Run pytest, check exit code
     c. Run git diff, verify expected files
     d. Parse JSONL for methodology compliance
  8. If ALL gates pass:
     → Update state: task=passed
     → Advance to next micro-task
     → Go to step 3
  9. If ANY gate fails:
     → Update state: task=failed, record which gate
     → Escalate: log failure, pause for human review
     → Do NOT retry in same context (fresh session if retrying)
  10. When all tasks complete:
      → Run final validator session
      → Produce summary report
      → Update MCP task status
```

## 9. Honest Assessment

### 9.1 What's Feasible (P2 MVP)

- **CLI piping works**: `echo | claude --print --output-format json` is reliable
- **Session persistence works**: `--session-id` + `--resume` for multi-turn
- **Tool constraints work**: `--tools` hard-constrains built-in tools
- **Cost tracking works**: `result.total_cost_usd` in JSON output
- **JSONL parsing works**: All tool calls, thinking, results are logged
- **External validation works**: pytest exit code, git diff, file existence
- **System prompt injection works**: `--system-prompt` and `--append-system-prompt`

### 9.2 What's Tricky (Needs Investigation in P2)

- **MCP tool constraints**: `--tools` only affects built-ins. MCP tools need `--disallowedTools` with exact names, or `--strict-mcp-config` with per-role MCP configs. Verbose but doable.
- **Long sessions**: For implementation tasks, the agent may need 20+ tool calls. `--max-budget-usd` helps, but the orchestrator can't interrupt mid-session.
- **Test Writer role purity**: The agent may struggle to write tests WITHOUT also trying to fix them. Strong system prompt + `--tools` constraint (no prod file paths in allowedTools?) helps, but isn't bulletproof.
- **Prompt size**: Rich prompts with context eat input tokens. Balance context vs cost.

### 9.3 What's Aspirational (P3+)

- **Adaptive planning**: Planner role that dynamically adjusts remaining tasks based on validation results. Requires the planner to output structured plan changes.
- **Parallel sessions**: Multiple independent micro-tasks in parallel. Claude subscription = one session at a time. Could use worktrees + multiple terminals, but rate limits apply.
- **Learning from failures**: Cross-session memory of what worked and what didn't. ChromaDB integration possible.
- **GUI automation fallback**: xdotool/xdg for VS Code extension interaction. Fragile and unnecessary — CLI is sufficient.

### 9.4 What Won't Work

- **Real-time intervention**: Can't interrupt a `--print` session mid-execution. Must wait for completion.
- **Guaranteed role compliance**: Agent might ignore system prompt constraints in edge cases. Tool constraints are the hard enforcement; prompts are soft.
- **Zero cost overhead**: Each micro-task session pays cache warm-up cost (~$0.08). 20 micro-tasks = ~$1.60 in overhead alone. Mitigate with `--resume` for multi-turn within a task.
- **VS Code extension API**: No programmatic API for the VS Code extension. CLI is the only scriptable interface.

## 10. P2 Scope Estimate (Build the MVP)

### Deliverables

| Module | Complexity | Description |
|--------|-----------|-------------|
| `cli_runner.py` | S | subprocess wrapper for `claude --print` |
| `jsonl_parser.py` | M | Extract tool calls, cost, files from JSONL |
| `validator.py` | M | Gate engine: pytest, git diff, JSONL audit |
| `prompt_builder.py` | S | Template rendering with role/task/context |
| `plan_loader.py` | S | YAML → task queue |
| `state.py` | S | State persistence (YAML) |
| `main.py` | S | CLI entry point, main loop |
| Example plan | S | One real EPIC as YAML |

**Total P2 complexity: MEDIUM**
**Dependencies: none** (stdlib + subprocess + PyYAML)

### Suggested P2 Micro-Tasks (Dogfooding the Orchestrator to Build the Orchestrator)

1. Write `cli_runner.py` + unit tests (S)
2. Write `jsonl_parser.py` + unit tests (M)
3. Write `validator.py` + unit tests (M)
4. Write `prompt_builder.py` + unit tests (S)
5. Write `plan_loader.py` + `state.py` + unit tests (S)
6. Write `main.py` + integration test with real CLI call (M)
7. Create example plan for a real EPIC, dry-run (S)
8. Validate: run orchestrator on itself (meta-test) (M)

## 11. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI vs API | CLI (`--print`) | Subscription constraint; no API cost |
| Sequential vs parallel | Sequential | One session at a time; rate limits |
| YAML vs JSON plans | YAML | Human-readable, editable |
| Retry policy | No retry, escalate | Fresh context > retrying in rotted context |
| Session persistence | On (default) | JSONL needed for methodology audit |
| Role enforcement | Tools + prompt | Tools = hard constraint; prompt = soft guidance |
| State storage | YAML files | Simple, git-trackable, no DB needed |
| Budget per task | Configurable | `--max-budget-usd` per micro-task |

## 12. References

- TEST-E2E-01-v1: 3-tier validation mandate
- TEST-HOLO-01-v1: Holographic test output
- WORKFLOW-AUTO-01-v1: Halt commands
- RECOVER-AMNES-01-v1: Context recovery
- RECOVER-CRASH-01-v1: File size limits
- CONTAINER-DEV-01: Container restart after changes
- GOV-MCP-FIRST-01-v1: MCP as source of truth
- feedback_container_restart: Always restart after Python changes
- feedback_full_tier_validation: All 3 tiers regardless of risk
- feedback_tdd_strict_halt: RED→GREEN→REFACTOR, one at a time
- feedback_honest_e2e_suite: Solid tests first, fixes second
