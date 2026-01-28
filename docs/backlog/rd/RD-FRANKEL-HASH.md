# R&D: Frankel Hash Evidence System (FH-001 to FH-008)

**Status:** ✅ CORE COMPLETE - CLI, visualization, and tests implemented
**Priority:** HIGH/MEDIUM
**Vision:** Digital twin evidence world with holographic navigation
**Updated:** 2026-01-25

---

## Test Coverage (2026-01-25)

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `tests/test_frankel_hash.py` | 27 | Content hashing, Merkle trees, ASCII viz, zoom view |

**Core Implementation:** `governance/frankel_hash.py`
- `compute_hash()` - SHA-256 content hashing ✅
- `compute_chunk_hashes()` - Multi-level chunk hashing (levels 0-3) ✅
- `build_merkle_tree()` - Merkle tree construction ✅
- `has_changed()` - State change detection ✅
- `capture_workspace_state()` - Workspace snapshot with root hash ✅
- `compare_states()` - State difference detection ✅
- `compute_short_hash()` - 8-char uppercase hash ✅
- `compute_state_hash()` - Dict state hashing (FH-DUP-001 consolidation) ✅
- `render_merkle_tree()` - ASCII tree visualization (FH-002) ✅
- `render_file_tree()` - File tree with change markers ✅
- `zoom_view()` - Zoom level view (FH-001) ✅
- `interactive_tree_cli()` - Interactive CLI navigation (FH-001) ✅

**Issues Resolved (2026-01-25):**
- ✅ **FH-DUP-001 FIXED:** Hooks now import from governance module
- ✅ **FH-001 IMPLEMENTED:** Interactive CLI with zoom levels 0-3
- ✅ **FH-002 IMPLEMENTED:** ASCII Merkle tree rendering

---

## Task List

| ID | Task | Status | Priority | Notes |
|----|------|--------|----------|-------|
| FH-001 | CLI zoom in/out on hash changes | ✅ DONE | HIGH | `zoom_view()`, `interactive_tree_cli()`, 5 tests |
| FH-002 | Hash tree visualization (ASCII/terminal) | ✅ DONE | HIGH | `render_merkle_tree()`, `render_file_tree()`, 6 tests |
| FH-003 | 5D visualization framework | 📐 DESIGNED | MEDIUM | Roadmap documented, 3 phases planned |
| FH-004 | Holographic mapping of evidence world | 📐 DESIGNED | MEDIUM | Concept + API draft documented |
| FH-005 | Game theory for hash convergence | 📋 FUTURE | LOW | Group theory, equilibria, stability |
| FH-006 | Sync R&D tasks with GitHub issues | ✅ DONE | HIGH | governance/github_sync.py + 18 tests |
| FH-007 | Dashboard hash display on refresh | ✅ DONE | HIGH | Hooks import from governance (FH-DUP-001 fixed) |
| FH-008 | Test coverage effectiveness assessment | ✅ DONE | MEDIUM | 27 tests cover core + CLI features |

### GAP: Code Duplication (FH-DUP-001) - RESOLVED

~~Two implementations exist:~~
✅ **FIXED 2026-01-25:** `.claude/hooks/core/state.py` now imports from `governance/frankel_hash.py`

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│              Frankel Hash Evidence Navigation                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Layer 1: CHUNK HASHING (Core) ✅ IMPLEMENTED                           │
│  └── Document → Chunks → Merkle tree                                    │
│      governance/frankel_hash.py (27 tests)                              │
│                                                                          │
│  Layer 2: CLI NAVIGATION (FH-001, FH-002) ✅ IMPLEMENTED                │
│  └── Terminal UI with zoom levels, ASCII tree rendering                 │
│      Commands: tree, zoom, nav (interactive)                            │
│                                                                          │
│  Layer 3: 5D VISUALIZATION (FH-003) 📋 TODO                             │
│  └── X/Y/Z: Spatial, Lighting: Change intensity, Deformation: Stability│
│                                                                          │
│  Layer 4: HOLOGRAPHIC TWIN (FH-004) 📋 TODO                             │
│  └── Map all session evidence to hash-space, LLM navigation             │
│                                                                          │
│  Layer 5: THEORY LAYER (FH-005) 📋 FUTURE                               │
│  └── Group theory, game theory, topology                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## FH-003: 5D Visualization Roadmap (MEDIUM)

**Vision:** Transform hash-space into navigable 5D visualization for evidence exploration.

### Dimensions

| Dimension | Mapping | Implementation |
|-----------|---------|----------------|
| X | File/entity position | Graph layout algorithm |
| Y | Hierarchy depth | Merkle tree level |
| Z | Time (commit history) | Git log timestamps |
| Lighting | Change intensity | Hash delta magnitude |
| Deformation | Stability score | Frequency of changes |

### Implementation Phases

1. **Phase 1: 2D Grid View** (Prerequisite)
   - File grid with color-coded hash changes
   - Click to zoom into file details
   - Technology: Textual TUI or Trame web UI

2. **Phase 2: 3D Scatter**
   - X/Y/Z positioning of entities
   - Color = hash state (green=stable, red=changed)
   - Technology: Three.js or Plotly 3D

3. **Phase 3: Lighting + Deformation**
   - Intensity maps change frequency
   - Shape distortion shows instability
   - Technology: WebGL shaders

### Dependencies
- FH-001/002 (✅ Complete)
- Trame UI framework (existing in project)

---

## FH-004: Holographic Evidence Twin (MEDIUM)

**Vision:** Create a "digital twin" of the evidence world that both LLMs and humans can navigate.

### Concept

```
Evidence World → Hash Space → Holographic Map
     ↓              ↓              ↓
  Documents    Merkle Trees    3D Navigation
  Sessions     State Diffs     Time Travel
  Decisions    Comparisons     Impact Viz
```

### Features

1. **Semantic Clustering**
   - Group related evidence by embedding similarity
   - ChromaDB vector proximity → 3D cluster position

2. **Time Navigation**
   - Scrub through git history
   - Watch hash-space evolve over time
   - Identify stability patterns

3. **LLM Integration**
   - Natural language queries: "Show me what changed yesterday"
   - Guided navigation via MCP tools
   - Automatic focus on high-entropy regions

### API Design (Draft)

```python
# governance/holographic.py (Future)
def create_evidence_snapshot() -> HolographicState:
    """Capture current state as 3D-navigable structure."""

def navigate_to(entity_id: str) -> FocusView:
    """Zoom to specific entity in hash-space."""

def time_travel(commit_hash: str) -> HolographicState:
    """Reconstruct hash-space at historical point."""
```

### Dependencies
- FH-003 (5D framework)
- ChromaDB (for embeddings)
- TypeDB (for relationships)

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

## CLI Usage

```bash
# View ASCII Merkle tree
python3 governance/frankel_hash.py tree TODO.md 1

# View zoom at level 2 (paragraphs)
python3 governance/frankel_hash.py zoom CLAUDE.md 2

# Interactive navigation
python3 governance/frankel_hash.py nav TODO.md
```

---

## Evidence

- **Core Module:** `governance/frankel_hash.py` - TDD implementation (2026-01-14, CLI 2026-01-25)
- **Test Suite:** `tests/test_frankel_hash.py` - 27 tests passing
- GitHub sync: governance/github_sync.py (18 tests)
- RULE-022: Evidence-based wisdom extension

*Per RULE-012 DSP: Frankel Hash R&D documented*
*Per RULE-004: TDD approach with executable specification*
