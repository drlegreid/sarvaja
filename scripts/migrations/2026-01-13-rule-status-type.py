#!/usr/bin/env python3
"""
Migration: Add rule-type field and update status values
Date: 2026-01-13
Per: User request for rule status (ACTIVE/PROPOSED/DISABLED) and rule type

Changes:
1. Add rule-type attribute to schema
2. Update RULE-030 status from ACTIVE to DISABLED
3. Add rule-type to all existing rules
4. Update RULE-035 directive for Podman MCP
"""

from typedb.driver import TypeDB, SessionType, TransactionType

TYPEDB_HOST = "localhost:1729"
DATABASE = "sim-ai-governance"

# Rule type mapping based on rule analysis
RULE_TYPES = {
    # Foundational rules - other rules should depend on these
    "RULE-001": "FOUNDATIONAL",  # Evidence-Based Governance
    "RULE-003": "FOUNDATIONAL",  # TypeDB-First Architecture
    "RULE-006": "FOUNDATIONAL",  # Signal > Noise
    "RULE-011": "FOUNDATIONAL",  # Multi-Agent Governance

    # Meta rules - about rules themselves
    "RULE-013": "META",  # Rules Applicability Convention

    # Operational rules - day-to-day behaviors
    "RULE-002": "OPERATIONAL",  # Iterative Development
    "RULE-004": "OPERATIONAL",  # Gap-Driven Workflow
    "RULE-005": "OPERATIONAL",  # Living Documentation
    "RULE-007": "OPERATIONAL",  # Human Context Bridge
    "RULE-008": "OPERATIONAL",  # 80% Rewrite Rule
    "RULE-009": "OPERATIONAL",  # Version Evolution
    "RULE-010": "OPERATIONAL",  # Proactive Wisdom Loading
    "RULE-012": "OPERATIONAL",  # DSP Deep Sleep Protocol
    "RULE-014": "OPERATIONAL",  # HALT Command
    "RULE-015": "OPERATIONAL",  # R&D Workflow
    "RULE-018": "OPERATIONAL",  # Semantic Session IDs
    "RULE-020": "OPERATIONAL",  # E2E Test Generation
    "RULE-022": "OPERATIONAL",  # Evidence File Structure
    "RULE-023": "OPERATIONAL",  # Test Before Feature
    "RULE-025": "OPERATIONAL",  # Orchestrator Pattern
    "RULE-027": "OPERATIONAL",  # API Server Restart
    "RULE-028": "OPERATIONAL",  # Change Validation
    "RULE-031": "OPERATIONAL",  # Autonomous Continuation
    "RULE-033": "OPERATIONAL",  # PARTIAL Task Handling
    "RULE-035": "OPERATIONAL",  # Shell Environment (Podman MCP)
    "RULE-037": "OPERATIONAL",  # Fix Validation
    "RULE-041": "OPERATIONAL",  # Crash Investigation
    "RULE-042": "OPERATIONAL",  # Destructive Command Prevention

    # Technical rules - architecture/infrastructure
    "RULE-016": "TECHNICAL",  # Infrastructure Identity
    "RULE-017": "TECHNICAL",  # Cross-Workspace Patterns
    "RULE-019": "TECHNICAL",  # UI/UX Standards
    "RULE-021": "TECHNICAL",  # MCP Healthcheck
    "RULE-024": "TECHNICAL",  # AMNESIA Protocol
    "RULE-026": "TECHNICAL",  # Decision Context
    "RULE-029": "TECHNICAL",  # Executive Reporting
    "RULE-032": "TECHNICAL",  # File Size Standards
    "RULE-034": "TECHNICAL",  # Relative Linking
    "RULE-036": "TECHNICAL",  # MCP Separation
    "RULE-040": "TECHNICAL",  # Portable Config

    # Leaf/Disabled rules
    "RULE-030": "LEAF",  # Docker (DISABLED - use Podman)
}

def run_migration():
    """Execute the migration."""
    print("=== Migration: Rule Status & Type Update ===")
    print(f"Connecting to TypeDB at {TYPEDB_HOST}...")

    with TypeDB.core_driver(TYPEDB_HOST) as driver:
        # Check if database exists
        if not driver.databases.contains(DATABASE):
            print(f"ERROR: Database '{DATABASE}' not found!")
            return False

        # Step 1: Update schema to add rule-type
        print("\n[1/4] Checking schema for rule-type attribute...")
        with driver.session(DATABASE, SessionType.SCHEMA) as session:
            with session.transaction(TransactionType.READ) as tx:
                # Check if rule-type already exists
                result = tx.query.get("match $t type rule-type; get $t;")
                has_rule_type = list(result)

            if not has_rule_type:
                print("  Adding rule-type attribute to schema...")
                with session.transaction(TransactionType.WRITE) as tx:
                    tx.query.define("""
                        define
                        rule-type sub attribute, value string;
                        rule-entity owns rule-type;
                    """)
                    tx.commit()
                print("  Schema updated!")
            else:
                print("  rule-type attribute already exists")

        # Step 2: Update RULE-030 status to DISABLED
        print("\n[2/4] Updating RULE-030 status to DISABLED...")
        with driver.session(DATABASE, SessionType.DATA) as session:
            with session.transaction(TransactionType.WRITE) as tx:
                tx.query.delete("""
                    match
                    $r isa rule-entity, has rule-id "RULE-030", has status $s;
                    delete $r has $s;
                """)
                tx.query.insert("""
                    match
                    $r isa rule-entity, has rule-id "RULE-030";
                    insert $r has status "DISABLED";
                """)
                tx.commit()
            print("  RULE-030 status updated to DISABLED")

        # Step 3: Add rule-type to all rules
        print("\n[3/4] Adding rule-type to existing rules...")
        with driver.session(DATABASE, SessionType.DATA) as session:
            for rule_id, rule_type in RULE_TYPES.items():
                with session.transaction(TransactionType.WRITE) as tx:
                    # Check if rule exists and doesn't have type
                    result = tx.query.get(f"""
                        match
                        $r isa rule-entity, has rule-id "{rule_id}";
                        not {{ $r has rule-type $t; }};
                        get $r;
                    """)
                    rules = list(result)

                    if rules:
                        tx.query.insert(f"""
                            match
                            $r isa rule-entity, has rule-id "{rule_id}";
                            insert $r has rule-type "{rule_type}";
                        """)
                        tx.commit()
                        print(f"  {rule_id}: {rule_type}")
                    else:
                        print(f"  {rule_id}: already has type (skipped)")

        # Step 4: Update RULE-035 directive
        print("\n[4/4] Updating RULE-035 directive for Podman MCP...")
        new_directive = "Agents MUST use Podman MCP tools for container operations. Fallback to shell commands ONLY when Podman MCP is unavailable."
        with driver.session(DATABASE, SessionType.DATA) as session:
            with session.transaction(TransactionType.WRITE) as tx:
                tx.query.delete("""
                    match
                    $r isa rule-entity, has rule-id "RULE-035", has directive $d;
                    delete $r has $d;
                """)
                tx.query.insert(f"""
                    match
                    $r isa rule-entity, has rule-id "RULE-035";
                    insert $r has directive "{new_directive}";
                """)
                tx.commit()
            print("  RULE-035 directive updated")

        print("\n=== Migration Complete ===")
        return True

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
