# WORKFLOW-SFDC-01-v1: SFDC Development Lifecycle Workflow

**Category:** `workflow` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `sfdc`, `salesforce`, `deployment`, `langgraph`, `workflow`

---

## Directive

Salesforce development lifecycle MUST follow the governed workflow: DISCOVER → DEVELOP → TEST → REVIEW → DEPLOY → VALIDATE → MONITOR → REPORT. Deployments to production require sandbox_only=False override and explicit approval.

---

## Workflow Phases

| Phase | Purpose | Exit Criteria |
|-------|---------|---------------|
| DISCOVER | Scan org metadata, map dependencies | Components inventoried |
| DEVELOP | Create/modify Apex, LWC, Flows | Components ready for test |
| TEST | Run Apex tests, validate coverage | Coverage >= 75% |
| REVIEW | Security scan, code review | No CRITICAL findings |
| DEPLOY | Push to target org | Deployment succeeded |
| VALIDATE | Post-deploy checks | All checks pass |
| MONITOR | Production monitoring | No alerts |
| REPORT | Generate deployment summary | Report generated |

---

## Conditional Routing

| Condition | Route |
|-----------|-------|
| Breaking changes >= 10 | DISCOVER → skip_to_report |
| Test coverage < 75% (retries < 3) | TEST → loop_to_develop |
| Security scan failed (retries < 3) | REVIEW → loop_to_develop |
| Deployment failed | DEPLOY → rollback → report |
| Validation failed | VALIDATE → rollback → report |

---

## Safety Constraints

| Constraint | Value | Rationale |
|------------|-------|-----------|
| `sandbox_only` | `True` (default) | Prevent accidental production deploys |
| `MIN_CODE_COVERAGE` | 75% | Salesforce platform minimum |
| `MAX_DEPLOY_RETRIES` | 3 | Prevent infinite loops |
| `MAX_COMPONENTS_PER_DEPLOY` | 500 | Large deploys are risky |
| `BREAKING_CHANGE_THRESHOLD` | 10 | Skip if too many deletions |

---

## Implementation Reference

- **State**: `governance/sfdc/langgraph/state.py` (SFDCState TypedDict)
- **Graph**: `governance/sfdc/langgraph/graph.py` (build_sfdc_graph, run_sfdc_workflow)
- **Edges**: `governance/sfdc/langgraph/edges.py` (conditional routing)
- **Nodes**: `governance/sfdc/langgraph/nodes_*.py` (phase implementations)
- **Tests**: `tests/unit/test_sfdc_langgraph.py` (49 tests)

---

## Related

- WORKFLOW-DSP-01-v1: DSP Workflow (same LangGraph pattern)
- UI-TRAME-01-v1: Cross-workspace pattern reuse
- TEST-GUARD-01-v1: Test coverage requirements

---

*Per META-TAXON-01-v1: Semantic rule naming*
*Created: 2026-02-09 — SFDC workflow using LangGraph approach*
