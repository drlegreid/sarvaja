# R&D: Frankel Hash Evidence System (FH-001 to FH-008)

**Status:** ✅ CORE TESTS PASSING (16)
**Priority:** HIGH/MEDIUM
**Vision:** Digital twin evidence world with holographic navigation
**Updated:** 2026-01-14

---

## Test Coverage (2026-01-14)

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `tests/test_frankel_hash.py` | 16 | Content hashing, chunk hashing, Merkle trees, state capture |

**Core Implementation:** `governance/frankel_hash.py`
- `compute_hash()` - SHA-256 content hashing
- `compute_chunk_hashes()` - Multi-level chunk hashing (document, section, paragraph, line)
- `build_merkle_tree()` - Merkle tree construction with proof support
- `has_changed()` - State change detection
- `capture_workspace_state()` - Workspace snapshot with root hash
- `compare_states()` - State difference detection
- `compute_short_hash()` - Dashboard display (8-char uppercase)

---

## Task List

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| FH-001 | CLI zoom in/out on hash changes | ✅ CORE | HIGH | `compute_chunk_hashes()` implemented with levels 0-3 |
| FH-002 | Hash tree visualization (ASCII/terminal) | ✅ CORE | HIGH | `build_merkle_tree()` returns tree levels |
| FH-003 | 5D visualization framework | 📋 TODO | MEDIUM | Lighting + 3D + deformation mapping |
| FH-004 | Holographic mapping of evidence world | 📋 TODO | MEDIUM | Digital twin navigation for LLM + human |
| FH-005 | Game theory for hash convergence | 📋 TODO | FUTURE | Group theory, equilibria, stability |
| FH-006 | Sync R&D tasks with GitHub issues | ✅ DONE | HIGH | governance/github_sync.py + 18 tests |
| FH-007 | Dashboard hash display on refresh | ✅ CORE | HIGH | `compute_short_hash()` - 8-char uppercase for display |
| FH-008 | Test coverage effectiveness assessment | ✅ TDD | MEDIUM | 16 tests covering all core functions per TDD approach |

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

- **Core Module:** `governance/frankel_hash.py` - TDD implementation (2026-01-14)
- **Test Suite:** `tests/test_frankel_hash.py` - 16 tests passing
- GitHub sync: governance/github_sync.py (18 tests)
- RULE-022: Evidence-based wisdom extension

*Per RULE-012 DSP: Frankel Hash R&D documented*
*Per RULE-004: TDD approach with executable specification*
