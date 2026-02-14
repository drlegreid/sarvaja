---
description: Rapid rule creation with semantic ID guidance
allowed-tools: mcp__gov-core__rule_create, mcp__gov-core__rules_query, Read, Write
---

# Rapid Rule Creation

Create a governance rule with semantic ID and leaf document.

## Steps

1. Ask user for:
   - **Domain**: SESSION, REPORT, GOV, ARCH, UI, WORKFLOW, TEST, SAFETY, CONTAINER, DOC, RECOVER, META, COMM, DATA
   - **Subdomain**: Short identifier (e.g., EVID, GUARD, MCP, LINK)
   - **Directive**: What the rule mandates (required)
   - **Category**: governance / technical / operational
   - **Priority**: CRITICAL / HIGH / MEDIUM / LOW

2. Generate semantic ID: `{DOMAIN}-{SUB}-{NN}-v1`
   - Query existing rules to find next available NN for domain-sub prefix
   - e.g., if TEST-FIX-01-v1 exists, next is TEST-FIX-02-v1

3. Call `rule_create` with:
   - `rule_id`: Generated semantic ID
   - `name`: Short descriptive name
   - `directive`: User's directive text
   - `category`: Selected category
   - `priority`: Selected priority
   - `status`: "ACTIVE"

4. Create leaf document at `docs/rules/leaf/{RULE-ID}.md`:
   ```markdown
   # {RULE-ID}: {Name}

   | Field | Value |
   |-------|-------|
   | **Category** | {category} |
   | **Priority** | {priority} |
   | **Status** | ACTIVE |
   | **Created** | {today} |

   ## Directive

   {directive text}

   ## Rationale

   {brief rationale}
   ```

5. Report the created rule ID and leaf doc path.
