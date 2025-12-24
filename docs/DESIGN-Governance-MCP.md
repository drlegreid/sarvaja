# DESIGN: Governance MCP - Multi-Agent Conflict Resolution

**Status:** DRAFT
**Date:** 2024-12-24
**Related:** DECISION-005 (pending), RULE-011 (pending)

---

## Problem Statement

```
LOCAL (Claude Code)              SERVER (Docker Agents)
┌─────────────────┐              ┌─────────────────┐
│ R&D Agent       │              │ Production Agent│
│ - Rule creation │    SYNC?     │ - Task execution│
│ - Complex tasks │ <─────────>  │ - Rule application│
│ - Evidence gen  │   CONFLICT?  │ - Inference     │
└─────────────────┘              └─────────────────┘
         │                                │
         └────────── TypeDB ──────────────┘
                (Source of Truth)
```

**Challenges:**
1. Bidirectional sync without conflicts
2. Consensus when agents disagree
3. Trust scoring for agent reliability
4. Evidence-based dispute resolution

---

## Architecture: Governance-as-a-Service (GaaS)

Based on research: arxiv.org/html/2508.18765v2

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GOVERNANCE MCP SERVER                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ Rule Engine │  │ Consensus   │  │ Trust       │                 │
│  │             │  │ Protocol    │  │ Scoring     │                 │
│  │ - Validate  │  │ - Vote      │  │ - History   │                 │
│  │ - Enforce   │  │ - Debate    │  │ - Compliance│                 │
│  │ - Infer     │  │ - Resolve   │  │ - Severity  │                 │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
│         │                │                │                         │
│         └────────────────┼────────────────┘                         │
│                          │                                          │
│                   ┌──────┴──────┐                                   │
│                   │   TypeDB    │                                   │
│                   │ (Inference) │                                   │
│                   └─────────────┘                                   │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  MCP TOOLS:                                                          │
│  - governance_propose_rule    - governance_resolve_conflict         │
│  - governance_vote            - governance_get_trust_score          │
│  - governance_dispute         - governance_sync_state               │
│  - governance_query_rules     - governance_hypothesis_test          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## TypeDB Schema Extensions

### New Entity Types

```typeql
# Agent entity for trust tracking
agent sub entity,
    owns agent-id,
    owns agent-name,
    owns agent-type,        # "claude-code", "docker-agent", "sync-agent"
    owns trust-score,       # 0.0 to 1.0
    owns compliance-rate,   # Historical compliance
    plays proposal:proposer,
    plays vote:voter,
    plays dispute:disputer;

# Proposal for rule changes
proposal sub entity,
    owns proposal-id,
    owns proposal-type,     # "create", "modify", "deprecate"
    owns proposal-status,   # "pending", "approved", "rejected", "disputed"
    owns evidence,
    owns hypothesis,
    owns created-at,
    plays proposal:proposer,
    plays vote:target,
    plays dispute:disputed-proposal;

# Vote on proposals
vote sub relation,
    relates voter,
    relates target,
    owns vote-value,        # "approve", "reject", "abstain"
    owns vote-reason,
    owns vote-timestamp;

# Dispute mechanism
dispute sub relation,
    relates disputer,
    relates disputed-proposal,
    owns dispute-reason,
    owns semantic-analysis,
    owns resolution-method; # "consensus", "evidence", "authority"
```

### Conflict Resolution Inference Rules

```typeql
# Semantic conflict detection
rule semantic-conflict:
    when {
        $r1 isa rule-entity, has directive $d1, has status "ACTIVE";
        $r2 isa rule-entity, has directive $d2, has status "ACTIVE";
        not { $r1 is $r2; };
        # Semantic similarity would be computed externally
    } then {
        (conflicting-rule: $r1, conflicting-rule: $r2) isa rule-conflict;
    };

# Trust-weighted consensus
rule trust-weighted-approval:
    when {
        $p isa proposal, has proposal-id $pid;
        $votes = (voter: $a, target: $p) isa vote;
        $a has trust-score $ts;
        # Weighted voting based on trust score
    } then {
        # Approval threshold met
    };

# Evidence strength scoring
rule evidence-based-resolution:
    when {
        $d isa dispute, has dispute-reason $reason;
        $p isa proposal, has evidence $e, has hypothesis $h;
        (disputed-proposal: $p) isa dispute;
        # Evidence validation
    } then {
        # Resolution based on evidence weight
    };
```

---

## Conflict Resolution Protocol

### Phase 1: Detection

```
1. Agent proposes rule change
2. TypeDB checks for conflicts:
   - Priority conflict (same category, different priority)
   - Semantic conflict (similar directives, different outcomes)
   - Dependency conflict (breaks dependency chain)
3. If conflict detected → Phase 2
```

### Phase 2: Hypothesis-Based Resolution (RULE-010)

```
HYPOTHESIS: "Rule A should take precedence over Rule B"

EVIDENCE:
- Rule A has higher trust score (0.9 vs 0.7)
- Rule A has more recent evidence (2024-12-24 vs 2024-11-01)
- Rule A aligns with RULE-008 (In-House Rewrite Principle)

SEMANTIC ANALYSIS:
- Directive clarity score: A=0.85, B=0.72
- Ambiguity detection: A=low, B=medium
- Scope overlap: 67%

CONCLUSION:
- Resolution: Merge rules, A takes priority
- Rationale: Higher evidence, clearer directive
- Action: Create merged rule, deprecate B
```

### Phase 3: Consensus Voting

```
Agents vote on resolution:
- Claude Code Agent: APPROVE (trust: 0.95)
- Docker Agent 1:    APPROVE (trust: 0.88)
- Docker Agent 2:    ABSTAIN (trust: 0.75)

Weighted score: (0.95 + 0.88) / 2 = 0.915 > 0.80 threshold
Result: APPROVED
```

### Phase 4: Sync & Propagate

```
1. Update TypeDB with resolution
2. Notify all agents via MCP
3. Update trust scores based on vote alignment
4. Log evidence trail
```

---

## MCP Tool Specifications

### governance_propose_rule

```json
{
  "name": "governance_propose_rule",
  "description": "Propose a new rule or modification",
  "inputSchema": {
    "type": "object",
    "properties": {
      "rule_id": {"type": "string"},
      "action": {"enum": ["create", "modify", "deprecate"]},
      "hypothesis": {"type": "string"},
      "evidence": {"type": "array", "items": {"type": "string"}},
      "directive": {"type": "string"}
    },
    "required": ["action", "hypothesis", "evidence"]
  }
}
```

### governance_resolve_conflict

```json
{
  "name": "governance_resolve_conflict",
  "description": "Resolve conflict between rules using evidence-based approach",
  "inputSchema": {
    "type": "object",
    "properties": {
      "conflict_id": {"type": "string"},
      "resolution_method": {"enum": ["consensus", "evidence", "authority", "merge"]},
      "semantic_analysis": {"type": "object"},
      "hypothesis": {"type": "string"}
    },
    "required": ["conflict_id", "resolution_method"]
  }
}
```

### governance_hypothesis_test

```json
{
  "name": "governance_hypothesis_test",
  "description": "Test a hypothesis about rule behavior",
  "inputSchema": {
    "type": "object",
    "properties": {
      "hypothesis": {"type": "string"},
      "test_cases": {"type": "array"},
      "expected_outcome": {"type": "string"},
      "evidence_required": {"type": "array"}
    },
    "required": ["hypothesis", "test_cases"]
  }
}
```

---

## Trust Score Algorithm

```python
def calculate_trust_score(agent_id: str) -> float:
    """
    Trust = (Compliance * 0.4) + (Accuracy * 0.3) + (Consistency * 0.2) + (Tenure * 0.1)

    Compliance: % of rules followed
    Accuracy: % of predictions that were correct
    Consistency: Variance in behavior over time
    Tenure: Time-weighted experience factor
    """
    history = get_agent_history(agent_id)

    compliance = sum(h.compliant for h in history) / len(history)
    accuracy = sum(h.accurate for h in history) / len(history)
    consistency = 1 - calculate_variance(history)
    tenure = min(1.0, days_active / 365)

    return (compliance * 0.4) + (accuracy * 0.3) + (consistency * 0.2) + (tenure * 0.1)
```

---

## BDD Test Scenarios

```gherkin
Feature: Conflict Resolution
  As an AI governance system
  I want to resolve rule conflicts using evidence
  So that agents can operate without ambiguity

  Scenario: Semantic conflict detected
    Given RULE-001 has directive "Log all sessions"
    And RULE-012 has directive "Skip logging for test sessions"
    When both rules apply to a test session
    Then a semantic conflict should be detected
    And the conflict should trigger hypothesis-based resolution

  Scenario: Trust-weighted voting
    Given a proposal to modify RULE-005
    And Claude Code agent has trust score 0.95
    And Docker agent has trust score 0.70
    When both agents vote APPROVE
    Then the weighted approval score should be 0.825
    And the proposal should be APPROVED (threshold 0.80)

  Scenario: Evidence-based dispute resolution
    Given RULE-A and RULE-B are in conflict
    And RULE-A has 5 supporting evidence items
    And RULE-B has 2 supporting evidence items
    When dispute resolution is triggered
    Then RULE-A should be favored based on evidence weight
    And the resolution should be logged with rationale
```

---

## Implementation Phases

### Phase 1: Foundation (Current)
- [x] TypeDB schema for rules/decisions
- [x] Inference rules (transitive, cascade, conflict)
- [x] Python client wrapper
- [ ] Extended schema for agents/proposals/votes

### Phase 2: Governance MCP
- [ ] MCP server implementation
- [ ] Trust scoring algorithm
- [ ] Conflict detection hooks
- [ ] Basic consensus protocol

### Phase 3: Advanced Resolution
- [ ] Semantic analysis integration (embeddings)
- [ ] Hypothesis testing framework
- [ ] Dispute resolution workflow
- [ ] BDD test suite

### Phase 4: Production Sync
- [ ] Bidirectional sync protocol
- [ ] Agent state management
- [ ] Audit trail and compliance logging
- [ ] Dashboard for human oversight

---

## References

- [Governance-as-a-Service Framework](https://arxiv.org/html/2508.18765v2)
- [Multi-Agent Collaboration Mechanisms](https://arxiv.org/html/2501.06322v1)
- [Multi-Agent Risks from Advanced AI](https://arxiv.org/abs/2502.14143)
- [Anthropic MCP Protocol](https://modelcontextprotocol.io/)
- RULE-010: Evidence-Based Wisdom Accumulation
- Bicameral Governance Model (claude-mem)

---

*Document created: 2024-12-24*
*Status: DRAFT - Pending DECISION-005 approval*
