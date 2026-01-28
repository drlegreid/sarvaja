# RD-RESEARCH-002: Anthropic Context Engineering

**Status:** COMPLETE | **Priority:** HIGH | **Category:** R&D
**Source:** [Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
**Date:** 2026-01-21

---

## Executive Summary

Context engineering is the strategic curation of tokens for LLM inference. It's the natural evolution of prompt engineering - less about finding right words, more about optimal information configuration.

---

## Core Principles

### 1. Context as Finite Resource

Even as capabilities scale, treating context as precious remains central to building reliable agents.

```
n² pairwise relationships → computational strain
More tokens → reduced precision
Extended context → long-range reasoning degradation
```

### 2. Three Anti-Rot Techniques

| Technique | Description | Output |
|-----------|-------------|--------|
| **Compaction** | Summarize when approaching limits | Condensed history |
| **Note-Taking** | Persistent memory files outside context | External state |
| **Sub-Agents** | Delegate tasks to clean contexts | 1-2K token summaries |

### 3. Prompt Structure Pattern

```xml
<background_information>
  Domain knowledge, project context
</background_information>

<instructions>
  ## Tool guidance
  ## Output description
</instructions>
```

### 4. Tool Design Guidelines

| Do | Don't |
|----|-------|
| Single-action tools | Multi-purpose tools |
| Self-contained operations | Nested dependencies |
| Token-efficient returns | Verbose outputs |
| Clear parameter names | Ambiguous interfaces |

> "If humans cannot definitively identify the right tool, agents cannot either."

---

## Just-In-Time Context Pattern

**Anti-pattern**: Pre-load all potentially relevant data

**Pattern**: Maintain lightweight identifiers, load at runtime

```
Stored: [file paths, queries, links]
Action: → Load dynamically when needed
Benefit: → Progressive discovery through exploration
```

This mirrors human cognition: we don't memorize entire codebases, we navigate them.

---

## Multi-Agent Architecture

```
┌───────────────────────────────────────┐
│         Main Agent (Orchestrator)      │
│  - Maintains clean working context     │
│  - Coordinates sub-agents              │
└───────────────┬───────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌───────┐   ┌───────┐   ┌───────┐
│ Sub-1 │   │ Sub-2 │   │ Sub-3 │
│ Clean │   │ Clean │   │ Clean │
│Context│   │Context│   │Context│
└───┬───┘   └───┬───┘   └───┬───┘
    │           │           │
    └───────────┴───────────┘
            ▼
    [1-2K token summaries]
```

**Benefits**:
- Each sub-agent starts fresh
- Specialized context per task
- Condensed information flow back to orchestrator

---

## Compaction Strategy

**Goal**: Maximize recall, then improve precision

1. **First Pass**: Preserve everything that might be relevant
2. **Refinement**: Eliminate superfluous content
3. **Keep**: Architectural decisions, critical details
4. **Discard**: Redundant tool outputs, intermediate work

```python
# Example compaction categories
PRESERVE = [
    "architectural decisions",
    "key constraints",
    "success criteria",
    "blocking issues"
]

DISCARD = [
    "verbose tool outputs",
    "intermediate reasoning",
    "redundant explanations",
    "already-resolved issues"
]
```

---

## Application to Sarvaja

### Current Implementation Status

| Pattern | Our Status | Notes |
|---------|------------|-------|
| XML Prompts | DONE | MCP tools use structured prompts |
| Compaction | PARTIAL | DSP has compression but no active rot detection |
| Sub-Agents | PARTIAL | Task delegation exists |
| JIT Loading | PARTIAL | Doc service loads on demand |

### Recommended Actions

1. **Add Active Compaction** - Trigger summaries at context thresholds
2. **Implement Note-Taking** - Persistent task state files
3. **Enhance Sub-Agent Summaries** - Standardize return format
4. **Add Context Metrics** - Track token utilization

---

## Key Quotes

> "Context engineering is the natural progression of prompt engineering."

> "Do the simplest thing that works."

> "Agents are LLMs autonomously using tools in a loop."

---

## Sources

- [Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

---

*Per WORKFLOW-RD-01-v1: R&D Workflow with Human Approval*
