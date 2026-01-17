# GAP-UI-PAGING-001: UI Needs Pagination & Loading States

**Priority:** HIGH | **Category:** ui | **Status:** RESOLVED
**Discovered:** 2026-01-16 | **Session:** SESSION-2026-01-16-PLATFORM-AUDIT

---

## Summary

UI loads all data at once without pagination or proper loading indicators. With 7-9 second API response times, user experience is degraded.

## Evidence

### Current Behavior

| View | Records Loaded | API Time | Loading Indicator |
|------|----------------|----------|-------------------|
| Tasks | 68 (all) | 7.5s | **None visible** |
| Agents | 8 (all) | 9.0s | **None visible** |
| Rules | 50 (all) | 0.7s | None needed |
| Sessions | ? | 1.6s | Unknown |

### Problems

1. **No pagination** - All 68 tasks dumped at once
2. **No skeleton/loader** - User sees empty space for 7+ seconds
3. **No infinite scroll** - Can't handle 1000+ tasks
4. **No total count** - API returns `[]` without metadata

## Impact

- **User thinks app is broken** - 7 seconds of nothing
- **Memory issues** - Loading 1000 tasks would crash browser
- **Poor UX** - No visual feedback during load

## Proposed Fix

### Phase 1: Loading States (Quick Win)
```vue
<!-- Add to each view -->
<v-progress-linear v-if="loading" indeterminate />
<v-skeleton-loader v-if="loading" type="list-item@5" />
```

### Phase 2: API Pagination Metadata
```json
{
  "data": [...],
  "meta": {
    "total": 68,
    "page": 1,
    "per_page": 20,
    "pages": 4
  }
}
```

### Phase 3: UI Pagination
```vue
<v-pagination v-model="page" :length="totalPages" />
```

### Phase 4: Infinite Scroll (Optional)
```vue
<v-infinite-scroll @load="loadMore">
```

## Acceptance Criteria

- [x] Loading spinner visible during API calls (VProgressLinear)
- [x] Skeleton loader for lists (2026-01-16: Tasks, Agents, Sessions views)
- [x] Pagination controls (20 items per page)
- [x] Total count displayed ("68 tasks" not just list)

## Implementation Progress (2026-01-16)

### Phase 1: Loading States - COMPLETE

**Files Modified:**
- `agent/governance_ui/views/tasks/list.py` - Added VSkeletonLoader for 5 placeholder items
- `agent/governance_ui/views/agents/list.py` - Added VSkeletonLoader with avatar placeholders
- `agent/governance_ui/views/sessions/list.py` - Added VSkeletonLoader for timeline items

**Pattern Used:**
```python
# Show skeleton items when is_loading=true, hide content
with v3.VCardText(v_if="is_loading"):
    with v3.VList(density="compact"):
        with v3.VListItem(v_for="n in 5", **{":key": "'skeleton-' + n"}):
            v3.VSkeletonLoader(type="avatar", width=24, height=24)
            v3.VSkeletonLoader(type="text", width="60%")
            v3.VSkeletonLoader(type="chip", width=60, height=20)
```

---

## Resolution (2026-01-17)

### Phase 2: API Pagination - COMPLETE (EPIC-DR-003)

**API Changes:**
- `GET /api/tasks` returns `PaginatedTaskResponse` with `items` + `pagination`
- Query params: `offset`, `limit`, `sort_by`, `order`, `phase`, `status`, `agent_id`
- Location: [governance/routes/tasks/crud.py:34-86](../../../../governance/routes/tasks/crud.py#L34)

### Phase 3: UI Pagination Controls - COMPLETE (EPIC-DR-005)

**Files:**
- `agent/governance_ui/views/tasks/list.py` (lines 247-300) - Pagination UI
- `agent/governance_ui/controllers/tasks.py` (lines 155-229) - Pagination logic
- `agent/governance_ui/state/initial.py` (lines 159-169) - Pagination state

**Features Implemented:**
1. Items per page selector (10, 20, 50, 100)
2. Page navigation (prev/next buttons)
3. Page info display: "Page X of Y (N total)"
4. State: `tasks_page`, `tasks_per_page`, `tasks_pagination`

**Verification:**
- API returns: `{"items": [...], "pagination": {"total": 76, "has_more": true, ...}}`
- UI displays: "Page 1 of 4 (76 total)"

---

*Per GAP-DOC-01-v1: Evidence file for gap documentation*
