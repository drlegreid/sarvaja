# RD-RESEARCH-003: Long-Running Agent Harnesses

**Status:** COMPLETE | **Priority:** HIGH | **Category:** R&D
**Source:** [Anthropic Engineering](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
**Date:** 2026-01-21

---

## Executive Summary

Long-running agents need harness architectures with explicit state artifacts. The key insight: decompose into Initializer + Coding agents with clear handoff mechanisms.

---

## Core Architecture

### Dual-Agent Pattern

```
┌──────────────────────────────────────────────┐
│              FIRST CONTEXT WINDOW             │
│  ┌────────────────────────────────────────┐  │
│  │         INITIALIZER AGENT              │  │
│  │  - Creates feature requirements        │  │
│  │  - Writes automation scripts           │  │
│  │  - Establishes git history             │  │
│  │  - Generates progress docs             │  │
│  └────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────┘
                       │
                       ▼ [State Artifacts]
┌──────────────────────────────────────────────┐
│           SUBSEQUENT CONTEXT WINDOWS          │
│  ┌────────────────────────────────────────┐  │
│  │           CODING AGENT                 │  │
│  │  1. Verify working directory           │  │
│  │  2. Review progress logs               │  │
│  │  3. Parse feature requirements         │  │
│  │  4. Execute init.sh + baseline tests   │  │
│  │  5. Implement ONE feature              │  │
│  │  6. Commit + update progress           │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
```

### State Artifacts

| Artifact | Purpose | Format |
|----------|---------|--------|
| `claude-progress.txt` | Activity log | Plain text |
| `init.sh` | Environment resurrection | Shell script |
| Git history | Completed work record | Commits |
| `features.json` | Done vs remaining | JSON |

> **Key Finding**: JSON > Markdown for feature tracking. Models resist corrupting structured formats.

---

## Session Startup Protocol

Each new session MUST follow this sequence:

```bash
1. pwd                      # Verify location
2. Review progress logs     # What happened before?
3. Parse feature list       # What's next?
4. ./init.sh                # Resurrect environment
5. Run baseline tests       # Catch prior regressions
6. Begin work               # Only AFTER above pass
```

**Why**: Prevents building on unstable foundations. Catches bugs before new work compounds them.

---

## Implementation Discipline

### One Feature Per Session

```
Session N:
  ├── Pick ONE feature from pending list
  ├── Implement with tests
  ├── Commit with descriptive message
  ├── Update progress file
  └── Leave code mergeable

Session N+1:
  ├── Read progress
  ├── Verify N's work didn't break anything
  └── Pick NEXT feature
```

### Failure Mode Mitigations

| Problem | Solution |
|---------|----------|
| Premature completion claims | Comprehensive feature checklist |
| Buggy handoffs | Git + progress + baseline tests |
| Environment confusion | `init.sh` eliminates discovery |
| Partial implementations | Single-feature-per-session |

---

## Testing Requirements

**Baseline Testing**:
- Run BEFORE starting new work
- E2E verification (browser automation)
- User-perspective validation

**Avoid**:
- Unit test false positives
- Marking features complete without E2E verification
- Skipping baseline on "it worked last time"

---

## Application to Sarvaja

### Current Alignment

| Pattern | Our Status | Implementation |
|---------|------------|----------------|
| Progress logging | DONE | `evidence/SESSION-*.md` |
| Init script | MISSING | Need `scripts/session_init.sh` |
| Feature tracking | PARTIAL | TODO.md but not JSON |
| Baseline tests | PARTIAL | Tests exist but no session startup |

### Recommended Actions

1. **Create Session Init Script**
   ```bash
   scripts/session_init.sh
   # - health_check()
   # - Run baseline tests
   # - Load TODO.md state
   ```

2. **Convert TODO.md to JSON**
   - Better structure preservation
   - Easier parsing for agents
   - Resistance to corruption

3. **Add Baseline Test Gate**
   - Must pass before new work
   - Catches cross-session regressions

4. **Enhance Progress Artifacts**
   - `claude-progress.txt` equivalent
   - Machine-readable session summaries

---

## Key Quotes

> "Each new session begins with no memory of what came before."

> "Work on exactly one feature per session."

> "Leave environment clean (mergeable code quality)."

> "Baseline testing catches bugs introduced in prior sessions before new work begins."

---

## Sources

- [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)

---

*Per WORKFLOW-RD-01-v1: R&D Workflow with Human Approval*
