# RD-DOCUMENT-MCP-SERVICE: Dedicated Document MCP Investigation

**Status:** INVESTIGATION | **Priority:** MEDIUM | **Created:** 2026-01-20
**Linked EPIC:** EPIC-CLEANUP-001 | **Requested by:** User

---

## Executive Summary

Analysis of whether a dedicated `gov-docs` MCP server would solve current issues related to document handling in the Sarvaja platform.

---

## Current State

### Document Tools Location
Currently in `gov-sessions` MCP server (governance/mcp_tools/evidence/documents*.py):

| Tool | Purpose |
|------|---------|
| `doc_get` | Get document content with pagination |
| `docs_list` | List documents in directory |
| `doc_rule_get` | Get rule markdown document |
| `doc_task_get` | Get task from workspace docs |
| `doc_links_extract` | Extract links from document |
| `doc_link_resolve` | Resolve relative link to path |

### MCP Server Architecture
```
claude-mem    → Semantic memory (ChromaDB)
gov-core      → Rules CRUD, quality, conflicts
gov-agents    → Trust, proposals, voting
gov-sessions  → Sessions, DSM, decisions, **DOCUMENTS**  ← Coupling issue
gov-tasks     → Tasks, gaps, workspace sync
```

---

## Problems Identified

### P1: Coupling
Document operations are coupled with session operations in gov-sessions, violating separation of concerns.

### P2: Tool Discovery
23+ tools in gov-sessions makes document tools hard to find/remember.

### P3: Inconsistent Access
- Claude Code uses Read tool directly for files
- MCP tools use doc_get for files
- No unified interface

### P4: No Caching
Frequently accessed documents (CLAUDE.md, TODO.md) read repeatedly without caching.

### P5: Link Validation
Document links can become stale; no automated validation pipeline.

---

## Proposed Solution: gov-docs MCP

### Architecture
```
gov-docs (NEW)
├── doc_get          → Cached document access
├── docs_list        → Directory listing
├── doc_rule_get     → Rule documents
├── doc_task_get     → Task documents
├── doc_validate     → Validate all links in a document
├── doc_render       → Render markdown to TOON/text
└── doc_cache_stats  → Cache hit/miss metrics
```

### Benefits

| Benefit | Impact |
|---------|--------|
| **Separation** | Clean boundary between documents and sessions |
| **Caching** | LRU cache for hot documents (~30% token savings) |
| **Validation** | Automated stale link detection |
| **Metrics** | Visibility into document access patterns |
| **Render** | TOON output format for all documents |

### Implementation Effort

| Task | Effort |
|------|--------|
| Create mcp_server_docs.py | LOW |
| Move document tools from gov-sessions | MEDIUM |
| Add LRU caching layer | LOW |
| Add link validation | MEDIUM |
| Update .mcp.json | LOW |
| Update CLAUDE.md references | LOW |

**Total:** ~4-6 hours focused work

---

## Alternative: Keep in gov-sessions

### Pros
- No migration effort
- Works today
- One less MCP server to maintain

### Cons
- Continued coupling
- Tool discoverability issues persist
- No caching improvements

---

## Recommendation

**DEFER until gov-sessions becomes unwieldy (>30 tools).**

Current state is functional. The coupling is architectural debt but not blocking.

**Revisit when:**
1. gov-sessions exceeds 30 tools
2. Document caching becomes critical for performance
3. Link validation becomes a recurring manual task

---

## Quick Wins (No New MCP)

Can implement without new MCP server:

| Improvement | Effort | Impact |
|-------------|--------|--------|
| Add doc_cache to gov-sessions | LOW | Caching benefit |
| Add doc_validate tool | LOW | Link validation |
| Improve doc_get TOON output | DONE | Consistency |

---

*Per RD-DOC-SERVICE task reference*
*Per user request: "i have a feeling document MCP service will solve lots of current issues"*
