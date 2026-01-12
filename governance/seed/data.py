"""
Seed Data Definitions
Created: 2024-12-28
Modularized: 2026-01-02 (RULE-032)

Initial seed data for tasks, sessions, and agents.
"""


def get_seed_tasks():
    """Get seed task data. Shared between TypeDB and in-memory seeding."""
    return [
        # Phase 3: Stabilization
        {"task_id": "P3.1", "description": "Hybrid query router (TypeDB + ChromaDB)", "phase": "P3", "status": "DONE",
         "body": "Implement router that dispatches queries to TypeDB for structured data and ChromaDB for semantic search.",
         "linked_rules": ["RULE-007"], "created_at": "2024-12-23T09:00:00"},
        {"task_id": "P3.5", "description": "Performance benchmarks (governance/benchmark.py)", "phase": "P3", "status": "DONE",
         "body": "Create benchmark suite for TypeDB query performance.",
         "linked_rules": ["RULE-009"], "created_at": "2024-12-24T10:00:00"},

        # Phase 4: Cross-Workspace Integration
        {"task_id": "P4.1", "description": "MCP -> Agno @tool wrapping", "phase": "P4", "status": "DONE",
         "body": "Wrap MCP server tools as Agno @tool decorators for seamless integration.",
         "linked_rules": ["RULE-007"], "created_at": "2024-12-24T08:00:00"},
        {"task_id": "P4.2", "description": "Session Evidence Collection via MCP", "phase": "P4", "status": "DONE",
         "body": "Implement SessionCollector MCP tool for gathering session artifacts.",
         "linked_rules": ["RULE-001", "RULE-012"], "created_at": "2024-12-24T10:00:00"},

        # Phase 9: Agentic Platform UI/MCP
        {"task_id": "P9.1", "description": "Task/Session/Evidence MCP Tools", "phase": "P9", "status": "DONE",
         "body": "7 MCP tools for artifact viewing.",
         "linked_rules": ["RULE-007", "RULE-001"], "created_at": "2024-12-25T08:00:00"},
        {"task_id": "P9.2", "description": "Governance Dashboard UI (Trame-based)", "phase": "P9", "status": "DONE",
         "body": "Build Governance Dashboard with Trame: rules browser, decisions viewer.",
         "linked_rules": ["RULE-019", "RULE-011"], "created_at": "2024-12-25T08:00:00"},

        # Phase 10: Architecture Debt Resolution
        {"task_id": "P10.1", "description": "Tasks -> TypeDB Migration", "phase": "P10", "status": "IN_PROGRESS",
         "body": "Migrate _tasks_store from in-memory dict to TypeDB.",
         "linked_rules": ["RULE-007"], "gap_id": "GAP-ARCH-001", "created_at": "2024-12-26T08:00:00"},
        {"task_id": "P10.2", "description": "Sessions -> TypeDB Migration", "phase": "P10", "status": "IN_PROGRESS",
         "body": "Migrate _sessions_store to TypeDB.",
         "linked_rules": ["RULE-007"], "gap_id": "GAP-ARCH-002", "created_at": "2024-12-26T08:30:00"},

        # R&D Tasks
        {"task_id": "RD-001", "description": "Haskell MCP Research", "phase": "R&D", "status": "TODO",
         "body": "Research Haskell-based MCP server implementation.",
         "linked_rules": ["RULE-007"], "created_at": "2024-12-26T10:00:00"},

        # Current Sprint Tasks
        {"task_id": "TODO-6", "description": "Agent Task Backlog UI", "phase": "P1", "status": "DONE",
         "body": "Build UI for agent task backlog visualization.",
         "linked_rules": ["RULE-019"], "gap_id": "GAP-005", "created_at": "2024-12-26T08:00:00"},
        {"task_id": "TODO-7", "description": "Sync Agent Implementation", "phase": "P1", "status": "DONE",
         "body": "Implement sync agent skeleton with ChromaDB-TypeDB synchronization.",
         "linked_rules": ["RULE-007"], "gap_id": "GAP-006", "created_at": "2024-12-26T08:00:00"},
    ]


def get_seed_sessions():
    """Get seed session data. Shared between TypeDB and in-memory seeding."""
    return [
        {
            "session_id": "SESSION-2024-12-24-001",
            "start_time": "2024-12-24T09:00:00",
            "end_time": "2024-12-24T18:00:00",
            "status": "COMPLETED",
            "tasks_completed": 5,
            "description": "Phase 3-4: Stabilization and Cross-Workspace Integration",
            "linked_rules_applied": ["RULE-001", "RULE-007", "RULE-012"],
            "linked_decisions": ["DECISION-001"],
            "evidence_files": [
                "evidence/DECISION-001-Opik-Removal.md",
                "evidence/SESSION-2024-12-24-PHASE-3-4.md"
            ],
        },
        {
            "session_id": "SESSION-2024-12-25-001",
            "start_time": "2024-12-25T08:00:00",
            "end_time": "2024-12-25T22:00:00",
            "status": "COMPLETED",
            "tasks_completed": 12,
            "description": "Phase 9: Governance Dashboard UI + Agent Trust Dashboard",
            "linked_rules_applied": ["RULE-011", "RULE-019", "RULE-020"],
            "linked_decisions": ["DECISION-003"],
            "evidence_files": [
                "evidence/DECISION-003-TypeDB-First.md",
                "evidence/SESSION-2024-12-25-PHASE-9.md"
            ],
        },
        {
            "session_id": "SESSION-2024-12-26-001",
            "start_time": "2024-12-26T08:00:00",
            "status": "ACTIVE",
            "tasks_completed": 8,
            "description": "Phase 10-11: REST API, CRUD fixes, Data Integrity Resolution",
            "linked_rules_applied": ["RULE-001", "RULE-007", "RULE-019"],
            "evidence_files": [
                "evidence/SESSION-2024-12-26-PHASE-10-11.md"
            ],
        },
        {
            "session_id": "SESSION-2024-12-28-001",
            "start_time": "2024-12-28T08:00:00",
            "status": "ACTIVE",
            "tasks_completed": 5,
            "description": "Phase 10: TypeDB-First Migration + GAP-FILE Resolution",
            "linked_rules_applied": ["RULE-007", "RULE-012", "RULE-030"],
            "evidence_files": [
                "evidence/SESSION-2024-12-28-PHASE-10.md",
                "docs/gaps/GAP-INDEX.md"
            ],
        },
    ]


def get_seed_agents():
    """
    Get seed agent data. Shared between TypeDB and in-memory seeding.

    Per P10.3: Base agent definitions for TypeDB-first migration.
    """
    return [
        {"agent_id": "task-orchestrator", "name": "Task Orchestrator", "agent_type": "orchestrator", "base_trust": 0.95},
        {"agent_id": "rules-curator", "name": "Rules Curator", "agent_type": "curator", "base_trust": 0.90},
        {"agent_id": "research-agent", "name": "Research Agent", "agent_type": "researcher", "base_trust": 0.85},
        {"agent_id": "code-agent", "name": "Code Agent", "agent_type": "coder", "base_trust": 0.88},
        {"agent_id": "local-assistant", "name": "Local Assistant", "agent_type": "assistant", "base_trust": 0.92},
    ]
