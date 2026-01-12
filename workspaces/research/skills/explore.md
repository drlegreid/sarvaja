# Skill: Codebase Exploration

**ID:** SKILL-EXPLORE-001
**Tags:** research, analysis, codebase
**Requires:** Read, Glob, Grep, Task tools

## When to Use

- New codebase analysis
- Finding implementation patterns
- Understanding architecture
- Locating related files for a task

## Procedure

1. **Read Entry Points**
   - Read CLAUDE.md for project context
   - Read TODO.md for current tasks
   - Check docs/ for architecture docs

2. **Find Patterns**
   ```bash
   # Find all Python files
   Glob("**/*.py")

   # Search for specific patterns
   Grep("class.*Handler")
   ```

3. **Trace Flows**
   - Identify entry points (main.py, __init__.py)
   - Follow imports to understand dependencies
   - Map data flow through components

4. **Document Findings**
   - Create architecture diagrams (Mermaid)
   - List key files and their purposes
   - Note patterns and conventions

## Evidence Output

```markdown
## Exploration Summary

### Key Files
| File | Purpose | Lines |
|------|---------|-------|
| governance/mcp_server_core.py | Core MCP tools | 250 |
| agent/governance_dashboard.py | Trame UI | 180 |

### Architecture
- Pattern: MCP server split by domain
- Convention: tools in mcp_tools/, routes in routes/
- Entry: governance_dashboard.py → build_layout()

### Mermaid Diagram
graph TD
    A[Entry] --> B[Component]
```

## Related Skills

- SKILL-ANALYZE-002 (Gap Analysis)
- SKILL-EVIDENCE-003 (Evidence Collection)

---

*Per RULE-024: Context Recovery*
