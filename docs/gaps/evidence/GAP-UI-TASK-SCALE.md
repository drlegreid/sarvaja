# GAP-UI-TASK-SCALE: Task Windows Don't Scale to Fit Main Page

**Priority:** MEDIUM | **Category:** ui/ux | **Status:** OPEN
**Discovered:** 2026-01-20 | **Source:** Session audit

---

## Problem Statement

Multiple UI views use fixed `max-height: 500px` that prevents content from filling available screen space. Users with larger monitors see wasted whitespace.

---

## Affected Files

| File | Line | Current | Issue |
|------|------|---------|-------|
| `tasks/list.py` | 73, 133 | `max-height: 500px` | Fixed height |
| `agents/list.py` | 43, 57 | `max-height: 500px` | Fixed height |
| `sessions/list.py` | 62, 78 | `max-height: 500px` | Fixed height |
| `rules_view.py` | 97 | `max-height: 500px` | Fixed height |
| `decisions/list.py` | 68 | `max-height: 500px` | Fixed height |
| `backlog_view.py` | 68, 182 | `max-height: 400/500px` | Fixed height |
| `monitor_view.py` | 128, 188 | `max-height: 400px` | Fixed height |

**Total:** 13 instances across 7 files

---

## Proposed Solution

Replace fixed heights with viewport-relative heights:

```python
# Before
style="max-height: 500px; overflow-y: auto;"

# After (Option A: viewport-relative)
style="max-height: calc(100vh - 250px); overflow-y: auto;"

# After (Option B: flexbox)
classes="flex-grow-1"
style="overflow-y: auto;"
```

**Trade-offs:**
- Option A: Simple, predictable, works with any layout
- Option B: More flexible, but requires parent container changes

---

## Acceptance Criteria

1. [ ] List views fill available vertical space
2. [ ] Content remains scrollable when overflow
3. [ ] Works on different screen sizes (responsive)
4. [ ] No layout breaks on small screens (<768px)

---

## Scope

- **Files:** 7
- **Changes:** 13 style modifications
- **Complexity:** LOW
- **Risk:** LOW (CSS only, no logic changes)

---

*Per GOV-TRANSP-01-v1: Gap documented with full scope*
