# Shell Command Guide - Sim.ai

> **Parent:** [CLAUDE.md](../CLAUDE.md) | **Rule:** RULE-035
> **Last Updated:** 2026-01-04

---

## Environment Selection (CRITICAL)

> ⚠️ The Bash tool runs in LINUX, not Windows. Never mix environments.

| Environment | Tool | Runs In | Use For |
|-------------|------|---------|---------|
| **Linux Bash** | Built-in `Bash` tool | Linux/Container | Docker, curl, git, sleep, head, tail |
| **Windows PowerShell** | `mcp__powershell__run_powershell` | Windows host | Invoke-WebRequest, Get-ChildItem, Start-Sleep |

---

## Command Mapping

| Task | Bash Tool (Linux) | PowerShell MCP (Windows) |
|------|-------------------|--------------------------|
| Wait 5 seconds | `sleep 5` | `Start-Sleep -Seconds 5` |
| HTTP request | `curl http://...` | `Invoke-WebRequest -Uri "http://..."` |
| First N lines | `head -n 20` | `Select-Object -First 20` |
| Last N lines | `tail -n 30` | `Select-Object -Last 30` |
| List files | `ls -la` | `Get-ChildItem` |
| Run pytest | `python3 -m pytest ... \| tail -30` | `python -m pytest ... \| Select-Object -Last 30` |
| Docker commands | `docker compose up -d` | Same (Docker CLI works in both) |

---

## Examples

### Bash Tool (Linux)
```bash
docker exec sim-ai-typedb-1 curl -s http://localhost:8082/api/health
sleep 5 && curl http://localhost:8082/api/agents | head -c 500
```

### PowerShell MCP (Windows)
```powershell
mcp__powershell__run_powershell(code="Get-Process | Select-Object -First 10")
mcp__powershell__run_powershell(code="Invoke-WebRequest -Uri 'http://localhost:8082/api/health'")
```

---

## Common Pitfalls

| Wrong | Correct |
|-------|---------|
| ❌ `Start-Sleep` in Bash | ✅ Use `sleep 5` instead |
| ❌ `Select-Object` in Bash | ✅ Use `head -n 20` instead |
| ❌ `Invoke-WebRequest` in Bash | ✅ Use `curl` instead |
| ❌ `$variable` in Bash | ✅ Use `${variable}` or escape as `\$variable` |
| ❌ `python script.py` in Bash | ✅ Use `python3 script.py` (per GAP-PYTHON-001) |

---

*Per RULE-035: Shell Command Environment Selection*
