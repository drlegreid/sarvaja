# P2-9: Entity Model Audit + Design

**Date**: 2026-03-19
**Status**: DESIGN (Phase 1 — no code changes)
**Goal**: Full entity graph: Project → Workspace → Agent → Capabilities → Tasks → Sessions

---

## 1. Entity Graph (Current State)

```
                          ┌─────────────────────────────────────────────────────────────────┐
                          │                     TypeDB Entity Graph                         │
                          └─────────────────────────────────────────────────────────────────┘

    ┌─────────┐     project-has-workspace    ┌──────────┐    workspace-has-agent    ┌─────────┐
    │ PROJECT │─────────────────────────────▶│WORKSPACE │───────────────────────────▶│  AGENT  │
    └────┬────┘                              └──────────┘                           └────┬────┘
         │                                                                               │
         │ project-has-session                                       agent-capability     │
         │                                                    (agent→rule binding)        │
         ▼                                                                               ▼
    ┌──────────┐    completed-in    ┌──────┐    implements-rule    ┌─────────────┐
    │ SESSION  │◀──────────────────│ TASK │───────────────────────▶│ RULE-ENTITY │
    └────┬────┘                    └──┬───┘                        └──────┬──────┘
         │                            │                                   │
         │ has-evidence               │ evidence-supports                 │ decision-affects
         │ session-applied-rule       │ task-commit                       │ rule-dependency
         │ session-decision           │ references-gap                    │ rule-conflict
         ▼                            │ task-hierarchy                    ▼
    ┌──────────┐                      │ task-blocks-task           ┌──────────┐
    │ EVIDENCE │                      │ task-related               │ DECISION │
    └──────────┘                      ▼                            └──────────┘
                                 ┌─────────┐
                                 │   GAP   │
                                 └─────────┘

    ╔═══════════════════════════════════════════════════════════════════════╗
    ║  MISSING FROM 3x SCHEMA (exists in legacy schema.tql only):        ║
    ║                                                                     ║
    ║  PROJECT ──project-contains-plan──▶ PLAN                           ║
    ║  PLAN ──plan-contains-epic──▶ EPIC                                 ║
    ║  EPIC ──epic-contains-task──▶ TASK                                 ║
    ╚═══════════════════════════════════════════════════════════════════════╝

    ┌────────────────────────────────────────────────────────────────────┐
    │  SUPPORTING ENTITIES (fully in 3x schema):                        │
    │  document, vector-document, proposal, git-commit                  │
    │  exploration-session, exploration-step, test-case, test-failure   │
    └────────────────────────────────────────────────────────────────────┘
```

---

## 2. Audit Results: Schema ↔ Query Layer ↔ Service Layer

### 2.1 Fully Integrated (Schema + Queries + Service + API)

| Entity | Schema (3x) | TypeDB Queries | Service | API Routes | Persistence |
|--------|:-----------:|:--------------:|:-------:|:----------:|:-----------:|
| rule-entity | Y | Y (crud, read, archive, inference, decisions) | Y | Y | TypeDB primary |
| task | Y | Y (crud, read, details, linking, relationships, status) | Y | Y | TypeDB + memory |
| work-session | Y | Y (crud, mutations, read, linking) | Y | Y | TypeDB + memory |
| decision | Y | Y (via rules/decisions.py) | Y | Y | TypeDB |
| agent | Y | Y (agents.py) | Y | Y | TypeDB + memory |
| gap | Y | Y (via rule inference) | Partial | Partial | TypeDB |
| project | Y | Y (crud.py, linking.py) | Y | Y | TypeDB + memory |
| git-commit | Y | Y (via task linking) | Y | Via task API | TypeDB |
| evidence-file | Y | Y (via session linking) | Y | Via session API | TypeDB + filesystem |
| document | Y | Y (via task linking) | Y | Via task API | TypeDB |

### 2.2 Schema Defined, NO Query Layer (Critical Gap)

| Entity/Relation | Schema (3x) | TypeDB Queries | Service | API Routes | Current Persistence |
|----------------|:-----------:|:--------------:|:-------:|:----------:|:-------------------:|
| **workspace** | Y (07/16/26) | **NO** | Y | Y | **JSON file only** |
| **agent-capability** | Y (26) | **NO** | Y | Y | **In-memory only** |
| **workspace-has-agent** | Y (26) | **NO** | Y | Y | **JSON file only** |
| **project-has-workspace** | Y (26) | **NO** | N | N | **Not wired** |

### 2.3 In Legacy Schema, MISSING from 3x Schema (Critical Gap)

| Entity/Relation | Legacy schema.tql | Schema 3x | TypeDB Queries | Notes |
|----------------|:-----------------:|:---------:|:--------------:|:-----:|
| **plan** entity | Y (line 149) | **NO** | Referenced in linking.py | Queries will FAIL without schema |
| **epic** entity | Y (line 157) | **NO** | Referenced in linking.py | Queries will FAIL without schema |
| **project-contains-plan** | Y (line 582) | **NO** | Used in linking.py | Relation undefined in 3x |
| **plan-contains-epic** | Y (line 587) | **NO** | Used in linking.py | Relation undefined in 3x |
| **epic-contains-task** | Y (line 592) | **NO** | Used in linking.py | Relation undefined in 3x |
| plan-id, plan-name attrs | Y (line 368-369) | **NO** | — | — |
| epic-id, epic-name attrs | Y (line 370-371) | **NO** | — | — |

### 2.4 In Legacy Schema, MISSING from 3x Entity Roles

| Entity | Missing Role | Defined In |
|--------|-------------|------------|
| **work-session** | `plays project-has-session:project-session` | 26_workspace_relations has the relation but 02_session_entities doesn't play it |
| **agent** | `plays workspace-has-agent:assigned-agent` | 26_workspace_relations has the relation but 06_agent_entities doesn't play it |
| **agent** | `plays agent-capability:capable-agent` | 26_workspace_relations has the relation but 06_agent_entities doesn't play it |
| **rule-entity** | `plays agent-capability:governing-rule` | 26_workspace_relations has the relation but 01_core_entities doesn't play it |
| **task** | `plays epic-contains-task:epic-task` | Legacy schema.tql has it, not in 3x |
| **project** | `plays project-contains-plan:parent-project` | Legacy schema.tql has it (as `owning-project` in 3x differs from `parent-project` in legacy) |

### 2.5 CC Session Attributes (Legacy→3x Gap)

These attributes exist in legacy `schema.tql` and were applied via `scripts/migrate_cc_attributes.py` but are NOT in the modularized 3x schema files:

| Attribute | In schema.tql | In 3x files | In migrate script |
|-----------|:------------:|:-----------:|:-----------------:|
| cc-session-uuid | Y | **NO** | Y |
| cc-project-slug | Y | **NO** | Y |
| cc-git-branch | Y | **NO** | Y |
| cc-tool-count | Y | **NO** | Y |
| cc-thinking-chars | Y | **NO** | Y |
| cc-compaction-count | Y | **NO** | Y |

**Impact**: The live TypeDB database HAS these attributes (applied via migration), but the 3x schema files don't document them. A fresh schema load from 3x files would lose them.

---

## 3. Design: Missing Schema Additions

All additions use TypeDB 3.x syntax per project conventions.

### 3.1 New File: `08_hierarchy_entities_3x.tql` — Plan + Epic Entities

```typeql
# Project Hierarchy Entities (Plan → Epic chain)
# Completes: Project → Plan → Epic → Task
# Migrated from legacy schema.tql
# Part of: P2-9 Entity Model Completion
# Created: 2026-03-19

define

# =============================================================================
# PLAN ENTITY — a planned body of work within a project
# =============================================================================

entity plan,

    owns plan-id,
    owns plan-name,
    owns plan-description,
    plays project-contains-plan:child-plan,
    plays plan-contains-epic:parent-plan;

# =============================================================================
# EPIC ENTITY — a large feature/initiative within a plan
# =============================================================================

entity epic,

    owns epic-id,
    owns epic-name,
    owns epic-description,
    plays plan-contains-epic:child-epic,
    plays epic-contains-task:parent-epic;
```

### 3.2 New File: `17_hierarchy_attributes_3x.tql` — Plan + Epic Attributes

```typeql
# Project Hierarchy Attributes
# Part of: P2-9 Entity Model Completion
# Created: 2026-03-19

define

# Plan attributes
attribute plan-id value string;
attribute plan-name value string;
attribute plan-description value string;

# Epic attributes
attribute epic-id value string;
attribute epic-name value string;
attribute epic-description value string;
```

### 3.3 New File: `27_hierarchy_relations_3x.tql` — Hierarchy Relations

```typeql
# Project Hierarchy Relations
# Completes: Project → Plan → Epic → Task chain
# Part of: P2-9 Entity Model Completion
# Created: 2026-03-19

define

# =============================================================================
# PROJECT → PLAN RELATION
# =============================================================================

relation project-contains-plan,
    relates parent-project,
    relates child-plan;

# =============================================================================
# PLAN → EPIC RELATION
# =============================================================================

relation plan-contains-epic,
    relates parent-plan,
    relates child-epic;

# =============================================================================
# EPIC → TASK RELATION
# =============================================================================

relation epic-contains-task,
    relates parent-epic,
    relates epic-task;
```

### 3.4 Updated: `11_session_attributes_3x.tql` — Add CC Attributes

```typeql
# ADD to existing file (after evidence attributes):

# Claude Code session attributes (SESSION-CC-01-v1)
# Applied live via scripts/migrate_cc_attributes.py
attribute cc-session-uuid value string;
attribute cc-project-slug value string;
attribute cc-git-branch value string;
attribute cc-tool-count value integer;
attribute cc-thinking-chars value integer;
attribute cc-compaction-count value integer;
```

### 3.5 Updated Entity Role Additions

**`02_session_entities_3x.tql`** — work-session needs:
```typeql
    # ADD these roles:
    owns cc-session-uuid,
    owns cc-project-slug,
    owns cc-git-branch,
    owns cc-tool-count,
    owns cc-thinking-chars,
    owns cc-compaction-count,
    plays project-has-session:project-session;
```

**`06_agent_entities_3x.tql`** — agent needs:
```typeql
    # ADD these roles:
    plays workspace-has-agent:assigned-agent,
    plays agent-capability:capable-agent;
```

**`01_core_entities_3x.tql`** — rule-entity needs:
```typeql
    # ADD this role:
    plays agent-capability:governing-rule;
```

**`01_core_entities_3x.tql`** — task needs:
```typeql
    # ADD this role:
    plays epic-contains-task:epic-task;
```

**`07_workspace_entities_3x.tql`** — project needs:
```typeql
    # ADD this role:
    plays project-contains-plan:parent-project;
```

---

## 4. Design: Missing TypeDB Query Modules

### 4.1 `governance/typedb/queries/workspaces/crud.py`

Methods needed (mirroring JSON service layer):
- `insert_workspace(workspace_id, name, workspace_type, project_id?, description?, status?)`
- `get_workspace(workspace_id) → dict`
- `list_workspaces(project_id?, workspace_type?, limit?, offset?) → list[dict]`
- `update_workspace(workspace_id, name?, description?, status?)`
- `delete_workspace(workspace_id) → bool`

### 4.2 `governance/typedb/queries/workspaces/linking.py`

Methods needed:
- `assign_agent_to_workspace(workspace_id, agent_id) → bool`
- `remove_agent_from_workspace(workspace_id, agent_id) → bool`
- `get_workspace_agents(workspace_id) → list[str]`
- `get_agent_workspaces(agent_id) → list[str]`
- `link_workspace_to_project(workspace_id, project_id) → bool`

### 4.3 `governance/typedb/queries/capabilities/crud.py`

Methods needed:
- `bind_rule_to_agent(agent_id, rule_id, category?, status?) → bool`
- `unbind_rule_from_agent(agent_id, rule_id) → bool`
- `get_capabilities_for_agent(agent_id) → list[dict]`
- `get_agents_for_rule(rule_id) → list[dict]`
- `list_capabilities(agent_id?, rule_id?, category?, status?) → list[dict]`
- `update_capability_status(agent_id, rule_id, status) → bool`

---

## 5. Migration Plan

### Phase A: Schema Alignment (Session 1, ~2h)

| Step | Action | Risk | Rollback |
|------|--------|------|----------|
| A1 | Create `08_hierarchy_entities_3x.tql` | None (new file) | Delete file |
| A2 | Create `17_hierarchy_attributes_3x.tql` | None (new file) | Delete file |
| A3 | Create `27_hierarchy_relations_3x.tql` | None (new file) | Delete file |
| A4 | Add CC attributes to `11_session_attributes_3x.tql` | None (additive) | Revert edit |
| A5 | Add CC owns to `02_session_entities_3x.tql` + project-session role | None (additive) | Revert edit |
| A6 | Add workspace/capability roles to `06_agent_entities_3x.tql` | None (additive) | Revert edit |
| A7 | Add capability role to `01_core_entities_3x.tql` (rule-entity + task) | None (additive) | Revert edit |
| A8 | Add plan role to `07_workspace_entities_3x.tql` (project) | None (additive) | Revert edit |
| A9 | Create migration script `scripts/migrate_entity_model.py` | None | Delete file |
| A10 | Run migration against live TypeDB | **MEDIUM** — new entities | Backup first |
| A11 | Unit tests for schema validation | None | — |

**Validation**: `health_check()` shows no errors + schema can load fresh from 3x files.

### Phase B: TypeDB Query Modules (Session 2, ~3h)

| Step | Action | Risk |
|------|--------|------|
| B1 | Create `governance/typedb/queries/workspaces/__init__.py` | None |
| B2 | Create `governance/typedb/queries/workspaces/crud.py` | None |
| B3 | Create `governance/typedb/queries/workspaces/linking.py` | None |
| B4 | Create `governance/typedb/queries/capabilities/__init__.py` | None |
| B5 | Create `governance/typedb/queries/capabilities/crud.py` | None |
| B6 | Add `WorkspaceQueries` + `CapabilityQueries` to `client.py` mixin chain | Low |
| B7 | Unit tests for all new query methods | None |

**Validation**: All new query methods work against live TypeDB with test data.

### Phase C: Service Layer Integration (Session 3, ~3h)

| Step | Action | Risk |
|------|--------|------|
| C1 | Wire `workspaces.py` service to TypeDB (keep JSON as fallback) | Medium |
| C2 | Wire `capabilities.py` service to TypeDB (keep in-memory as fallback) | Medium |
| C3 | Add workspace→project linking in project service | Low |
| C4 | Update existing unit tests for dual persistence | Medium |
| C5 | Integration tests: API → service → TypeDB round-trip | None |

**Validation**: Full CRUD via API persists to TypeDB. Container restart preserves data.

### Phase D: Entity Graph Traversal + E2E (Session 4, ~2h)

| Step | Action | Risk |
|------|--------|------|
| D1 | Add API endpoint: `GET /api/entity-graph/{entity_id}` for traversal | None |
| D2 | Test full chain: Project→Workspace→Agent→Capabilities→Tasks→Sessions | None |
| D3 | E2E: Dashboard navigation through entity chain | Low |
| D4 | Container restart + verify persistence | None |

**Acceptance**: Can traverse the full entity graph via API:
```
GET /api/projects/PROJ-SARVAJA → workspaces: [WS-001]
GET /api/workspaces/WS-001 → agents: [code-agent, ...]
GET /api/agents/code-agent/capabilities → rules: [TEST-GUARD-01, ...]
GET /api/tasks?agent_id=code-agent → tasks: [...]
GET /api/sessions?agent_id=code-agent → sessions: [...]
```

---

## 6. Dependency Order

```
Phase A (schema)
    │
    ├──▶ Phase B (query modules) ──▶ Phase C (service wiring) ──▶ Phase D (E2E)
    │
    └──▶ [P2-11: Workspace UI] depends on Phase C
         [P2-12: Capabilities Service] depends on Phase C
```

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| TypeDB schema migration breaks existing data | LOW | HIGH | Backup TypeDB before migration; all changes are additive |
| Dual persistence (TypeDB + fallback) causes inconsistency | MEDIUM | MEDIUM | Fallback reads merge with TypeDB; write-through pattern |
| Plan/epic queries fail (no schema loaded) | **CONFIRMED** | LOW | Not actively called from any service layer currently |
| Capability data lost on restart | **CONFIRMED** | MEDIUM | Phase C fixes this — TypeDB persistence |
| Workspace data diverges from TypeDB | LOW | LOW | Phase C adds write-through; JSON becomes cache |

---

## 8. Current Data Inventory

From MCP health check (2026-03-18):
- **Projects**: 2 in TypeDB (PROJ-sarvaja-platform, PROJ-buntu-ger)
- **Workspaces**: 2 in JSON (Sarvaja Platform Dev, Job Hunt 2026), 0 in TypeDB
- **Agents**: 9 in TypeDB (5 default + 4 test)
- **Capabilities**: ~20 bindings in memory, 0 in TypeDB
- **Tasks**: 720 in TypeDB
- **Sessions**: 100+ in TypeDB
- **Rules**: 91 in TypeDB (86 active)
- **Plans**: 0 in TypeDB (entity doesn't exist in loaded 3x schema)
- **Epics**: 0 in TypeDB (entity doesn't exist in loaded 3x schema)

---

## 9. Files to Create/Modify

### New Files (6)
1. `governance/schema_3x/08_hierarchy_entities_3x.tql`
2. `governance/schema_3x/17_hierarchy_attributes_3x.tql`
3. `governance/schema_3x/27_hierarchy_relations_3x.tql`
4. `governance/typedb/queries/workspaces/crud.py`
5. `governance/typedb/queries/workspaces/linking.py`
6. `governance/typedb/queries/capabilities/crud.py`

### Modified Files (7)
1. `governance/schema_3x/01_core_entities_3x.tql` — add capability + epic roles
2. `governance/schema_3x/02_session_entities_3x.tql` — add CC attributes + project-session role
3. `governance/schema_3x/06_agent_entities_3x.tql` — add workspace + capability roles
4. `governance/schema_3x/07_workspace_entities_3x.tql` — add plan role to project
5. `governance/schema_3x/11_session_attributes_3x.tql` — add CC attribute definitions
6. `governance/client.py` — add WorkspaceQueries + CapabilityQueries to mixin chain
7. `scripts/load-schema.sh` — add new .tql files to load order

### Service Layer Changes (Phase C, 2 files)
1. `governance/services/workspaces.py` — wire to TypeDB
2. `governance/services/capabilities.py` — wire to TypeDB
