# TypeDB Schema Modules

**Created:** 2026-01-17 | **Per:** EPIC-DR-012

## Overview

The monolithic `schema.tql` (705 lines) has been split into domain-specific modules per DOC-SIZE-01-v1 (files ≤300 lines).

## Module Structure

| Prefix | Category | Files |
|--------|----------|-------|
| `01-06` | Entities | Core, Session, Document, Vector, E2E, Agent |
| `10-15` | Attributes | Core, Session, Document, Vector, E2E, Agent |
| `20-25` | Relations | Core, Task, Session, Document, E2E, Agent |
| `30` | Inference | All inference rules |

## Loading Order

Files are loaded in sorted order by filename. The numeric prefix ensures:

1. **01-06**: Entity definitions (depend on attributes)
2. **10-15**: Attribute definitions (no dependencies)
3. **20-25**: Relation definitions (depend on entities)
4. **30**: Inference rules (depend on everything)

## Usage

### Modular Loading (Recommended for Development)

```bash
export USE_MODULAR_SCHEMA=true
python -m governance.loader
```

### Monolithic Loading (Default)

```bash
python -m governance.loader
```

## Module Inventory

| File | Lines | Description |
|------|-------|-------------|
| `01_core_entities.tql` | ~100 | rule-entity, decision, task, gap |
| `02_session_entities.tql` | ~45 | work-session, evidence-file, git-commit |
| `03_document_entities.tql` | ~25 | document |
| `04_vector_entities.tql` | ~50 | vector-document, relations |
| `05_e2e_entities.tql` | ~65 | exploration, test, failure entities |
| `06_agent_entities.tql` | ~45 | agent, proposal |
| `10_core_attributes.tql` | ~75 | Rule, decision, task, gap attributes |
| `11_session_attributes.tql` | ~25 | Session, evidence attributes |
| `12_document_attributes.tql` | ~20 | Document attributes |
| `13_vector_attributes.tql` | ~20 | Vector attributes |
| `14_e2e_attributes.tql` | ~45 | E2E exploration attributes |
| `15_agent_attributes.tql` | ~60 | Agent, proposal, vote, dispute attributes |
| `20_core_relations.tql` | ~40 | rule-dependency, decision-affects, etc. |
| `21_task_relations.tql` | ~50 | Task hierarchy, blocks, gaps |
| `22_session_relations.tql` | ~45 | Entity linkage relations |
| `23_document_relations.tql` | ~30 | Document cross-referencing |
| `24_e2e_relations.tql` | ~25 | E2E exploration relations |
| `25_agent_relations.tql` | ~55 | Multi-agent governance relations |
| `30_inference_rules.tql` | ~90 | All inference rules |

## Backward Compatibility

The original `schema.tql` is preserved and remains the default. Set `USE_MODULAR_SCHEMA=true` to use modules.

## Related

- EPIC-DR-012: Split TypeDB schema into modules
- DOC-SIZE-01-v1: Files ≤300 lines
- DECISION-003: TypeDB-First Strategy
