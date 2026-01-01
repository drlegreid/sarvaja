# R&D: Frankel Hash Evidence System (FH-001 to FH-008)

**Status:** PARTIAL
**Priority:** HIGH/MEDIUM
**Vision:** Digital twin evidence world with holographic navigation

---

## Task List

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| FH-001 | CLI zoom in/out on hash changes | 📋 TODO | HIGH | Navigate document changes at chunk level |
| FH-002 | Hash tree visualization (ASCII/terminal) | 📋 TODO | HIGH | Merkle tree depth navigation |
| FH-003 | 5D visualization framework | 📋 TODO | MEDIUM | Lighting + 3D + deformation mapping |
| FH-004 | Holographic mapping of evidence world | 📋 TODO | MEDIUM | Digital twin navigation for LLM + human |
| FH-005 | Game theory for hash convergence | 📋 TODO | FUTURE | Group theory, equilibria, stability |
| FH-006 | Sync R&D tasks with GitHub issues | ✅ DONE | HIGH | governance/github_sync.py + 18 tests |
| FH-007 | Dashboard hash display on refresh | 📋 TODO | HIGH | Show Frankel hash change on each refresh |
| FH-008 | Test coverage effectiveness assessment | 📋 TODO | MEDIUM | Assess test quality, coverage, correctness gaps |

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│              Frankel Hash Evidence Navigation                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Layer 1: CHUNK HASHING (Core)                                          │
│  └── Document → Chunks → Similarity hash → Merkle tree                  │
│                                                                          │
│  Layer 2: CLI NAVIGATION (FH-001, FH-002)                               │
│  └── Terminal UI with zoom levels (document → section → paragraph)      │
│                                                                          │
│  Layer 3: 5D VISUALIZATION (FH-003)                                     │
│  └── X/Y/Z: Spatial, Lighting: Change intensity, Deformation: Stability│
│                                                                          │
│  Layer 4: HOLOGRAPHIC TWIN (FH-004)                                     │
│  └── Map all session evidence to hash-space, LLM navigation             │
│                                                                          │
│  Layer 5: THEORY LAYER (FH-005)                                         │
│  └── Group theory, game theory, topology                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## TypeDB Integration

```typeql
define
  frankel-hash sub entity,
    owns hash-id,
    owns hash-value,
    owns chunk-level,      # 0=document, 1=section, 2=paragraph, N=line
    owns created-at,
    plays parent-child:parent,
    plays parent-child:child,
    plays document-hash:hash;

  parent-child sub relation,
    relates parent,
    relates child;

  document-hash sub relation,
    relates document,
    relates hash;
```

---

## Zoom Levels

| Level | Granularity | Use Case |
|-------|-------------|----------|
| 0 | Document root hash | Quick integrity check |
| 1 | Section hashes | Identify changed sections |
| 2 | Paragraph hashes | Locate specific changes |
| N | Line-level | Maximum detail for debugging |

---

## Evidence

- GitHub sync: governance/github_sync.py (18 tests)
- RULE-022: Evidence-based wisdom extension

*Per RULE-012 DSP: Frankel Hash R&D documented*
