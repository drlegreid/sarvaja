# GOV-PROJECT-01-v1: Project Hierarchy Organization

| Field | Value |
|-------|-------|
| **Rule ID** | GOV-PROJECT-01-v1 |
| **Category** | governance |
| **Priority** | HIGH |
| **Status** | ACTIVE |

## Statement

All work MUST be organized under a project entity. Projects contain plans, plans contain EPICs, and EPICs contain tasks.

## Rationale

Without project-level organization, sessions and tasks lack business context. The project hierarchy enables portfolio-level reporting, cross-cutting impact analysis, and workstream prioritization.

## Implementation

- TypeDB schema defines `project`, `plan`, `epic` entities with containment relations
- `governance/services/projects.py` provides CRUD + hierarchy navigation
- `governance/routes/projects/crud.py` exposes REST endpoints
- Dashboard "Projects" nav item enables drill-down navigation

## Verification

- `GET /api/projects` returns project list with plan/session counts
- `GET /api/projects/{id}` returns project with linked sessions
- Unit tests in `tests/unit/test_project_service.py`
