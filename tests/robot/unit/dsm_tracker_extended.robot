*** Settings ***
Documentation    RF-004: DSM Tracker Extended Tests (Cycles, Findings, Integration, Navigation)
...              Migrated from test_dsm_tracker_integration.py
...              Per RF-007 Robot Framework Migration
Library          ../../libs/DSMTrackerCycleLibrary.py
Library          ../../libs/DSMTrackerFindingLibrary.py
Library          ../../libs/DSMTrackerPhaseNavLibrary.py
Library          ../../libs/DSMTrackerIntegrationComplianceLibrary.py
Library          ../../libs/DSMTrackerIntegrationEvidenceLibrary.py
Library          ../../libs/DSMTrackerIntegrationMCPLibrary.py
Library          ../../libs/DSMTrackerIntegrationStateLibrary.py
Library          ../../libs/DSMTrackerIntegrationWorkflowLibrary.py
Library          Collections
Resource         ../resources/common.resource
Force Tags             unit    dsm    extended    sessions    low    session    validate    SESSION-DSM-01-v1

*** Test Cases ***
# =============================================================================
# Cycle Lifecycle Tests
# =============================================================================

Start Cycle Creates Cycle
    [Documentation]    Test: Start Cycle Creates Cycle
    ${result}=    Start Cycle Creates Cycle
    Skip If Import Failed    ${result}

Start Cycle Sets Start Time
    [Documentation]    Test: Start Cycle Sets Start Time
    ${result}=    Start Cycle Sets Start Time
    Skip If Import Failed    ${result}

Start Cycle While In Progress Raises
    [Documentation]    Test: Start Cycle While In Progress Raises
    ${result}=    Start Cycle While In Progress Raises
    Skip If Import Failed    ${result}

Complete Cycle Sets End Time
    [Documentation]    Test: Complete Cycle Sets End Time
    ${result}=    Complete Cycle Sets End Time
    Skip If Import Failed    ${result}

Complete Cycle Clears Current
    [Documentation]    Test: Complete Cycle Clears Current
    ${result}=    Complete Cycle Clears Current
    Skip If Import Failed    ${result}

Complete Cycle Generates Evidence File
    [Documentation]    Test: Complete Cycle Generates Evidence File
    ${result}=    Complete Cycle Generates Evidence File
    Skip If Import Failed    ${result}

Checkpoint Creates Checkpoint
    [Documentation]    Test: Checkpoint Creates Checkpoint
    ${result}=    Checkpoint Creates Checkpoint
    Skip If Import Failed    ${result}

Checkpoint With Metrics
    [Documentation]    Test: Checkpoint With Metrics
    ${result}=    Checkpoint With Metrics
    Skip If Import Failed    ${result}

Checkpoint With Evidence
    [Documentation]    Test: Checkpoint With Evidence
    ${result}=    Checkpoint With Evidence
    Skip If Import Failed    ${result}

Checkpoint No Cycle Raises
    [Documentation]    Test: Checkpoint No Cycle Raises
    ${result}=    Checkpoint No Cycle Raises
    Skip If Import Failed    ${result}

Abort Cycle Clears Current
    [Documentation]    Test: Abort Cycle Clears Current
    ${result}=    Abort Cycle Clears Current
    Skip If Import Failed    ${result}

Abort Cycle Without Cycle Is Safe
    [Documentation]    Test: Abort Cycle Without Cycle Is Safe
    ${result}=    Abort Cycle Without Cycle Is Safe
    Skip If Import Failed    ${result}

# =============================================================================
# Finding Tests
# =============================================================================

Add Finding Creates Finding
    [Documentation]    Test: Add Finding Creates Finding
    ${result}=    Add Finding Creates Finding
    Skip If Import Failed    ${result}

Add Finding Assigns Sequential Id
    [Documentation]    Test: Add Finding Assigns Sequential Id
    ${result}=    Add Finding Assigns Sequential Id
    Skip If Import Failed    ${result}

Add Finding With Severity
    [Documentation]    Test: Add Finding With Severity
    ${result}=    Add Finding With Severity
    Skip If Import Failed    ${result}

Add Finding With Related Rules
    [Documentation]    Test: Add Finding With Related Rules
    ${result}=    Add Finding With Related Rules
    Skip If Import Failed    ${result}

Get Status When Idle
    [Documentation]    Test: Get Status When Idle
    ${result}=    Get Status When Idle
    Skip If Import Failed    ${result}

Get Status When Active
    [Documentation]    Test: Get Status When Active
    ${result}=    Get Status When Active
    Skip If Import Failed    ${result}

Get Status Includes Required MCPs
    [Documentation]    Test: Get Status Includes Required MCPs
    ${result}=    Get Status Includes Required MCPs
    Skip If Import Failed    ${result}

# =============================================================================
# Phase Navigation Tests
# =============================================================================

Next Phase From Idle Returns Audit
    [Documentation]    Test: Next Phase From Idle Returns Audit
    ${result}=    Next Phase From Idle Returns Audit
    Skip If Import Failed    ${result}

Next Phase Through Sequence
    [Documentation]    Test: Next Phase Through Sequence
    ${result}=    Next Phase Through Sequence
    Skip If Import Failed    ${result}

Next Phase From Complete Is None
    [Documentation]    Test: Next Phase From Complete Is None
    ${result}=    Next Phase From Complete Is None
    Skip If Import Failed    ${result}

Prev Phase From Audit Returns Idle
    [Documentation]    Test: Prev Phase From Audit Returns Idle
    ${result}=    Prev Phase From Audit Returns Idle
    Skip If Import Failed    ${result}

Prev Phase Through Sequence
    [Documentation]    Test: Prev Phase Through Sequence
    ${result}=    Prev Phase Through Sequence
    Skip If Import Failed    ${result}

Advance Phase From Idle To Audit
    [Documentation]    Test: Advance Phase From Idle To Audit
    ${result}=    Advance Phase From Idle To Audit
    Skip If Import Failed    ${result}

Advance Phase Records Completed
    [Documentation]    Test: Advance Phase Records Completed
    ${result}=    Advance Phase Records Completed
    Skip If Import Failed    ${result}

Advance Phase No Cycle Raises
    [Documentation]    Test: Advance Phase No Cycle Raises
    ${result}=    Advance Phase No Cycle Raises
    Skip If Import Failed    ${result}

Go To Phase Jumps Directly
    [Documentation]    Test: Go To Phase Jumps Directly
    ${result}=    Go To Phase Jumps Directly
    Skip If Import Failed    ${result}

Go To Phase Idle Raises
    [Documentation]    Test: Go To Phase Idle Raises
    ${result}=    Go To Phase Idle Raises
    Skip If Import Failed    ${result}

# =============================================================================
# Compliance Integration Tests
# =============================================================================

Phases Match Rule 012
    [Documentation]    Test: Phases Match Rule 012
    ${result}=    Phases Match Rule 012
    Skip If Import Failed    ${result}

Evidence References Rule 012
    [Documentation]    Test: Evidence References Rule 012
    ${result}=    Evidence References Rule 012
    Skip If Import Failed    ${result}

MCPs Per Phase Per Rule 012
    [Documentation]    Test: MCPs Per Phase Per Rule 012
    ${result}=    MCPs Per Phase Per Rule 012
    Skip If Import Failed    ${result}

# =============================================================================
# Evidence Integration Tests
# =============================================================================

Evidence File Created
    [Documentation]    Test: Evidence File Created
    ${result}=    Evidence File Created
    Skip If Import Failed    ${result}

Evidence Contains Summary
    [Documentation]    Test: Evidence Contains Summary
    ${result}=    Evidence Contains Summary
    Skip If Import Failed    ${result}

Evidence Contains Findings
    [Documentation]    Test: Evidence Contains Findings
    ${result}=    Evidence Contains Findings
    Skip If Import Failed    ${result}

Evidence Contains Checkpoints
    [Documentation]    Test: Evidence Contains Checkpoints
    ${result}=    Evidence Contains Checkpoints
    Skip If Import Failed    ${result}

Evidence Contains Metrics
    [Documentation]    Test: Evidence Contains Metrics
    ${result}=    Evidence Contains Metrics
    Skip If Import Failed    ${result}

# =============================================================================
# MCP Integration Tests
# =============================================================================

DSM Start Tool Exists
    [Documentation]    Test: DSM Start Tool Exists
    ${result}=    DSM Start Tool Exists
    Skip If Import Failed    ${result}

DSM Advance Tool Exists
    [Documentation]    Test: DSM Advance Tool Exists
    ${result}=    DSM Advance Tool Exists
    Skip If Import Failed    ${result}

DSM Checkpoint Tool Exists
    [Documentation]    Test: DSM Checkpoint Tool Exists
    ${result}=    DSM Checkpoint Tool Exists
    Skip If Import Failed    ${result}

DSM Status Tool Exists
    [Documentation]    Test: DSM Status Tool Exists
    ${result}=    DSM Status Tool Exists
    Skip If Import Failed    ${result}

DSM Complete Tool Exists
    [Documentation]    Test: DSM Complete Tool Exists
    ${result}=    DSM Complete Tool Exists
    Skip If Import Failed    ${result}

DSM Finding Tool Exists
    [Documentation]    Test: DSM Finding Tool Exists
    ${result}=    DSM Finding Tool Exists
    Skip If Import Failed    ${result}

DSM Metrics Tool Exists
    [Documentation]    Test: DSM Metrics Tool Exists
    ${result}=    DSM Metrics Tool Exists
    Skip If Import Failed    ${result}

DSM Start Returns JSON
    [Documentation]    Test: DSM Start Returns JSON
    ${result}=    DSM Start Returns JSON
    Skip If Import Failed    ${result}

DSM Advance Returns JSON
    [Documentation]    Test: DSM Advance Returns JSON
    ${result}=    DSM Advance Returns JSON
    Skip If Import Failed    ${result}

DSM Status Returns JSON
    [Documentation]    Test: DSM Status Returns JSON
    ${result}=    DSM Status Returns JSON
    Skip If Import Failed    ${result}

DSM Checkpoint Returns JSON
    [Documentation]    Test: DSM Checkpoint Returns JSON
    ${result}=    DSM Checkpoint Returns JSON
    Skip If Import Failed    ${result}

DSM Finding Returns JSON
    [Documentation]    Test: DSM Finding Returns JSON
    ${result}=    DSM Finding Returns JSON
    Skip If Import Failed    ${result}

# =============================================================================
# State Integration Tests
# =============================================================================

State Saved On Start Cycle
    [Documentation]    Test: State Saved On Start Cycle
    ${result}=    State Saved On Start Cycle
    Skip If Import Failed    ${result}

State Saved On Advance Phase
    [Documentation]    Test: State Saved On Advance Phase
    ${result}=    State Saved On Advance Phase
    Skip If Import Failed    ${result}

State Saved On Checkpoint
    [Documentation]    Test: State Saved On Checkpoint
    ${result}=    State Saved On Checkpoint
    Skip If Import Failed    ${result}

State Loaded On Init
    [Documentation]    Test: State Loaded On Init
    ${result}=    State Loaded On Init
    Skip If Import Failed    ${result}

State Cleared On Complete
    [Documentation]    Test: State Cleared On Complete
    ${result}=    State Cleared On Complete
    Skip If Import Failed    ${result}

# =============================================================================
# Workflow Integration Tests
# =============================================================================

Full Cycle Workflow
    [Documentation]    Test: Full Cycle Workflow
    ${result}=    Full Cycle Workflow
    Skip If Import Failed    ${result}

Resume Interrupted Cycle
    [Documentation]    Test: Resume Interrupted Cycle
    ${result}=    Resume Interrupted Cycle
    Skip If Import Failed    ${result}

Update Metrics Adds To Cycle
    [Documentation]    Test: Update Metrics Adds To Cycle
    ${result}=    Update Metrics Adds To Cycle
    Skip If Import Failed    ${result}

Update Metrics Merges With Existing
    [Documentation]    Test: Update Metrics Merges With Existing
    ${result}=    Update Metrics Merges With Existing
    Skip If Import Failed    ${result}

Update Metrics No Cycle Raises
    [Documentation]    Test: Update Metrics No Cycle Raises
    ${result}=    Update Metrics No Cycle Raises
    Skip If Import Failed    ${result}
