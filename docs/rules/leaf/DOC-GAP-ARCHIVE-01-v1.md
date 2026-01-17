# DOC-GAP-ARCHIVE-01-v1: Gap Index Archive Structure

**Category:** `documentation` | **Priority:** MEDIUM | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Task ID:** DOC-GAP-ARCHIVE-001
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `documentation`, `gaps`, `archive`, `maintenance`

---

## Directive

GAP-INDEX.md MUST contain only active gaps (OPEN, BLOCKED, PARTIAL, DEFERRED). RESOLVED gaps MUST be moved to GAP-INDEX-ARCHIVE.md to maintain index readability.

---

## File Structure

```
docs/gaps/
├── GAP-INDEX.md          # Active gaps only (<100 entries)
├── GAP-INDEX-ARCHIVE.md  # RESOLVED gaps (historical)
└── evidence/             # Detailed gap analysis files
```

---

## Status Routing

| Status | Location | Action |
|--------|----------|--------|
| OPEN | GAP-INDEX.md | Active work |
| BLOCKED | GAP-INDEX.md | Waiting on dependency |
| PARTIAL | GAP-INDEX.md | Partially complete |
| DEFERRED | GAP-INDEX.md | Postponed with reason |
| RESOLVED | GAP-INDEX-ARCHIVE.md | Move after resolution |
| NOT_IMPLEMENTED | GAP-INDEX-ARCHIVE.md | Closed without implementation |

---

## Archive Process

When marking a gap RESOLVED:

1. **Update status** in GAP-INDEX.md to RESOLVED with fix summary
2. **Copy entry** to GAP-INDEX-ARCHIVE.md under appropriate section
3. **Remove from** GAP-INDEX.md (defer to batch cleanup)
4. **Update counts** in header of both files

---

## Header Format

### GAP-INDEX.md
```markdown
# Gap Index - Sarvaja (Active Gaps)

**Last Updated:** YYYY-MM-DD
**Active Gaps:** N | Status: X OPEN, Y BLOCKED, Z PARTIAL, W DEFERRED
**Archived:** M RESOLVED gaps → [GAP-INDEX-ARCHIVE.md](GAP-INDEX-ARCHIVE.md)
```

### GAP-INDEX-ARCHIVE.md
```markdown
# Gap Index Archive - Sarvaja

**Archived:** YYYY-MM-DD
**Total Resolved:** N gaps
**Active Gaps:** See [GAP-INDEX.md](GAP-INDEX.md)
```

---

## Batch Cleanup

Quarterly or when active index exceeds 100 entries:
1. Run archive script or manual cleanup
2. Move all RESOLVED entries to archive
3. Update headers with accurate counts
4. Commit: "chore: Q{N} gap archive cleanup"

---

## Validation

- [ ] GAP-INDEX.md has <100 active entries
- [ ] No RESOLVED entries in active index (or pending batch cleanup)
- [ ] Archive has all historical RESOLVED gaps
- [ ] Headers have accurate counts

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
*Per DOC-SIZE-01-v1: Keep files manageable size*
