# Claude Code Crash Report
**Date:** 2026-01-11
**Error:** `Claude Code process exited with code 1`
**Status:** ANALYZED

---

## 1. Crash Timeline

| Time | Event | Severity |
|------|-------|----------|
| 21:10:57 | MCP server "playwright" exited cleanly | INFO |
| 21:10:58 | **CRASH** - Exit code 1 (channel 4ify5lebrxt) | CRITICAL |
| 21:15:05 | claude-mem MCP: ModuleNotFoundError | HIGH |
| 21:15:10 | claude-vscode: Method not found | MEDIUM |
| 21:41:39 | MaxFileReadTokenExceededError (73998 tokens) | HIGH |
| 21:41:50 | MaxFileReadTokenExceededError (81069 tokens) | HIGH |
| 21:44:29 | MCP servers exited (playwright, podman, rest-api) | INFO |
| 21:44:29 | **CRASH** - Exit code 1 (channel 1n0aidzve66) | CRITICAL |
| 22:02:30 | claude-mem MCP: Connection failed | HIGH |
| 22:03:15 | API overloaded_error (fallback to non-streaming) | MEDIUM |

---

## 2. Root Cause Analysis

### Primary Causes

1. **MCP Server Failures (claude-mem)**
   ```
   ModuleNotFoundError: No module named 'claude_mem'
   MCP error -32000: Connection closed
   ```
   - **Impact:** MCP chain broken, fallback memory unavailable
   - **Resolution:** Implemented claude_mem/mcp_server.py (2026-01-11)

2. **Large File Reads Exceeding Token Limits**
   ```
   MaxFileReadTokenExceededError: File content (73998 tokens)
   exceeds maximum allowed tokens (25000)
   ```
   - **Impact:** Read tool failures, potential context overflow
   - **Resolution:** Use offset/limit parameters or Grep tool

3. **API Overload**
   ```
   overloaded_error: Overloaded
   ```
   - **Impact:** Streaming fallback, potential timeouts
   - **Resolution:** Retry with backoff, reduce request frequency

### Secondary Causes

4. **claude-vscode Method Not Found**
   - `MCP error -32601: Method not found`
   - Low impact, likely incompatible MCP version

5. **Tool Registration Warnings**
   - `Tool already exists: governance_health`
   - Non-fatal, indicates duplicate registration

---

## 3. Prevention Advice

### Immediate Actions

| Action | Priority | Status |
|--------|----------|--------|
| Fix claude-mem MCP module | CRITICAL | DONE |
| Avoid reading files >25000 tokens | HIGH | Use Grep/offset |
| Handle API overload gracefully | MEDIUM | Retry logic |

### Best Practices

1. **Before Reading Large Files:**
   ```
   # Check file size first
   wc -l <file>
   # If >500 lines, use offset/limit or Grep
   ```

2. **MCP Health Check:**
   ```python
   # Call at session start
   governance_health()  # Check all MCP servers
   chroma_health()      # Check claude-mem
   ```

3. **Save Context Before Risky Operations:**
   ```python
   chroma_save_session_context(
       session_id="SESSION-2026-01-11-WORK",
       summary="Current progress...",
       ...
   )
   ```

---

## 4. Log File Locations

### Claude Code Logs (VS Code Extension)

```bash
# Location (Linux)
~/.config/Code/logs/<timestamp>/window1/exthost/Anthropic.claude-code/Claude\ VSCode.log

# Latest log directory
ls -la ~/.config/Code/logs/ | tail -5

# Search for errors
grep -i "error\|crash\|exit" "/path/to/Claude VSCode.log" | tail -50

# Real-time monitoring
tail -f ~/.config/Code/logs/*/window1/exthost/Anthropic.claude-code/*.log
```

### VS Code Extension Host Logs

```bash
# Location (Linux)
~/.config/Code/logs/<timestamp>/exthost/exthost.log

# Check for extension crashes
grep -i "crash\|error\|SIGTERM" ~/.config/Code/logs/*/exthost/*.log
```

### MCP Server Logs (in Claude VSCode.log)

```bash
# Filter MCP errors
grep "MCP server" "Claude VSCode.log" | grep -i error

# Check specific server
grep "governance-core\|claude-mem" "Claude VSCode.log"
```

### Output Panel (VS Code UI)

1. Open VS Code
2. View > Output (Ctrl+Shift+U)
3. Select "Claude Code" from dropdown
4. Scroll to see recent activity

---

## 5. Investigation Checklist

When Claude Code crashes with exit code 1:

- [ ] Check Claude VSCode.log for last error before crash
- [ ] Look for MCP server failures (`ModuleNotFoundError`, `Connection closed`)
- [ ] Check for token limit errors (`MaxFileReadTokenExceededError`)
- [ ] Check for API errors (`overloaded_error`, `rate_limit`)
- [ ] Verify all MCP servers are running (`governance_health()`)
- [ ] Check file sizes before reading large files
- [ ] Review recent operations for memory-intensive tasks

---

## 6. Recovery Steps

After a crash:

1. **Check Logs:**
   ```bash
   grep -i "error\|crash" ~/.config/Code/logs/*/window1/exthost/Anthropic.claude-code/*.log | tail -20
   ```

2. **Restart MCP Servers:**
   - Close and reopen VS Code, OR
   - Run `governance_health()` to trigger reconnection

3. **Recover Context:**
   ```python
   chroma_recover_context(project="sim-ai", n_results=3)
   ```

4. **Check TODO.md for last work:**
   - Read TODO.md
   - Check evidence/ for recent session files

---

*Per RULE-024: AMNESIA Protocol*
*Per RULE-021: MCP Healthcheck Protocol*
