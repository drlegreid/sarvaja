# TASK-SEARCH-01-v1: Server-Side Task Search

| Field | Value |
|-------|-------|
| **Category** | Technical |
| **Priority** | MEDIUM |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-21 |

## Directive

Task search MUST be server-side and MUST support attribute-prefix structured syntax.

## Requirements

### 1. Server-Side Execution
- Search queries are sent to the API as a `search` query parameter
- API applies search BEFORE pagination (correct total count)
- Client-side page-local filtering is FORBIDDEN for search

### 2. Search Scope
- Free-text search matches across: task_id, description, summary, body, gap_id
- Case-insensitive substring matching

### 3. Structured Prefix Syntax
- Format: `key:value freetext`
- Supported prefixes: `type:`, `priority:`, `status:`, `phase:`, `agent:`
- Example: `type:bug priority:HIGH authentication`
- Prefixes are extracted, remaining text used as free-text query
- `_parse_structured_search()` extracts key:value pairs

### 4. Pagination Interaction
- `pagination.total` reflects post-search count (not total task count)
- Changing search resets to page 1

## Anti-Patterns
- Client-side filtering that only searches the current page
- Search that ignores pagination totals
- Hardcoded field lists that miss new attributes

## Rationale

Phase 9d discovered that client-side search only filtered the current page of results, giving users the false impression that matching tasks don't exist.

## Related Rules
- TASK-SUMMARY-01-v1 (summary is a searchable field)
- TASK-NAV-01-v1 (search results must be navigable)
