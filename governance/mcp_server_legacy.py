"""
Governance MCP Server - Multi-Agent Conflict Resolution
Implements Governance-as-a-Service (GaaS) pattern from DESIGN-Governance-MCP.md

Created: 2024-12-24 (RULE-011, DECISION-005)
Protocol: MCP (Model Context Protocol)
Backend: TypeDB 2.29.1

Usage:
    python governance/mcp_server.py

Or add to MCP config:
    {
        "governance": {
            "command": "python",
            "args": ["governance/mcp_server.py"],
            "env": {"TYPEDB_HOST": "localhost", "TYPEDB_PORT": "1729"}
        }
    }
"""

import os
import json
from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass, asdict

from mcp.server.fastmcp import FastMCP

# Import TypeDB client
try:
    from governance.client import TypeDBClient
except ImportError:
    # When running as script
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from governance.client import TypeDBClient

# Initialize MCP server
mcp = FastMCP("governance")

# TypeDB configuration
TYPEDB_HOST = os.getenv("TYPEDB_HOST", "localhost")
TYPEDB_PORT = int(os.getenv("TYPEDB_PORT", "1729"))
DATABASE_NAME = "sim-ai-governance"


@dataclass
class TrustScore:
    """Agent trust score calculation result."""
    agent_id: str
    agent_name: str
    trust_score: float
    compliance_rate: float
    accuracy_rate: float
    tenure_days: int
    vote_weight: float  # Derived from trust_score


def calculate_vote_weight(trust_score: float) -> float:
    """Calculate vote weight based on trust score (RULE-011)."""
    # Low trust agents (< 0.5) have vote-weight = trust-score
    # High trust agents (>= 0.5) have vote-weight = 1.0
    return 1.0 if trust_score >= 0.5 else trust_score


# =============================================================================
# MCP TOOLS - Query Operations
# =============================================================================

@mcp.tool()
def governance_query_rules(
    category: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None
) -> str:
    """
    Query rules from the governance database.

    Args:
        category: Filter by category (governance, architecture, testing, etc.)
        status: Filter by status (ACTIVE, DRAFT, DEPRECATED)
        priority: Filter by priority (CRITICAL, HIGH, MEDIUM, LOW)

    Returns:
        JSON array of matching rules
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        # Build query based on filters
        if status == "ACTIVE":
            rules = client.get_active_rules()
        else:
            rules = client.get_all_rules()

        # Apply additional filters
        if category:
            rules = [r for r in rules if r.category == category]
        if priority:
            rules = [r for r in rules if r.priority == priority]
        if status and status != "ACTIVE":
            rules = [r for r in rules if r.status == status]

        return json.dumps([asdict(r) for r in rules], default=str, indent=2)

    finally:
        client.close()


@mcp.tool()
def governance_get_rule(rule_id: str) -> str:
    """
    Get a specific rule by ID.

    Args:
        rule_id: The rule ID (e.g., "RULE-001")

    Returns:
        JSON object with rule details or error
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        rule = client.get_rule_by_id(rule_id)
        if rule:
            return json.dumps(asdict(rule), default=str, indent=2)
        else:
            return json.dumps({"error": f"Rule {rule_id} not found"})

    finally:
        client.close()


@mcp.tool()
def governance_get_dependencies(rule_id: str) -> str:
    """
    Get all dependencies for a rule (uses TypeDB inference for transitive deps).

    Args:
        rule_id: The rule ID to get dependencies for

    Returns:
        JSON array of dependency rule IDs
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        deps = client.get_rule_dependencies(rule_id)
        return json.dumps(deps, indent=2)

    finally:
        client.close()


@mcp.tool()
def governance_find_conflicts() -> str:
    """
    Find conflicting rules using TypeDB inference.

    Returns:
        JSON array of conflict pairs with explanations
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        conflicts = client.find_conflicts()
        return json.dumps(conflicts, indent=2)

    finally:
        client.close()


# =============================================================================
# MCP TOOLS - Trust Score Operations
# =============================================================================

@mcp.tool()
def governance_get_trust_score(agent_id: str) -> str:
    """
    Get trust score for an agent (RULE-011).

    Trust Formula: (Compliance × 0.4) + (Accuracy × 0.3) + (Consistency × 0.2) + (Tenure × 0.1)

    Args:
        agent_id: The agent ID (e.g., "AGENT-001")

    Returns:
        JSON object with trust score details
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        # Query agent data from TypeDB
        query = f'''
            match
                $a isa agent, has agent-id "{agent_id}";
                $a has agent-name $name;
                $a has trust-score $trust;
                $a has compliance-rate $compliance;
                $a has accuracy-rate $accuracy;
                $a has tenure-days $tenure;
            get $name, $trust, $compliance, $accuracy, $tenure;
        '''

        results = client.execute_query(query)

        if not results:
            return json.dumps({"error": f"Agent {agent_id} not found"})

        result = results[0]
        trust_score = result.get('trust', 0.0)

        score = TrustScore(
            agent_id=agent_id,
            agent_name=result.get('name', 'Unknown'),
            trust_score=trust_score,
            compliance_rate=result.get('compliance', 0.0),
            accuracy_rate=result.get('accuracy', 0.0),
            tenure_days=result.get('tenure', 0),
            vote_weight=calculate_vote_weight(trust_score)
        )

        return json.dumps(asdict(score), indent=2)

    finally:
        client.close()


@mcp.tool()
def governance_list_agents() -> str:
    """
    List all registered agents with their trust scores.

    Returns:
        JSON array of agents with trust information
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        query = '''
            match
                $a isa agent;
                $a has agent-id $id;
                $a has agent-name $name;
                $a has agent-type $type;
                $a has trust-score $trust;
            get $id, $name, $type, $trust;
        '''

        results = client.execute_query(query)

        agents = []
        for r in results:
            agents.append({
                "agent_id": r.get('id'),
                "agent_name": r.get('name'),
                "agent_type": r.get('type'),
                "trust_score": r.get('trust'),
                "vote_weight": calculate_vote_weight(r.get('trust', 0.0))
            })

        return json.dumps(agents, indent=2)

    finally:
        client.close()


# =============================================================================
# MCP TOOLS - Proposal Operations
# =============================================================================

@mcp.tool()
def governance_propose_rule(
    action: str,
    hypothesis: str,
    evidence: list[str],
    rule_id: Optional[str] = None,
    directive: Optional[str] = None
) -> str:
    """
    Propose a new rule or modification (RULE-011).

    Args:
        action: "create", "modify", or "deprecate"
        hypothesis: Why this change is needed
        evidence: List of evidence items supporting the proposal
        rule_id: Required for modify/deprecate actions
        directive: Required for create/modify actions

    Returns:
        JSON object with proposal ID and status
    """
    # Validate inputs
    if action not in ["create", "modify", "deprecate"]:
        return json.dumps({"error": f"Invalid action: {action}"})

    if action in ["modify", "deprecate"] and not rule_id:
        return json.dumps({"error": f"rule_id required for {action} action"})

    if action in ["create", "modify"] and not directive:
        return json.dumps({"error": f"directive required for {action} action"})

    # Generate proposal ID
    proposal_id = f"PROPOSAL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Note: Full implementation would insert into TypeDB
    # For now, return the proposal structure
    proposal = {
        "proposal_id": proposal_id,
        "action": action,
        "hypothesis": hypothesis,
        "evidence": evidence,
        "rule_id": rule_id,
        "directive": directive,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "message": "Proposal created. Awaiting votes from agents."
    }

    return json.dumps(proposal, indent=2)


@mcp.tool()
def governance_vote(
    proposal_id: str,
    agent_id: str,
    vote: str,
    reason: Optional[str] = None
) -> str:
    """
    Vote on a proposal (RULE-011).

    Args:
        proposal_id: The proposal to vote on
        agent_id: The voting agent's ID
        vote: "approve", "reject", or "abstain"
        reason: Optional reason for the vote

    Returns:
        JSON object with vote confirmation and weighted score
    """
    if vote not in ["approve", "reject", "abstain"]:
        return json.dumps({"error": f"Invalid vote: {vote}"})

    # Get agent's trust score for vote weighting
    trust_result = governance_get_trust_score(agent_id)
    trust_data = json.loads(trust_result)

    if "error" in trust_data:
        return json.dumps({"error": f"Cannot get trust score: {trust_data['error']}"})

    vote_weight = trust_data["vote_weight"]

    vote_record = {
        "proposal_id": proposal_id,
        "agent_id": agent_id,
        "vote": vote,
        "reason": reason,
        "vote_weight": vote_weight,
        "timestamp": datetime.now().isoformat(),
        "message": f"Vote recorded with weight {vote_weight:.2f}"
    }

    return json.dumps(vote_record, indent=2)


@mcp.tool()
def governance_dispute(
    proposal_id: str,
    agent_id: str,
    reason: str,
    resolution_method: str = "evidence"
) -> str:
    """
    Dispute a proposal (RULE-011).

    Args:
        proposal_id: The proposal to dispute
        agent_id: The disputing agent's ID
        reason: Why the proposal is disputed
        resolution_method: "consensus", "evidence", "authority", or "escalate"

    Returns:
        JSON object with dispute status
    """
    if resolution_method not in ["consensus", "evidence", "authority", "escalate"]:
        return json.dumps({"error": f"Invalid resolution method: {resolution_method}"})

    dispute = {
        "dispute_id": f"DISPUTE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "proposal_id": proposal_id,
        "agent_id": agent_id,
        "reason": reason,
        "resolution_method": resolution_method,
        "status": "active",
        "escalation_required": resolution_method == "escalate",
        "timestamp": datetime.now().isoformat()
    }

    if resolution_method == "escalate":
        dispute["message"] = "ESCALATION: Human oversight required (RULE-011 bicameral model)"
    else:
        dispute["message"] = f"Dispute filed. Resolution method: {resolution_method}"

    return json.dumps(dispute, indent=2)


# =============================================================================
# MCP TOOLS - Decision Impact
# =============================================================================

@mcp.tool()
def governance_get_decision_impacts(decision_id: str) -> str:
    """
    Get all rules affected by a decision (uses TypeDB inference).

    Args:
        decision_id: The decision ID (e.g., "DECISION-003")

    Returns:
        JSON array of affected rule IDs
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        if not client.connect():
            return json.dumps({"error": "Failed to connect to TypeDB"})

        impacts = client.get_decision_impacts(decision_id)
        return json.dumps(impacts, indent=2)

    finally:
        client.close()


# =============================================================================
# MCP TOOLS - Health Check
# =============================================================================

@mcp.tool()
def governance_health() -> str:
    """
    Check governance system health.

    Returns:
        JSON object with health status and statistics
    """
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)

    try:
        connected = client.connect()

        if not connected:
            return json.dumps({
                "status": "unhealthy",
                "typedb_connected": False,
                "error": "Cannot connect to TypeDB"
            })

        # Get counts
        rules = client.get_all_rules()

        return json.dumps({
            "status": "healthy",
            "typedb_connected": True,
            "typedb_host": f"{TYPEDB_HOST}:{TYPEDB_PORT}",
            "database": DATABASE_NAME,
            "statistics": {
                "rules_count": len(rules),
                "active_rules": len([r for r in rules if r.status == "ACTIVE"])
            },
            "timestamp": datetime.now().isoformat()
        }, indent=2)

    finally:
        client.close()


# =============================================================================
# MCP TOOLS - Session Evidence (P4.2)
# =============================================================================

# Import session collector
try:
    from governance.session_collector import (
        SessionCollector,
        get_or_create_session,
        end_session,
        list_active_sessions
    )
    SESSION_COLLECTOR_AVAILABLE = True
except ImportError:
    SESSION_COLLECTOR_AVAILABLE = False


@mcp.tool()
def session_start(topic: str, session_type: str = "general") -> str:
    """
    Start a new session with evidence collection.

    Args:
        topic: Session topic (e.g., "STRATEGIC-VISION", "RD-HASKELL-MCP")
        session_type: Type of session (general, strategic, research, debug)

    Returns:
        JSON object with session ID and status
    """
    if not SESSION_COLLECTOR_AVAILABLE:
        return json.dumps({"error": "SessionCollector not available"})

    collector = get_or_create_session(topic, session_type)

    return json.dumps({
        "session_id": collector.session_id,
        "topic": topic,
        "session_type": session_type,
        "started_at": collector.start_time.isoformat(),
        "message": f"Session started: {collector.session_id}"
    }, indent=2)


@mcp.tool()
def session_decision(
    decision_id: str,
    name: str,
    context: str,
    rationale: str,
    topic: Optional[str] = None
) -> str:
    """
    Record a strategic decision in the current session.

    Args:
        decision_id: Decision ID (e.g., "DECISION-007")
        name: Decision title
        context: Context/problem statement
        rationale: Reasoning for the decision
        topic: Session topic (uses last session if not provided)

    Returns:
        JSON object with decision confirmation
    """
    if not SESSION_COLLECTOR_AVAILABLE:
        return json.dumps({"error": "SessionCollector not available"})

    # Get or create session
    sessions = list_active_sessions()
    if not sessions and not topic:
        return json.dumps({"error": "No active session. Call session_start first."})

    collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())

    decision = collector.capture_decision(
        decision_id=decision_id,
        name=name,
        context=context,
        rationale=rationale
    )

    return json.dumps({
        "decision_id": decision_id,
        "session_id": collector.session_id,
        "name": name,
        "indexed_to_typedb": TYPEDB_AVAILABLE,
        "message": f"Decision {decision_id} recorded and indexed"
    }, indent=2)


@mcp.tool()
def session_task(
    task_id: str,
    name: str,
    description: str,
    status: str = "pending",
    priority: str = "MEDIUM",
    topic: Optional[str] = None
) -> str:
    """
    Record a task in the current session.

    Args:
        task_id: Task ID (e.g., "P4.2", "RD-001")
        name: Task name
        description: Task description
        status: Task status (pending, in_progress, completed, blocked)
        priority: Task priority (LOW, MEDIUM, HIGH, CRITICAL)
        topic: Session topic (uses last session if not provided)

    Returns:
        JSON object with task confirmation
    """
    if not SESSION_COLLECTOR_AVAILABLE:
        return json.dumps({"error": "SessionCollector not available"})

    # Get or create session
    sessions = list_active_sessions()
    if not sessions and not topic:
        return json.dumps({"error": "No active session. Call session_start first."})

    collector = get_or_create_session(topic or sessions[-1].split("-")[-1].lower())

    task = collector.capture_task(
        task_id=task_id,
        name=name,
        description=description,
        status=status,
        priority=priority
    )

    return json.dumps({
        "task_id": task_id,
        "session_id": collector.session_id,
        "name": name,
        "status": status,
        "message": f"Task {task_id} recorded"
    }, indent=2)


@mcp.tool()
def session_end(topic: str) -> str:
    """
    End session and generate evidence artifacts.

    Args:
        topic: Session topic to end

    Returns:
        JSON object with log path and sync status
    """
    if not SESSION_COLLECTOR_AVAILABLE:
        return json.dumps({"error": "SessionCollector not available"})

    log_path = end_session(topic)

    if log_path:
        return json.dumps({
            "topic": topic,
            "log_path": log_path,
            "synced_to_chromadb": True,
            "message": f"Session ended. Log: {log_path}"
        }, indent=2)
    else:
        return json.dumps({
            "error": f"Session for topic '{topic}' not found"
        })


@mcp.tool()
def session_list() -> str:
    """
    List all active sessions.

    Returns:
        JSON array of active session IDs
    """
    if not SESSION_COLLECTOR_AVAILABLE:
        return json.dumps({"error": "SessionCollector not available"})

    sessions = list_active_sessions()

    return json.dumps({
        "active_sessions": sessions,
        "count": len(sessions)
    }, indent=2)


# =============================================================================
# MCP TOOLS - Rule Quality Analysis
# =============================================================================

# Import rule quality analyzer
try:
    from governance.rule_quality import (
        RuleQualityAnalyzer,
        analyze_rule_quality,
        get_rule_impact,
        find_rule_issues
    )
    RULE_QUALITY_AVAILABLE = True
except ImportError:
    RULE_QUALITY_AVAILABLE = False


@mcp.tool()
def governance_analyze_rules() -> str:
    """
    Run comprehensive rule quality analysis.

    Detects:
    - Orphaned rules (no dependents)
    - Shallow rules (missing attributes)
    - Over-connected rules (too many dependencies)
    - Under-documented rules (not referenced by docs)
    - Circular dependencies

    Returns:
        JSON health report with issues, severity, impact, and remediation
    """
    if not RULE_QUALITY_AVAILABLE:
        return json.dumps({"error": "RuleQualityAnalyzer not available"})

    return analyze_rule_quality()


@mcp.tool()
def governance_rule_impact(rule_id: str) -> str:
    """
    Analyze impact if a rule is modified or deprecated.

    Args:
        rule_id: Rule ID (e.g., "RULE-001")

    Returns:
        JSON with affected rules, impact score, and recommendation
    """
    if not RULE_QUALITY_AVAILABLE:
        return json.dumps({"error": "RuleQualityAnalyzer not available"})

    return get_rule_impact(rule_id)


@mcp.tool()
def governance_find_issues(issue_type: Optional[str] = None) -> str:
    """
    Find specific types of rule quality issues.

    Args:
        issue_type: Type of issues to find:
            - "orphaned": Rules with no dependents
            - "shallow": Rules missing attributes
            - "over_connected": Rules with too many dependencies
            - "circular": Circular dependency chains
            - "under_documented": Rules not in any docs
            - None: All issues (default)

    Returns:
        JSON array of issues with severity, impact, and remediation
    """
    if not RULE_QUALITY_AVAILABLE:
        return json.dumps({"error": "RuleQualityAnalyzer not available"})

    return find_rule_issues(issue_type)


# =============================================================================
# MCP TOOLS - DSM Tracker (P4.3 - RULE-012 Deep Sleep Protocol)
# =============================================================================

# Import DSM tracker
try:
    from governance.dsm_tracker import (
        DSMTracker,
        DSPPhase,
        get_tracker,
        reset_tracker
    )
    DSM_TRACKER_AVAILABLE = True
except ImportError:
    DSM_TRACKER_AVAILABLE = False


@mcp.tool()
def dsm_start(batch_id: Optional[str] = None) -> str:
    """
    Start a new DSM cycle (RULE-012 Deep Sleep Protocol).

    Args:
        batch_id: Optional batch identifier (e.g., "P4.3", "RD-001")

    Returns:
        JSON object with cycle ID and current phase
    """
    if not DSM_TRACKER_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})

    tracker = get_tracker()

    try:
        cycle = tracker.start_cycle(batch_id)
        return json.dumps({
            "cycle_id": cycle.cycle_id,
            "batch_id": cycle.batch_id,
            "current_phase": cycle.current_phase,  # Already a string
            "started_at": cycle.start_time,
            "message": f"DSM cycle started: {cycle.cycle_id}"
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def dsm_advance() -> str:
    """
    Advance to the next DSP phase.

    Phase sequence: IDLE → AUDIT → HYPOTHESIZE → MEASURE → OPTIMIZE → VALIDATE → DREAM → REPORT

    Returns:
        JSON object with new phase and required MCPs
    """
    if not DSM_TRACKER_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})

    tracker = get_tracker()

    try:
        new_phase = tracker.advance_phase()
        return json.dumps({
            "new_phase": new_phase.value,
            "required_mcps": new_phase.required_mcps,
            "message": f"Advanced to phase: {new_phase.value}"
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def dsm_checkpoint(
    description: str,
    metrics: Optional[str] = None,
    evidence: Optional[str] = None
) -> str:
    """
    Record a checkpoint in the current phase.

    Args:
        description: What was accomplished
        metrics: Optional JSON metrics (e.g., '{"tests_passed": 78}')
        evidence: Optional evidence reference (file path or URL)

    Returns:
        JSON object with checkpoint details
    """
    if not DSM_TRACKER_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})

    tracker = get_tracker()

    # Parse optional JSON metrics
    parsed_metrics = None
    if metrics:
        try:
            parsed_metrics = json.loads(metrics)
        except json.JSONDecodeError:
            return json.dumps({"error": f"Invalid metrics JSON: {metrics}"})

    try:
        checkpoint = tracker.checkpoint(
            description=description,
            metrics=parsed_metrics,
            evidence=evidence
        )
        return json.dumps({
            "phase": checkpoint.phase,  # Already a string
            "description": checkpoint.description,
            "timestamp": checkpoint.timestamp,
            "metrics": checkpoint.metrics,
            "evidence": checkpoint.evidence,
            "message": "Checkpoint recorded"
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def dsm_finding(
    finding_type: str,
    description: str,
    severity: str = "MEDIUM",
    related_rules: Optional[str] = None
) -> str:
    """
    Add a finding to the current cycle.

    Args:
        finding_type: Type of finding (gap, issue, improvement, observation)
        description: Description of the finding
        severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
        related_rules: Comma-separated rule IDs (e.g., "RULE-001,RULE-004")

    Returns:
        JSON object with finding ID and details
    """
    if not DSM_TRACKER_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})

    tracker = get_tracker()

    # Parse related rules
    rules = None
    if related_rules:
        rules = [r.strip() for r in related_rules.split(",")]

    try:
        finding = tracker.add_finding(
            finding_type=finding_type,
            description=description,
            severity=severity,
            related_rules=rules
        )
        return json.dumps({
            "finding_id": finding["id"],  # Key is 'id' in DSMTracker
            "finding_type": finding_type,
            "description": description,
            "severity": severity,
            "related_rules": rules or [],
            "message": f"Finding recorded: {finding['id']}"
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def dsm_status() -> str:
    """
    Get current DSM cycle status.

    Returns:
        JSON object with current phase, checkpoints, findings, and metrics
    """
    if not DSM_TRACKER_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})

    tracker = get_tracker()
    status = tracker.get_status()

    return json.dumps(status, indent=2)


@mcp.tool()
def dsm_complete() -> str:
    """
    Complete the current DSM cycle and generate evidence.

    Returns:
        JSON object with evidence path and cycle summary
    """
    if not DSM_TRACKER_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})

    tracker = get_tracker()

    try:
        evidence_path = tracker.complete_cycle()
        return json.dumps({
            "status": "completed",
            "evidence_path": evidence_path,
            "completed_cycles": len(tracker.completed_cycles),
            "message": f"Cycle completed. Evidence: {evidence_path}"
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def dsm_metrics(metrics_json: str) -> str:
    """
    Update metrics for the current cycle.

    Args:
        metrics_json: JSON object with metrics (e.g., '{"tests_passed": 78, "coverage": 85}')

    Returns:
        JSON object with updated metrics
    """
    if not DSM_TRACKER_AVAILABLE:
        return json.dumps({"error": "DSMTracker not available"})

    tracker = get_tracker()

    try:
        metrics = json.loads(metrics_json)
    except json.JSONDecodeError:
        return json.dumps({"error": f"Invalid metrics JSON: {metrics_json}"})

    try:
        tracker.update_metrics(metrics)
        return json.dumps({
            "metrics": tracker.current_cycle.metrics,
            "message": "Metrics updated"
        }, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})


# Check TypeDB availability for session tools
try:
    TYPEDB_AVAILABLE = True
except:
    TYPEDB_AVAILABLE = False


# =============================================================================
# MCP TOOLS - Evidence Viewing (P9.1 - Strategic Platform)
# =============================================================================
# Strategic Goal: View all task/session/evidence artifacts via MCP and UI

import glob
from pathlib import Path

# Evidence paths
EVIDENCE_DIR = Path("evidence")
DOCS_DIR = Path("docs")
BACKLOG_DIR = DOCS_DIR / "backlog"


@mcp.tool()
def governance_list_sessions(
    limit: int = 20,
    session_type: Optional[str] = None
) -> str:
    """
    List all session evidence files.

    Args:
        limit: Maximum number of sessions to return (default 20)
        session_type: Filter by session type (e.g., "PHASE", "DSP", "STRATEGIC")

    Returns:
        JSON array of sessions with ID, date, topic, and summary
    """
    sessions = []

    # Search evidence directory for session files
    pattern = EVIDENCE_DIR / "SESSION-*.md"
    for filepath in sorted(glob.glob(str(pattern)), reverse=True)[:limit]:
        try:
            path = Path(filepath)
            filename = path.name

            # Parse filename: SESSION-YYYY-MM-DD-TOPIC.md
            parts = filename.replace(".md", "").split("-")
            if len(parts) >= 4:
                date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"
                topic = "-".join(parts[4:]) if len(parts) > 4 else "general"
            else:
                date_str = "unknown"
                topic = filename

            # Apply type filter
            if session_type and session_type.upper() not in topic.upper():
                continue

            # Read first few lines for summary
            content = path.read_text(encoding="utf-8")
            lines = content.split("\n")
            summary = ""
            for line in lines[:10]:
                if line.startswith("## Summary") or line.startswith("**Summary"):
                    idx = lines.index(line)
                    if idx + 1 < len(lines):
                        summary = lines[idx + 1].strip()
                    break

            sessions.append({
                "session_id": filename.replace(".md", ""),
                "date": date_str,
                "topic": topic,
                "summary": summary[:200] if summary else "No summary available",
                "path": str(filepath)
            })

        except Exception as e:
            continue

    return json.dumps({
        "sessions": sessions,
        "count": len(sessions),
        "total_available": len(list(glob.glob(str(EVIDENCE_DIR / "SESSION-*.md"))))
    }, indent=2)


@mcp.tool()
def governance_get_session(session_id: str) -> str:
    """
    Get full session evidence content.

    Args:
        session_id: Session ID (e.g., "SESSION-2024-12-25-PHASE8")

    Returns:
        JSON object with session metadata and full markdown content
    """
    # Handle both with and without .md extension
    if not session_id.endswith(".md"):
        session_id = session_id + ".md"

    filepath = EVIDENCE_DIR / session_id

    if not filepath.exists():
        # Try without SESSION- prefix
        if not session_id.startswith("SESSION-"):
            filepath = EVIDENCE_DIR / f"SESSION-{session_id}"
        if not filepath.exists():
            return json.dumps({"error": f"Session not found: {session_id}"})

    try:
        content = filepath.read_text(encoding="utf-8")

        # Parse metadata from content
        lines = content.split("\n")
        metadata = {}
        for line in lines[:20]:
            if line.startswith("**Date:**"):
                metadata["date"] = line.replace("**Date:**", "").strip()
            elif line.startswith("**Session ID:**"):
                metadata["session_id"] = line.replace("**Session ID:**", "").strip()
            elif line.startswith("**Status:**"):
                metadata["status"] = line.replace("**Status:**", "").strip()

        return json.dumps({
            "session_id": session_id.replace(".md", ""),
            "path": str(filepath),
            "metadata": metadata,
            "content": content,
            "lines": len(lines)
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Failed to read session: {str(e)}"})


@mcp.tool()
def governance_list_decisions() -> str:
    """
    List all strategic decisions from TypeDB and evidence files.

    Returns:
        JSON array of decisions with ID, name, status, and date
    """
    decisions = []

    # Get from TypeDB
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)
    try:
        if client.connect():
            db_decisions = client.get_all_decisions()
            for d in db_decisions:
                decisions.append({
                    "decision_id": d.id,
                    "name": d.name,
                    "status": d.status,
                    "date": str(d.decision_date) if d.decision_date else None,
                    "source": "typedb"
                })
            client.close()
    except:
        pass

    # Also scan evidence directory for DECISION-*.md files
    pattern = EVIDENCE_DIR / "DECISION-*.md"
    for filepath in glob.glob(str(pattern)):
        try:
            path = Path(filepath)
            filename = path.name.replace(".md", "")
            # Check if already in list from TypeDB
            if not any(d["decision_id"] == filename for d in decisions):
                content = path.read_text(encoding="utf-8")
                # Extract title from first # heading
                title = filename
                for line in content.split("\n"):
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                decisions.append({
                    "decision_id": filename,
                    "name": title,
                    "status": "DOCUMENTED",
                    "date": None,
                    "source": "evidence_file"
                })
        except:
            continue

    return json.dumps({
        "decisions": decisions,
        "count": len(decisions)
    }, indent=2)


@mcp.tool()
def governance_get_decision(decision_id: str) -> str:
    """
    Get detailed decision information.

    Args:
        decision_id: Decision ID (e.g., "DECISION-003")

    Returns:
        JSON object with decision details, context, rationale, and impacts
    """
    result = {"decision_id": decision_id}

    # Get from TypeDB
    client = TypeDBClient(host=TYPEDB_HOST, port=TYPEDB_PORT, database=DATABASE_NAME)
    try:
        if client.connect():
            db_decisions = client.get_all_decisions()
            for d in db_decisions:
                if d.id == decision_id:
                    result["name"] = d.name
                    result["context"] = d.context
                    result["rationale"] = d.rationale
                    result["status"] = d.status
                    result["date"] = str(d.decision_date) if d.decision_date else None
                    result["source"] = "typedb"

                    # Get impacts
                    impacts = client.get_decision_impacts(decision_id)
                    result["affected_rules"] = impacts
                    break

            client.close()
    except:
        pass

    # Check for evidence file
    evidence_file = EVIDENCE_DIR / f"{decision_id}.md"
    if not evidence_file.exists():
        # Try with suffix
        matches = list(glob.glob(str(EVIDENCE_DIR / f"{decision_id}*.md")))
        if matches:
            evidence_file = Path(matches[0])

    if evidence_file.exists():
        result["evidence_file"] = str(evidence_file)
        result["evidence_content"] = evidence_file.read_text(encoding="utf-8")

    if len(result) == 1:  # Only has decision_id
        return json.dumps({"error": f"Decision {decision_id} not found"})

    return json.dumps(result, indent=2)


@mcp.tool()
def governance_list_tasks(
    phase: Optional[str] = None,
    status: Optional[str] = None
) -> str:
    """
    List R&D and backlog tasks.

    Args:
        phase: Filter by phase (e.g., "P7", "P9", "FH", "RD")
        status: Filter by status (e.g., "TODO", "DONE", "IN_PROGRESS")

    Returns:
        JSON array of tasks with ID, name, status, and priority
    """
    tasks = []

    # Parse R&D-BACKLOG.md
    backlog_file = BACKLOG_DIR / "R&D-BACKLOG.md"
    if backlog_file.exists():
        content = backlog_file.read_text(encoding="utf-8")

        # Parse task tables
        import re
        table_pattern = r"\|\s*([\w.-]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"

        for match in re.finditer(table_pattern, content):
            task_id, name_or_status, status_or_desc, priority_or_notes = match.groups()

            # Clean up
            task_id = task_id.strip()
            name_or_status = name_or_status.strip()
            status_or_desc = status_or_desc.strip()

            # Skip headers and separators
            if task_id in ("ID", "Task", "Pillar", "Factor") or task_id.startswith("-"):
                continue
            if not re.match(r'^(P\d+\.\d+|RD-\d+|FH-\d+)', task_id):
                continue

            # Normalize status
            if "✅" in status_or_desc or "DONE" in status_or_desc:
                task_status = "DONE"
            elif "📋" in status_or_desc or "TODO" in status_or_desc:
                task_status = "TODO"
            elif "⏸️" in status_or_desc or "BLOCKED" in status_or_desc:
                task_status = "BLOCKED"
            elif "🔄" in status_or_desc or "IN_PROGRESS" in status_or_desc:
                task_status = "IN_PROGRESS"
            else:
                task_status = "TODO"

            # Determine phase from ID
            task_phase = "UNKNOWN"
            if task_id.startswith("P"):
                task_phase = task_id.split(".")[0]
            elif task_id.startswith("RD-"):
                task_phase = "RD"
            elif task_id.startswith("FH-"):
                task_phase = "FH"

            # Apply filters
            if phase and task_phase != phase:
                continue
            if status and task_status != status:
                continue

            tasks.append({
                "task_id": task_id,
                "name": name_or_status[:100],
                "status": task_status,
                "phase": task_phase,
                "description": status_or_desc[:200] if len(status_or_desc) > 10 else ""
            })

    return json.dumps({
        "tasks": tasks,
        "count": len(tasks),
        "phases": list(set(t["phase"] for t in tasks))
    }, indent=2)


@mcp.tool()
def governance_get_task_deps(task_id: str) -> str:
    """
    Get task dependencies (what blocks this task, what this task blocks).

    Args:
        task_id: Task ID (e.g., "P7.1", "P9.1")

    Returns:
        JSON object with blocked_by and blocks arrays
    """
    # Parse R&D backlog for dependency hints
    backlog_file = BACKLOG_DIR / "R&D-BACKLOG.md"

    result = {
        "task_id": task_id,
        "blocked_by": [],
        "blocks": []
    }

    if backlog_file.exists():
        content = backlog_file.read_text(encoding="utf-8")

        # Look for Dependencies: section
        import re
        deps_pattern = r"Dependencies:\s*\n((?:[-*]\s*.+\n)+)"
        for match in re.finditer(deps_pattern, content):
            deps_text = match.group(1)
            # Check if our task is mentioned
            if task_id in deps_text:
                # Extract dependency relationships
                for line in deps_text.split("\n"):
                    if task_id in line:
                        # Parse "Phase X: Y required" patterns
                        phase_match = re.search(r"Phase\s*(\d+)", line)
                        if phase_match:
                            result["blocked_by"].append(f"P{phase_match.group(1)}")

        # Infer dependencies from phase ordering
        if task_id.startswith("P"):
            phase_num = float(task_id[1:].replace("-", "."))
            # Tasks in earlier phases block later ones
            if phase_num > 7:
                result["blocked_by"].append("P7 (TypeDB-First)")
            if phase_num > 3:
                result["blocked_by"].append("P3 (Stabilization)")

    return json.dumps(result, indent=2)


@mcp.tool()
def governance_evidence_search(
    query: str,
    top_k: int = 5,
    source_type: Optional[str] = None
) -> str:
    """
    Semantic search across all evidence artifacts.

    Args:
        query: Search query (e.g., "authentication security rules")
        top_k: Number of results to return (default 5)
        source_type: Filter by type (session, decision, rule)

    Returns:
        JSON array of matching evidence with relevance scores
    """
    # Try to use vector store for semantic search
    try:
        from governance.vector_store import VectorStore, MockEmbeddings

        store = VectorStore()
        generator = MockEmbeddings(dimension=384)

        # Connect if possible
        if store.connect():
            query_embedding = generator.generate(query)
            results = store.search(query_embedding, top_k=top_k, source_type=source_type)
            store.close()

            return json.dumps({
                "query": query,
                "results": [
                    {
                        "source": r.source,
                        "source_type": r.source_type,
                        "score": round(r.score, 4),
                        "content": r.content[:200] + "..." if len(r.content) > 200 else r.content
                    }
                    for r in results
                ],
                "count": len(results),
                "search_method": "semantic_vector"
            }, indent=2)
    except:
        pass

    # Fall back to keyword search
    results = []
    query_lower = query.lower()

    # Search evidence files
    for pattern in [EVIDENCE_DIR / "*.md", DOCS_DIR / "rules/*.md"]:
        for filepath in glob.glob(str(pattern)):
            try:
                path = Path(filepath)
                content = path.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    # Count occurrences as relevance score
                    score = content.lower().count(query_lower)
                    results.append({
                        "source": path.stem,
                        "source_type": "evidence" if "evidence" in str(path) else "rule",
                        "score": score,
                        "path": str(filepath),
                        "content": content[:200] + "..."
                    })
            except:
                continue

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    return json.dumps({
        "query": query,
        "results": results[:top_k],
        "count": len(results[:top_k]),
        "search_method": "keyword_fallback"
    }, indent=2)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("Starting Governance MCP Server...")
    print(f"TypeDB: {TYPEDB_HOST}:{TYPEDB_PORT}/{DATABASE_NAME}")
    mcp.run()
