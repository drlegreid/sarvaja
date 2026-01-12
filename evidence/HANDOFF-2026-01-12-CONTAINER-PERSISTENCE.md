# Handoff: Container Persistence Fix

**Date:** 2026-01-12
**Session:** Container persistence and claude-mem MCP fix
**Status:** READY FOR USER TESTING

---

## Summary

Fixed three critical issues:
1. **GAP-PERSIST-001**: Containers lost on reboot
2. **claude-mem MCP failure**: Module not found in container
3. **Healthcheck visibility**: Added "SERVICES STARTING" status

---

## Changes Made

### 1. docker-compose.yml
Added `restart: unless-stopped` to all services:
- litellm
- ollama
- chromadb
- typedb
- agents
- governance-dashboard-dev

### 2. Rootless Podman Linger
```bash
loginctl enable-linger $(whoami)
```
This allows containers to persist when user logs out.

### 3. Dockerfile.mcp
Added claude_mem module to container image:
```dockerfile
COPY claude_mem/ ./claude_mem/
```

### 4. scripts/mcp-runner.sh
Added volume mount for claude_mem:
```bash
-v "$PROJECT_DIR/claude_mem:/app/claude_mem:ro"
```

### 5. Healthcheck Enhancement
Added "SERVICES STARTING" status detection and clear messaging.

---

## User Testing Instructions

### Test 1: Reboot Persistence
1. Reboot workstation
2. After login, check containers:
   ```bash
   podman ps
   ```
3. **Expected**: TypeDB, ChromaDB containers should be running automatically

### Test 2: Service Health Check
1. Open VS Code with Claude Code extension
2. Run `/health` command
3. **Expected**: All services show OK status

### Test 3: claude-mem MCP
1. In Claude Code, try to use a claude-mem tool:
   ```
   mcp__claude-mem__chroma_query_documents(["sim-ai 2026-01 infrastructure"])
   ```
2. **Expected**: Should return results without ModuleNotFoundError

---

## Verification Checklist

- [ ] After reboot, `podman ps` shows containers running
- [ ] `/health` shows all services OK
- [ ] claude-mem MCP tools work
- [ ] No "ModuleNotFoundError: No module named 'claude_mem'" in logs

---

## Rollback (if needed)

If issues occur:
```bash
# Disable linger (containers stop on logout)
loginctl disable-linger $(whoami)

# Restore old docker-compose.yml
git checkout docker-compose.yml
```

---

## Related

- **Gaps Resolved:** GAP-PERSIST-001
- **Gaps Created:** GAP-DESTRUCT-001, GAP-VERIFY-001
- **Documentation Updated:** docs/DEVOPS.md
- **Evidence:** evidence/SESSION-2026-01-11-AMNESIA-ROOT-CAUSE.md

---

*Per RULE-001: Session Evidence Logging*
*Per RULE-037: Fix Validation Protocol*
