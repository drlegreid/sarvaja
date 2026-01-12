"""
Data Integrity Schemas
Created: P10.7
Modularized: 2026-01-02 (RULE-032)

TypeDB entity schemas, valid values, and relation schemas.
"""

# Required fields per entity type (from TypeDB schema)
ENTITY_SCHEMAS = {
    "rule": {
        "required": ["rule-id", "rule-name", "category", "priority", "status", "directive"],
        "optional": ["created-date"],
        "id_pattern": r"^RULE-\d{3}$"
    },
    "decision": {
        "required": ["decision-id", "decision-name", "context", "rationale"],
        "optional": ["decision-status", "decision-date"],
        "id_pattern": r"^DECISION-\d{3}$"
    },
    "task": {
        "required": ["task-id", "task-name", "task-status"],
        "optional": ["task-body", "phase", "gap-reference"],
        "id_pattern": r"^(P\d+\.\d+|RD-\d{3}|ORCH-\d{3}|TEST-\d{3}|FH-\d{3}|TOOL-\d{3}|DOC-\d{3})$"
    },
    "gap": {
        "required": ["gap-id", "gap-name", "gap-status", "severity"],
        "optional": ["location"],
        "id_pattern": r"^GAP-[A-Z]+-\d{3}$"
    },
    "agent": {
        "required": ["agent-id", "agent-name", "agent-type"],
        "optional": ["trust-score", "compliance-rate", "accuracy-rate", "tenure-days"],
        "id_pattern": r"^(AGENT-\d{3}|TEST-AGENT-\d{3})$"
    },
    "session": {
        "required": ["session-id"],
        "optional": ["session-name", "session-description", "session-file-path", "started-at", "completed-at"],
        "id_pattern": r"^SESSION-\d{4}-\d{2}-\d{2}-.*$"
    }
}

# Valid values for enum-like attributes
VALID_VALUES = {
    "priority": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
    "status": ["ACTIVE", "DRAFT", "DEPRECATED"],
    "decision-status": ["APPROVED", "PENDING", "SUPERSEDED"],
    "task-status": ["TODO", "IN_PROGRESS", "DONE", "BLOCKED", "pending", "in_progress", "completed"],
    "gap-status": ["OPEN", "RESOLVED", "DEFERRED", "PARTIAL"],
    "severity": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
    "agent-type": ["claude-code", "docker-agent", "sync-agent", "test-agent"]
}

# Relation schemas (P10.7 typed references)
RELATION_SCHEMAS = {
    "references-gap": {
        "roles": ["referencing-task", "referenced-gap"],
        "required_entities": ["task", "gap"]
    },
    "task-outcome": {
        "roles": ["outcome-decision", "source-task"],
        "attributes": ["has-authority"],
        "required_entities": ["decision", "task"]
    },
    "implements-rule": {
        "roles": ["implementing-task", "implemented-rule"],
        "required_entities": ["task", "rule"]
    },
    "completed-in": {
        "roles": ["completed-task", "hosting-session"],
        "required_entities": ["task", "session"]
    },
    "decision-affects": {
        "roles": ["affecting-decision", "affected-rule"],
        "required_entities": ["decision", "rule"]
    }
}
