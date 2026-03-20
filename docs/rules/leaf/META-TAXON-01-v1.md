# META-TAXON-01-v1: Rule Taxonomy & Management

**Category:** `meta` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** META

> **Location:** [RULES-GOVERNANCE.md](../RULES-GOVERNANCE.md)
> **Tags:** `meta`, `taxonomy`, `rule-management`, `versioning`, `governance`

---

## Directive

All governance rules MUST follow the semantic rule ID taxonomy defined in this document. Rule IDs MUST be meaningful, hierarchical, and versioned to enable clear categorization, dependency tracking, and evolution over time.

## Rule ID Format

```
{DOMAIN}-{SUB}-{NN}-v{N}
```

| Component | Description | Example |
|-----------|-------------|---------|
| `DOMAIN` | Primary category (3-10 chars) | `SESSION`, `GOV`, `ARCH` |
| `SUB` | Sub-category (3-6 chars) | `EVID`, `TRUST`, `MCP` |
| `NN` | Sequential number (01-99) | `01`, `02`, `15` |
| `v{N}` | Version number | `v1`, `v2` |

## Domain Registry

| Domain | Description | Sub-categories |
|--------|-------------|----------------|
| `SESSION` | Session management | `EVID` (evidence), `DSM` (deep sleep) |
| `REPORT` | Reporting & decisions | `DEC` (decisions), `LOG` (logging) |
| `GOV` | Governance & trust | `TRUST` (trust scoring), `BICAM` (bicameral), `PROP` (proposals), `RULE` (rule ops) |
| `META` | Meta-rules about rules | `TAXON` (taxonomy), `STRUCT` (structure) |
| `ARCH` | Architecture | `BEST` (best practices), `INFRA` (infrastructure), `MCP` (MCP patterns) |
| `WORKFLOW` | Workflow & autonomy | `AUTO` (autonomy), `SEQ` (sequencing), `RD` (R&D approval) |
| `RECOVER` | Recovery & resilience | `AMNES` (amnesia), `CRASH` (crash), `MEM` (memory) |
| `TEST` | Testing & validation | `FIX` (fix validation), `COMP` (comprehensive), `GUARD` (guardrails) |
| `SAFETY` | Safety & prevention | `DESTR` (destructive prevention), `HEALTH` (healthcheck), `INTEG` (integrity) |
| `CONTAINER` | Container operations | `SHELL` (shell selection), `DEV` (dev workflow), `RESTART` (restart protocol) |
| `DOC` | Documentation | `LINK` (linking), `SIZE` (file size), `PARTIAL` (partial tasks) |
| `UI` | User interface | `TRAME` (trame patterns) |
| `IDE` | IDE integrations | `VSCODE` (VS Code), `CC` (Claude Code) |

## Versioning Rules

1. **v1**: Initial version of a rule
2. **v{N+1}**: Increment when directive changes materially
3. **DEPRECATED**: Old versions marked deprecated, not deleted
4. **Alias**: Old ID (RULE-XXX) remains as alias in TypeDB

## Migration from Legacy IDs

Legacy `RULE-XXX` IDs are aliased to new semantic IDs:

```typescript
// TypeDB alias relation
rule-alias sub relation,
    relates legacy-id,
    relates semantic-id;
```

## Rule Lifecycle

```
PROPOSED → DRAFT → ACTIVE → DEPRECATED
    ↓                          ↓
  [rejected]              [archived]
```

## Anti-Patterns

| Pattern | Why It's Wrong |
|---------|----------------|
| `RULE-999` | Generic, non-semantic ID |
| `SESSION-01` | Missing sub-category and version |
| `SESSION-EVID-01` | Missing version suffix |
| `SESSION-EVIDENCE-01-v1` | Sub-category too long (max 6 chars) |

## Validation

- [ ] Rule ID matches format `{DOMAIN}-{SUB}-{NN}-v{N}`
- [ ] Domain exists in registry
- [ ] Sub-category is 3-6 characters
- [ ] Version starts at v1
- [ ] Legacy alias maintained if migrated

---

*Per META-TAXON-01-v1: Rule Taxonomy & Management*
