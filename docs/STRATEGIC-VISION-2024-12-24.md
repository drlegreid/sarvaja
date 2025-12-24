# Strategic Vision Analysis: Deep Sleep Protocol & Governance Enhancements

**Date:** 2024-12-24
**Session:** Post Phase 2 Strategic Vision
**Status:** APPROVED

---

## Executive Summary

This document analyzes the strategic vision for sim-ai platform evolution, incorporating:
1. **DSP (Deep Sleep Protocol)** for technical backlog hygiene
2. **Rules Applicability Convention** for meta-referencing gaps to rules
3. **Document Splitting Strategy** for LLM-optimized navigation
4. **TypeDB Document Cross-referencing** for governance integration
5. **Session Milestone Workflow** for GitHub issue integration

---

## 1. DSP: Deep Sleep Protocol (RULE-012)

### What It Is

DSP (Deep Sleep Protocol) is a deliberate, methodical process for **technical backlog hygiene** - unlike aggressive navigation toward business goals. It's inspired by the DSM (Deep Sleep Mode) protocol from localgai.

### DSM Protocol Phases (Foundation)

```
AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE
```

| Phase | Purpose | Sim.ai Adaptation |
|-------|---------|-------------------|
| **AUDIT** | Inventory gaps, debt, orphans | Scan TODO.md + TypeDB for stale items |
| **HYPOTHESIZE** | Form improvement theories | Propose rule/decision changes |
| **MEASURE** | Quantify current state | Run tests, check metrics |
| **OPTIMIZE** | Apply improvements | Update TypeDB, clean backlog |
| **VALIDATE** | Verify improvements | Run full test suite |

### When to Invoke DSP

| Trigger | Action | Cadence |
|---------|--------|---------|
| **Session End** | Quick audit of new gaps | Every session |
| **Milestone** | Full backlog hygiene | Weekly or per milestone |
| **Pre-Release** | Deep technical review | Before major releases |
| **Entropy Alert** | Detected orphan rules/gaps | When TypeDB inference detects |

### DSP vs Business Navigation

| Aspect | DSP (Deep Sleep) | Business Navigation |
|--------|------------------|---------------------|
| **Pace** | Deliberate, methodical | Aggressive, fast |
| **Focus** | Technical debt, backlog | Feature delivery |
| **Scope** | Cleanup, hygiene | New functionality |
| **Evidence** | Audit trails | User stories |
| **Outcome** | Reduced entropy | Customer value |

**Key Insight:** Both modes are necessary. DSP prevents technical debt accumulation while business navigation drives product forward. They should alternate, not compete.

---

## 2. Rules Applicability Convention (RULE-013)

### Problem Statement

Code gaps and TODOs lack traceability to governance rules:
- `# TODO: Fix this later` - No rule reference
- Gaps in TODO.md don't link to enforcing rules
- Hard to audit rule compliance across codebase

### Solution: Meta-Reference Convention

Every code comment, gap, or TODO should reference applicable rules:

```python
# TODO(RULE-002): Extract to separate module for separation of concerns
# FIXME(RULE-009): Version mismatch - check container version first
# GAP-020(RULE-005): Memory threshold exceeded, add monitoring
```

### Format Specification

```
{TYPE}({RULE-ID}): {Description}

Where:
- TYPE: TODO | FIXME | GAP-XXX | HACK | NOTE
- RULE-ID: RULE-001 through RULE-0XX
- Description: Action or context
```

### TypeDB Integration

Rules and gaps are cross-referenced in TypeDB:

```typeql
# Gap references a rule
gap-rule-reference sub relation,
    relates referenced-gap,
    relates governing-rule;

gap sub entity,
    owns gap-id,
    owns description,
    owns location,  # file:line
    plays gap-rule-reference:referenced-gap;

rule-entity sub entity,
    plays gap-rule-reference:governing-rule;
```

---

## 3. Document Splitting Strategy

### Problem Statement

TODO.md is ~950 lines - too large for LLM context efficiency.

### Proposed Structure

```
docs/
├── TODO.md                    # Index only (~100 lines)
├── tasks/
│   ├── TASKS-HIGH-PRIORITY.md      # High priority tasks
│   ├── TASKS-MEDIUM-PRIORITY.md    # Medium priority tasks
│   ├── TASKS-LOW-PRIORITY.md       # Low priority tasks
│   └── TASKS-COMPLETED.md          # Archive
├── backlog/
│   ├── R&D-BACKLOG.md              # Strategic R&D items
│   ├── PHASE-1-COMPLETE.md         # Phase 1 archive
│   ├── PHASE-2-COMPLETE.md         # Phase 2 archive
│   └── PHASE-3-PLANNING.md         # Phase 3 planning
└── gaps/
    ├── GAP-INDEX.md                # Master gap index
    └── GAP-ANALYSIS-*.md           # Per-session analysis
```

### Index Document (TODO.md)

```markdown
# TODO Index - Sim.ai PoC

## Quick Navigation

| Category | Document | Status |
|----------|----------|--------|
| High Priority | [tasks/TASKS-HIGH-PRIORITY.md](tasks/TASKS-HIGH-PRIORITY.md) | X active |
| Medium Priority | [tasks/TASKS-MEDIUM-PRIORITY.md](tasks/TASKS-MEDIUM-PRIORITY.md) | Y active |
| R&D Backlog | [backlog/R&D-BACKLOG.md](backlog/R&D-BACKLOG.md) | Z items |
| Gap Index | [gaps/GAP-INDEX.md](gaps/GAP-INDEX.md) | N gaps |

## Current Focus

1. [Task name](link) - Brief status
2. [Task name](link) - Brief status

## Gap Summary

| ID | Gap | Priority | Rule |
|----|-----|----------|------|
| GAP-001 | ... | HIGH | RULE-002 |
```

### Benefits

1. **LLM Efficiency**: Read only relevant document (~100-200 lines vs 950)
2. **Faster Navigation**: Semantic links guide LLM to correct doc
3. **Better Maintenance**: Each doc has clear ownership
4. **Archive Strategy**: Completed items don't pollute active view

---

## 4. TypeDB Document Entity Type

### Purpose

Cross-reference documentation to governance entities, supporting:
- WebDAV storage (remote)
- Local filesystem (development)
- GitHub (canonical source)

### Schema Addition

```typeql
# Document entity for cross-referencing
document sub entity,
    owns document-id,
    owns document-title,
    owns document-path,           # Local path: docs/RULES.md
    owns document-url,            # Remote: webdav://... or github://...
    owns document-type,           # markdown | yaml | json | code
    owns document-storage,        # local | webdav | github
    owns last-modified,
    owns content-hash;

# Document references rule
document-references-rule sub relation,
    relates referencing-document,
    relates referenced-rule;

# Document references decision
document-references-decision sub relation,
    relates referencing-document,
    relates referenced-decision;

# Document references gap
document-references-gap sub relation,
    relates referencing-document,
    relates referenced-gap;

document plays document-references-rule:referencing-document;
document plays document-references-decision:referencing-document;
document plays document-references-gap:referencing-document;
rule-entity plays document-references-rule:referenced-rule;
decision plays document-references-decision:referenced-decision;
gap plays document-references-gap:referenced-gap;
```

### Workflow: Document-Rule Cross-Reference

```
1. Document created/modified
2. Parser extracts RULE-XXX, DECISION-XXX, GAP-XXX references
3. TypeDB relations created automatically
4. Inference: "Find all documents affected by RULE-002"
5. Inference: "Find orphan rules (no document references)"
```

---

## 5. Session Milestone Workflow

### GitHub Issue Integration

Each session milestone creates:
1. Session log in `./docs/SESSION-{date}-{topic}.md`
2. GitHub issue for tracking (optional, for significant milestones)
3. Cross-reference in TypeDB

### Workflow

```
SESSION START:
1. Create session log from template
2. Log goals, models, tools

SESSION WORK:
3. Log decisions, gaps, artifacts
4. Update TODO.md index
5. Cross-reference to TypeDB

MILESTONE REACHED:
6. Create GitHub issue (if significant)
7. Link issue to session log
8. Update GAP-INDEX with findings

SESSION END:
9. Invoke DSP quick audit
10. Commit all changes
11. Save to claude-mem
12. Push to GitHub
```

### GitHub Issue Format

```markdown
## Session Milestone: {TOPIC}

**Date:** YYYY-MM-DD
**Session Log:** docs/SESSION-{date}-{topic}.md

### Summary
{1-3 sentences}

### Artifacts Created
- [ ] File 1
- [ ] File 2

### Gaps Discovered
- GAP-XXX: Description
- GAP-YYY: Description

### Related Rules
- RULE-001 (if applicable)
- RULE-006 (decisions logged)

### Next Steps
- [ ] Action 1
- [ ] Action 2
```

---

## 6. Implementation Plan

### Immediate (RULE-012, RULE-013)

| Task | Status | Effort |
|------|--------|--------|
| Add RULE-012 (DSP) to RULES-DIRECTIVES.md | 📋 TODO | 30 min |
| Add RULE-013 (Applicability Convention) to RULES-DIRECTIVES.md | 📋 TODO | 30 min |
| Update TypeDB schema with document entity | 📋 TODO | 1 hour |
| Create docs/tasks/ directory structure | 📋 TODO | 30 min |

### Next Session (Document Split)

| Task | Status | Effort |
|------|--------|--------|
| Split TODO.md into index + sub-docs | 📋 TODO | 2 hours |
| Update CLAUDE.md with new structure | 📋 TODO | 30 min |
| Test LLM navigation with split docs | 📋 TODO | 30 min |

### Phase 3 (TypeDB Integration)

| Task | Status | Effort |
|------|--------|--------|
| Implement document parser for rule references | 📋 TODO | 2 hours |
| Add document sync to Governance MCP | 📋 TODO | 2 hours |
| Create orphan rule detection inference | 📋 TODO | 1 hour |

---

## 7. Decision Summary

| ID | Decision | Rationale |
|----|----------|-----------|
| D1 | Adopt DSP for backlog hygiene | Prevents entropy, maintains technical quality |
| D2 | Meta-reference convention | Traceable gaps, auditable compliance |
| D3 | Split TODO.md | LLM efficiency, better maintenance |
| D4 | TypeDB document entity | Unified governance, cross-reference support |
| D5 | Session milestone + GitHub issue | Visibility, external tracking |

---

*Document created per RULE-001: Session Evidence Logging*
*Strategic vision per DSP: AUDIT phase*
