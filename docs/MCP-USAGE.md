# MCP Usage Guide - Sim.ai

**Status:** Active | **Updated:** 2024-12-26

Per RULE-007: MCP Usage Protocol
Per GAP-019: When to use each MCP

---

## Quick Reference

| Need | MCP Tool | When |
|------|----------|------|
| Query rules | `rules_query` | Check rule status, category, priority |
| Create/update rules | `rule_create`, `rule_update` | CRUD operations |
| Trust scores | `agent_trust_score` | Check agent reliability |
| Submit proposals | `proposal_create` | Request governance changes |
| Vote on proposals | `proposal_vote` | Multi-agent consensus |
| View sessions | `sessions_list` | Evidence trail lookup |
| Search evidence | `evidence_search` | Find decision context |
| Task management | `tasks_list` | Backlog operations |
| Agent operations | `agents_list` | Agent registry |

---

## 1. Rules Tools

### rules_query
Query governance rules from TypeDB.

**When to use:**
- Check if a rule applies to current situation
- Find rules by category (governance, technical, operational)
- Filter by status (ACTIVE, DRAFT, DEPRECATED)
- Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)

```python
# Example: Find active governance rules
result = rules_query(category="governance", status="ACTIVE")

# Example: Find critical rules
result = rules_query(priority="CRITICAL")
```

### rule_get
Get detailed information about a specific rule.

**When to use:**
- Need full rule directive and rationale
- Check rule dependencies
- View rule history

```python
# Example: Get rule details
result = rule_get(rule_id="RULE-001")
```

### rule_create / rule_update
CRUD operations for rules.

**When to use:**
- Create new governance policy
- Update existing rule
- Mark rule as deprecated

**Caution:** Requires appropriate trust level.

---

## 2. Trust Tools

### agent_trust_score
Check agent trust score.

**When to use:**
- Before delegating tasks to agent
- After agent reports violations
- Evaluating proposal submitter credibility

```python
# Example: Check agent trust
result = agent_trust_score(agent_id="claude-001")
# Returns: {"trust_score": 0.85, "level": "HIGH", ...}
```

### agent_trust_update
Adjust agent trust based on behavior.

**When to use:**
- Agent completes task successfully (+)
- Agent causes rule violation (-)
- Consensus validation results

**Per RULE-011:** Trust affects voting weight and task eligibility.

---

## 3. Proposal Tools

### proposal_create
Submit governance change proposal.

**When to use:**
- Request new rule creation
- Propose rule modification
- Escalate disputed decision

```python
# Example: Submit rule change
result = proposal_create(
    proposal_type="rule_change",
    rule_id="RULE-005",
    description="Add exception for testing environments",
    rationale="Development velocity requires flexibility"
)
```

### proposal_vote
Vote on pending proposal.

**When to use:**
- Multi-agent consensus required
- Proposal affects your domain
- Escalation review

**Per RULE-011:** Vote weight = trust_score * domain_expertise

### proposals_escalated
Get proposals requiring human review.

**When to use:**
- Critical decision escalation
- Multi-agent deadlock
- Trust score tie-breaker needed

---

## 4. Session & Evidence Tools

### sessions_list
List session evidence files.

**When to use:**
- Find decision context
- Review previous work
- Audit trail lookup

```python
# Example: Find recent sessions
result = sessions_list(limit=10)
```

### evidence_search
Search across all evidence.

**When to use:**
- Find related decisions
- Locate rule application examples
- Context for similar situations

```python
# Example: Search for authentication decisions
result = evidence_search(query="authentication flow")
```

### session_get
Get full session content.

**When to use:**
- Deep dive into specific session
- Extract decision rationale
- Gather evidence for proposal

---

## 5. Task Tools

### tasks_list
List platform tasks.

**When to use:**
- View backlog
- Find available work
- Check task status

### task_create / task_update
Task CRUD operations.

**When to use:**
- Add new work item
- Update task status
- Assign to agent

### REST API Alternative (TODO-6)
For programmatic task operations, use REST API:
- `GET /api/tasks/available` - Available tasks
- `PUT /api/tasks/{id}/claim` - Claim task
- `PUT /api/tasks/{id}/complete` - Complete with evidence

---

## 6. Agent Tools

### agents_list
List registered agents.

**When to use:**
- Find available agents
- Check agent status
- Agent registry audit

### agent_create
Register new agent.

**When to use:**
- New agent joining system
- Agent restart/recovery
- Capability registration

---

## 7. DSM (Deep Sleep Mode) Tools

### dsm_start_cycle / dsm_end_cycle
Track DSP cycles.

**When to use:**
- Starting exploratory DSP session
- Recording DSP findings
- Gap discovery workflow

### dsm_log_finding
Log DSP discovery.

**When to use:**
- Found missing test coverage
- Discovered undocumented behavior
- Identified improvement opportunity

---

## Decision Matrix: Which Tool?

| Scenario | Tool to Use |
|----------|-------------|
| "Is this allowed?" | `rules_query` |
| "What did we decide before?" | `evidence_search` |
| "Should I trust this agent?" | `agent_trust_score` |
| "I want to change a rule" | `proposal_create` |
| "What work is available?" | `tasks_list` or REST `/api/tasks/available` |
| "Record my findings" | `dsm_finding` |

---

## Integration Patterns

### Pattern 1: Rule-Aware Task Execution
```python
# 1. Check applicable rules
rules = rules_query(category="technical")

# 2. Execute task respecting rules
task = claim_task(task_id)
result = execute_with_rules(task, rules)

# 3. Report evidence
complete_task(task_id, evidence=f"Applied rules: {rules}")
```

### Pattern 2: Consensus-Based Decision
```python
# 1. Submit proposal
proposal = proposal_create(...)

# 2. Collect votes
votes = collect_agent_votes(proposal_id)

# 3. Check consensus
if consensus_reached(votes):
    apply_decision(proposal)
else:
    escalate_to_human(proposal)
```

### Pattern 3: Trust-Weighted Task Assignment
```python
# 1. Get agent trust scores
agents = agents_list()
for agent in agents:
    trust = agent_trust_score(agent.id)
    agent.trust = trust["trust_score"]

# 2. Assign to highest trust agent
best_agent = max(agents, key=lambda a: a.trust)
assign_task(task_id, best_agent.id)
```

---

## 8. Cross-Project Queries (claude-mem)

Per GAP-020: Cross-project query patterns for semantic memory.

### chroma_query_documents
Semantic search across memory collections.

**When to use:**
- Find related decisions across projects
- Locate similar implementation patterns
- Search historical context
- Cross-reference governance decisions

```python
# Example: Search for authentication decisions across all projects
result = mcp__claude-mem__chroma_query_documents(
    collection_name="claude_memories",
    query_texts=["sim-ai authentication oauth implementation"],
    n_results=10
)

# Example: Find related governance patterns
result = mcp__claude-mem__chroma_query_documents(
    collection_name="claude_memories",
    query_texts=["sim-ai multi-agent governance voting consensus"],
    n_results=5
)
```

### Cross-Project Search Tips

| Do | Don't |
|----|-------|
| Include project name in query | Use complex where filters |
| Add dates for temporal search | Use $and/$or operators |
| Use semantic intent phrases | Mix timestamp comparisons |
| Search with multiple phrasings | Query without project context |

**Best Practices:**
1. **Project Isolation**: Always prefix queries with project name
   - Good: `["sim-ai TypeDB migration tasks"]`
   - Bad: `["TypeDB migration tasks"]` (may return unrelated projects)

2. **Temporal Search**: Include dates in query text
   - `["sim-ai 2024-12-26 bug fix authentication"]`

3. **Intent-Based Queries**: Use natural language
   - Good: `["implementing oauth flow for user login"]`
   - Bad: `["oauth implementation code function class"]`

4. **Multiple Queries**: Search with variations
   ```python
   queries = [
       "sim-ai authentication middleware",
       "sim-ai API security headers",
       "sim-ai user session management"
   ]
   for q in queries:
       results = chroma_query_documents(query_texts=[q])
   ```

### Cross-Project Integration Pattern
```python
# 1. Search for related patterns in other projects
memories = mcp__claude-mem__chroma_query_documents(
    collection_name="claude_memories",
    query_texts=["governance multi-agent voting"],
    n_results=5
)

# 2. Extract relevant learnings
for memory in memories["documents"]:
    if "consensus" in memory.lower():
        apply_learning(memory)

# 3. Store new learnings back to memory
mcp__claude-mem__chroma_add_documents(
    collection_name="claude_memories",
    documents=["sim-ai: Implemented weighted voting per RULE-011"],
    ids=["sim-ai-voting-2024-12-27"],
    metadatas=[{"project": "sim-ai", "category": "governance"}]
)
```

---

## Related Documentation

- [RULES-GOVERNANCE.md](rules/RULES-GOVERNANCE.md) - Rule definitions
- [RULES-TECHNICAL.md](rules/RULES-TECHNICAL.md) - Technical rules
- [R&D-BACKLOG.md](backlog/R&D-BACKLOG.md) - Strategic roadmap
- [GAP-INDEX.md](gaps/GAP-INDEX.md) - Open gaps

---
*Per RULE-007: Always use MCP tools for governance operations*
