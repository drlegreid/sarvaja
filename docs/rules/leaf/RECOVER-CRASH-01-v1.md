# RECOVER-CRASH-01-v1: Crash Investigation Protocol

**Category:** `stability` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-041
> **Location:** [RULES-STABILITY.md](../operational/RULES-STABILITY.md)
> **Tags:** `crash`, `investigation`, `logs`, `recovery`

---

## Directive

When Claude Code crashes with exit code 1, IMMEDIATELY investigate using log files before resuming work.

---

## Log File Locations

### Linux
```bash
# Claude Code Extension Logs
~/.config/Code/logs/<timestamp>/window1/exthost/Anthropic.claude-code/Claude\ VSCode.log

# VS Code Extension Host
~/.config/Code/logs/<timestamp>/exthost/exthost.log

# Find latest logs
ls -la ~/.config/Code/logs/ | tail -5
```

### Windows
```powershell
# Claude Code Extension Logs
%APPDATA%\Code\logs\<timestamp>\window1\exthost\Anthropic.claude-code\Claude VSCode.log
```

### macOS
```bash
# Claude Code Extension Logs
~/Library/Application\ Support/Code/logs/<timestamp>/window1/exthost/Anthropic.claude-code/Claude\ VSCode.log
```

---

## Investigation Commands

```bash
# Search for errors
grep -i "error\|crash\|exit\|fatal" "/path/to/Claude VSCode.log" | tail -50

# Check MCP failures
grep "MCP server" "Claude VSCode.log" | grep -i "error\|failed"

# Check API errors
grep -i "overloaded\|rate_limit\|timeout" "Claude VSCode.log" | tail -20

# Real-time monitoring
tail -f ~/.config/Code/logs/*/window1/exthost/Anthropic.claude-code/*.log
```

---

## Common Crash Causes

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError` | MCP module missing | Install/fix module |
| `MaxFileReadTokenExceededError` | File too large (>25000 tokens) | Use offset/limit or Grep |
| `overloaded_error` | API overload | Wait and retry |
| `Connection closed` | MCP server died | Restart VS Code |
| `Method not found` | MCP version mismatch | Update MCP server |

---

## Recovery Checklist

After any crash with exit code 1:

1. [ ] Read crash report: `grep -i error ~/.config/Code/logs/*/window1/exthost/Anthropic.claude-code/*.log | tail -20`
2. [ ] Check MCP health: `governance_health()`
3. [ ] Verify claude-mem: `chroma_health()`
4. [ ] Recover context: `chroma_recover_context(project="sim-ai")`
5. [ ] Check TODO.md for last work
6. [ ] Document findings in evidence/

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Resume work without investigating | Check logs first |
| Ignore repeated crashes | Find root cause |
| Skip MCP health check | Verify all servers running |
| Read large files directly | Use Grep or offset/limit |
| Ignore API overload errors | Implement retry with backoff |

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
