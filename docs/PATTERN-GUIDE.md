# Sarvaja Platform — Pattern Guide

> Per P3-14: Unified Patterns Audit. Documents the canonical patterns
> for service, route, and controller code. Follow these when adding new
> domains or modifying existing ones.

## Service Layer (`governance/services/`)

### Error Handling

**Canonical pattern** — catch all, log sanitized, fall back to in-memory:
```python
client = get_typedb_client()
if client:
    try:
        result = client.operation(...)
    except Exception as e:
        logger.warning(f"TypeDB op failed: {type(e).__name__}", exc_info=True)
# Fallback to in-memory store
```

**Rules**: Always use `{type(e).__name__}` (never raw `{e}`). Always add `exc_info=True`.

**Exception — Rules service**: Uses fail-fast `_get_client_or_raise()` → `ConnectionError`.
This is intentional: rules are governance-critical and must not silently degrade.

### TypeDB Client Import

**Canonical import**:
```python
from governance.stores import get_typedb_client    # Sessions, Tasks, Agents
from governance.stores.config import get_typedb_client  # Capabilities
```

**Known variant** (rules, projects):
```python
from governance.client import get_client  # Direct client import
```

Future: consolidate on `governance.stores.get_typedb_client()` for all services.

### Response Format

**Service layer returns `Dict[str, Any]`** — routes convert to Pydantic models.

| Service | Returns | Notes |
|---------|---------|-------|
| sessions | `SessionResponse` (Pydantic) | Legacy — via `session_to_response()` |
| tasks | `TaskResponse` (Pydantic) | Legacy — via `task_to_response()` |
| rules | `Dict` | Canonical |
| agents | `Dict` | Canonical |
| workspaces | `Dict` | Canonical |
| capabilities | `Dict` | Canonical |
| projects | `Dict` | Canonical |

**Route responsibility**: `WorkspaceResponse(**ws)` etc.

### Audit + Monitoring

Every mutation (CREATE/UPDATE/DELETE) **must** call both:
```python
record_audit("CREATE", "entity_type", entity_id, metadata={...})
_monitor("create", entity_id, source=source)
```

### Persistence Strategy

| Strategy | Used By | Description |
|----------|---------|-------------|
| TypeDB-first + memory fallback | Sessions, Tasks, Agents, Projects | Try TypeDB, fall back silently |
| TypeDB-only (fail fast) | Rules | `ConnectionError` if unavailable |
| Memory-first + disk JSON | Workspaces | `_workspaces_store` + `workspaces.json` |
| Memory-first + TypeDB best-effort | Capabilities | Fire-and-forget persistence |

---

## Route Layer (`governance/routes/`)

### HTTP Methods

| Operation | Method | Status Code |
|-----------|--------|-------------|
| List | GET | 200 |
| Create | POST | 201 |
| Get One | GET | 200 |
| Update | PUT | 200 |
| Delete | DELETE | 204 (empty body) |
| Link | POST | 200 |
| Unlink | DELETE | 200 (returns updated parent) |

### Pagination

**Canonical pattern** — offset/limit with PaginationMeta:
```python
offset: int = Query(0, ge=0)
limit: int = Query(50, ge=1, le=200)
```

Response:
```json
{"items": [...], "pagination": {"total": N, "offset": 0, "limit": 50, "has_more": false, "returned": N}}
```

**Exception**: Workspaces and Capabilities return raw `list[T]` (small datasets).

### Error Handling

```python
try:
    result = service.operation(...)
except ValueError:
    raise HTTPException(status_code=409, detail="Conflict")
except ConnectionError:
    raise HTTPException(status_code=503, detail="Database unavailable")
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Failed: {type(e).__name__}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")
```

### Sort/Filter Injection Prevention

Whitelist sort keys explicitly:
```python
_VALID_SORT = {"id", "name", "status", "created_at"}
if sort_by not in _VALID_SORT:
    raise HTTPException(status_code=422, detail=f"Invalid sort_by")
```

---

## Controller Layer (`agent/governance_ui/controllers/`)

### State Naming

```
state.selected_{entity}           # Currently selected entity
state.show_{entity}_detail        # Detail view visible
state.show_{entity}_form          # Form visible
state.{entity}_form_mode          # "create" or "edit" (string enum)
state.form_{entity}_{field}       # Form field values
```

### Trigger Naming

```
select_{entity}                   # Open detail from list
close_{entity}_detail             # Close detail
open_{entity}_form                # Open create/edit form
create_{entity}                   # POST new entity
edit_{entity}                     # Enter edit mode
delete_{entity}                   # DELETE entity
load_{entity}s                    # Load list from API
{entity}_apply_filters            # Apply filter changes
{entity}_prev_page / _next_page   # Pagination
```

### API Call Pattern

```python
with httpx.Client(timeout=10.0) as client:
    response = client.get(f"{api_base_url}/api/{endpoint}")
    if response.status_code in (200, 201):
        state.selected_entity = response.json()
    else:
        state.has_error = True
        state.error_message = f"API Error: {response.status_code}"
```

---

## Known Deviations (Accepted)

1. **Sessions/Tasks return Pydantic from service** — legacy, works via `_ensure_response()`
2. **Rules fail fast on TypeDB** — intentional, governance-critical
3. **Edit mode boolean vs string** — Tasks use `edit_task_mode = True/False` (boolean),
   Rules/Sessions use `{entity}_form_mode = "create"/"edit"` (string enum).
   New code should use the string enum pattern.

---

*Created: 2026-03-20 per P3-14*
