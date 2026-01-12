# AMNESIA Recovery Document - 2026-01-02

**Purpose**: Assist Claude Code in recovering context after workstation restart.
**Created**: 2026-01-02 19:15 UTC
**Status**: PRE-RESTART CHECKPOINT

---

## Quick Context Recovery

### 1. Run Healthcheck First
```
/health
```
Or manually:
```python
mcp__governance__governance_health()
```
**Expected**: `status: healthy`, TypeDB 32 rules, ChromaDB OK

### 2. Restore Memory Context
```python
mcp__claude-mem__chroma_query_documents(
    collection_name="claude_memories",
    query_texts=["sim-ai 2026-01-02 session GAP UI work"],
    n_results=5
)
```

### 3. Check GAP-INDEX for Current State
Read: `docs/gaps/GAP-INDEX.md`
- **Current**: 82 RESOLVED, 8 PARTIAL, 104 OPEN

---

## Session Context Before Restart

### Work Completed This Session (2026-01-02)

| GAP | Description | Status |
|-----|-------------|--------|
| GAP-UI-005 | Loading states for list views | RESOLVED |
| GAP-UI-009 | Search functionality implementation | RESOLVED |
| GAP-UI-036 | Scrolling for list views | RESOLVED |
| GAP-UI-035 | Datetime columns in lists | RESOLVED |

### Commits Made This Session
- `c20b1ea` - GAP-UI-005: Add loading states to all list views
- `10c6817` - GAP-UI-009: Implement evidence search functionality
- `0d12118` - GAP-UI-036: Add scrolling to all list views
- `f74bc16` - GAP-UI-035: Add datetime columns to all list views

### Files Modified
- `agent/governance_ui/views/rules_view.py`
- `agent/governance_ui/views/sessions/list.py`
- `agent/governance_ui/views/tasks/list.py`
- `agent/governance_ui/views/decisions/list.py`
- `agent/governance_ui/views/agents/list.py`
- `agent/governance_ui/views/search_view.py`
- `agent/governance_ui/controllers/search.py` (NEW)
- `agent/governance_ui/controllers/__init__.py`
- `docs/gaps/GAP-INDEX.md`

---

## MCP Server Configuration

### Active Servers (Project Level)
From `.mcp.json`:
- **governance**: TypeDB MCP server (port 1729)

### Active Servers (Global Level)
From `~/.claude.json`:
- **claude-mem**: ChromaDB memory (port 8001)
- **sequential-thinking**: Reasoning chains
- **git**: Git operations
- **powershell**: Windows shell
- **llm-sandbox**: Python execution
- **playwright**: Browser automation (for UI testing)

### If MCP Servers Not Responding
```powershell
# Check Docker containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Start services if down
.\deploy.ps1 -Action up -Profile cpu

# Or directly:
docker compose --profile cpu up -d typedb chromadb
```

---

## Config Backup Locations

| Config | Backup Path |
|--------|-------------|
| Global Claude | `C:\Users\natik\.claude.json.backup-2026-01-02` |
| Project MCP | `.mcp.json.backup-2026-01-02` |
| Local Settings | `.claude\settings.local.json.backup-2026-01-02` |

### Restore Commands
```powershell
# If configs corrupted, restore from backup:
Copy-Item "C:\Users\natik\.claude.json.backup-2026-01-02" "C:\Users\natik\.claude.json" -Force
Copy-Item ".mcp.json.backup-2026-01-02" ".mcp.json" -Force
```

---

## AMNESIA Detection Signs

If you see these indicators, AMNESIA has occurred:

1. **No memory of today's work** - Query claude-mem returns 0 results for today
2. **GAP counts don't match** - Should be 82 RESOLVED, not 64 or lower
3. **Missing file changes** - Check git status for uncommitted changes
4. **TypeDB rules count wrong** - Should be 32 rules, 29 active

### Recovery Steps if AMNESIA Detected

1. **Read this document first** (you're doing it!)
2. **Run healthcheck**: `/health`
3. **Query claude-mem**:
   ```python
   mcp__claude-mem__chroma_query_documents(
       collection_name="claude_memories",
       query_texts=["sim-ai session 2026-01-02"],
       n_results=10
   )
   ```
4. **Read CLAUDE.md** for project context
5. **Check git log for recent commits**:
   ```bash
   git log --oneline -10
   ```
6. **Read GAP-INDEX.md** for current backlog

---

## Key Project Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project instructions and rules |
| `TODO.md` | Current sprint tasks |
| `docs/gaps/GAP-INDEX.md` | Gap tracking (182 total) |
| `docs/RULES-DIRECTIVES.md` | Rule index |
| `.claude/hooks/healthcheck.py` | Healthcheck hook |

---

## Governance Rules to Remember

- **RULE-001**: Session Evidence Logging (CRITICAL)
- **RULE-007**: MCP Usage Protocol (HIGH)
- **RULE-012**: Deep Sleep Protocol - files <300 lines (HIGH)
- **RULE-021**: MCP Healthcheck Protocol (CRITICAL)
- **RULE-024**: AMNESIA Protocol (CRITICAL)

---

## User's Last Requests

1. Prepare AMNESIA recovery document (this file)
2. Backup configs before restart
3. Verify healthcheck works
4. Check Playwright MCP availability for UI testing

**Note**: UI changes were verified with unit tests, not browser tests.
Playwright MCP IS configured globally but wasn't used this session.

---

## Next Steps After Recovery

1. Verify healthcheck passes
2. Run Playwright tests on UI changes if needed
3. Continue with remaining CRITICAL gaps:
   - GAP-DATA-001: Tasks have no descriptions
   - GAP-UI-CHAT-001: Platform UI no prompt/chat
   - GAP-UI-CHAT-002: No agent interaction UI

---

*Document created per RULE-024 (AMNESIA Protocol)*
