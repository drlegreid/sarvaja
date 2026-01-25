*** Settings ***
Documentation    RF-004: Unit Tests - DSM Tracker Phase Transitions
...              Migrated from tests/test_dsm_tracker_phases.py
...              Per RULE-012: Deep Sleep Protocol
Library          Collections
Library          ../../libs/DSMTrackerPhasesLibrary.py

*** Test Cases ***
# =============================================================================
# Phase Navigation Tests
# =============================================================================

Next Phase From Idle Returns Audit
    [Documentation]    GIVEN IDLE phase WHEN next_phase THEN AUDIT
    [Tags]    unit    dsm    phase    navigation
    ${result}=    Next Phase From Idle Returns Audit
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_audit]

Next Phase Through Sequence
    [Documentation]    GIVEN phase WHEN next_phase THEN correct sequence
    [Tags]    unit    dsm    phase    sequence
    ${result}=    Next Phase Through Sequence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[all_correct]

Next Phase From Complete Is None
    [Documentation]    GIVEN COMPLETE phase WHEN next_phase THEN None
    [Tags]    unit    dsm    phase    terminal
    ${result}=    Next Phase From Complete Is None
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_none]

Prev Phase From Audit Returns Idle
    [Documentation]    GIVEN AUDIT phase WHEN prev_phase THEN IDLE
    [Tags]    unit    dsm    phase    navigation
    ${result}=    Prev Phase From Audit Returns Idle
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_idle]

Prev Phase Through Sequence
    [Documentation]    GIVEN phase WHEN prev_phase THEN correct sequence
    [Tags]    unit    dsm    phase    sequence
    ${result}=    Prev Phase Through Sequence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[all_correct]

# =============================================================================
# Cycle Lifecycle Tests
# =============================================================================

Start Cycle Creates Cycle
    [Documentation]    GIVEN tracker WHEN start_cycle THEN cycle created
    [Tags]    unit    dsm    cycle    create
    ${result}=    Start Cycle Creates Cycle
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_none]
    Should Be True    ${result}[has_dsm_prefix]
    Should Be True    ${result}[batch_correct]
    Should Be True    ${result}[phase_idle]

Start Cycle Sets Start Time
    [Documentation]    GIVEN tracker WHEN start_cycle THEN start_time set
    [Tags]    unit    dsm    cycle    timestamp
    ${result}=    Start Cycle Sets Start Time
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_start_time]

Start Cycle While In Progress Raises
    [Documentation]    GIVEN active cycle WHEN start_cycle THEN ValueError
    [Tags]    unit    dsm    cycle    error
    ${result}=    Start Cycle While In Progress Raises
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[raises]
    Should Be True    ${result}[message_correct]

Complete Cycle Sets End Time
    [Documentation]    GIVEN cycle WHEN complete_cycle THEN end_time set
    [Tags]    unit    dsm    cycle    complete
    ${result}=    Complete Cycle Sets End Time
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_completed]
    Should Be True    ${result}[has_end_time]

Complete Cycle Clears Current
    [Documentation]    GIVEN cycle WHEN complete_cycle THEN current cleared
    [Tags]    unit    dsm    cycle    complete
    ${result}=    Complete Cycle Clears Current
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[cleared]

Complete Cycle Generates Evidence File
    [Documentation]    GIVEN cycle WHEN complete_cycle THEN evidence file
    [Tags]    unit    dsm    cycle    evidence
    ${result}=    Complete Cycle Generates Evidence File
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[is_md]

# =============================================================================
# Phase Transition Tests
# =============================================================================

Advance Phase From Idle To Audit
    [Documentation]    GIVEN IDLE WHEN advance_phase THEN AUDIT
    [Tags]    unit    dsm    transition    advance
    ${result}=    Advance Phase From Idle To Audit
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_audit]
    Should Be True    ${result}[current_audit]

Advance Phase Records Completed
    [Documentation]    GIVEN phase WHEN advance_phase THEN records completed
    [Tags]    unit    dsm    transition    record
    ${result}=    Advance Phase Records Completed
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[audit_completed]

Advance Phase No Cycle Raises
    [Documentation]    GIVEN no cycle WHEN advance_phase THEN ValueError
    [Tags]    unit    dsm    transition    error
    ${result}=    Advance Phase No Cycle Raises
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[raises]
    Should Be True    ${result}[message_correct]

Go To Phase Jumps Directly
    [Documentation]    GIVEN cycle WHEN go_to_phase THEN direct jump
    [Tags]    unit    dsm    transition    jump
    ${result}=    Go To Phase Jumps Directly
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_validate]

Go To Phase Idle Raises
    [Documentation]    GIVEN cycle WHEN go_to_phase(IDLE) THEN ValueError
    [Tags]    unit    dsm    transition    error
    ${result}=    Go To Phase Idle Raises
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[raises]
    Should Be True    ${result}[message_correct]

# =============================================================================
# Checkpoint Tests
# =============================================================================

Checkpoint Creates Checkpoint
    [Documentation]    GIVEN cycle WHEN checkpoint THEN checkpoint created
    [Tags]    unit    dsm    checkpoint    create
    ${result}=    Checkpoint Creates Checkpoint
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[phase_audit]
    Should Be True    ${result}[description_correct]
    Should Be True    ${result}[added_to_list]

Checkpoint With Metrics
    [Documentation]    GIVEN cycle WHEN checkpoint with metrics THEN recorded
    [Tags]    unit    dsm    checkpoint    metrics
    ${result}=    Checkpoint With Metrics
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_metrics]

Checkpoint With Evidence
    [Documentation]    GIVEN cycle WHEN checkpoint with evidence THEN recorded
    [Tags]    unit    dsm    checkpoint    evidence
    ${result}=    Checkpoint With Evidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[evidence_count]

Checkpoint No Cycle Raises
    [Documentation]    GIVEN no cycle WHEN checkpoint THEN ValueError
    [Tags]    unit    dsm    checkpoint    error
    ${result}=    Checkpoint No Cycle Raises
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[raises]
    Should Be True    ${result}[message_correct]

# =============================================================================
# Finding Tests
# =============================================================================

Add Finding Creates Finding
    [Documentation]    GIVEN cycle WHEN add_finding THEN finding created
    [Tags]    unit    dsm    finding    create
    ${result}=    Add Finding Creates Finding
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[type_gap]
    Should Be True    ${result}[description_correct]
    Should Be True    ${result}[added_to_list]

Add Finding Assigns Sequential Id
    [Documentation]    GIVEN cycle WHEN add_finding twice THEN sequential IDs
    [Tags]    unit    dsm    finding    id
    ${result}=    Add Finding Assigns Sequential Id
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[first_id]
    Should Be True    ${result}[second_id]

Add Finding With Severity
    [Documentation]    GIVEN cycle WHEN add_finding with severity THEN recorded
    [Tags]    unit    dsm    finding    severity
    ${result}=    Add Finding With Severity
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[severity_correct]

Add Finding With Related Rules
    [Documentation]    GIVEN cycle WHEN add_finding with rules THEN recorded
    [Tags]    unit    dsm    finding    rules
    ${result}=    Add Finding With Related Rules
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_rule_001]
    Should Be True    ${result}[has_rule_012]

# =============================================================================
# Abort Cycle Tests
# =============================================================================

Abort Cycle Clears Current
    [Documentation]    GIVEN cycle WHEN abort_cycle THEN current cleared
    [Tags]    unit    dsm    abort    clear
    ${result}=    Abort Cycle Clears Current
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[cleared]

Abort Cycle Without Cycle Is Safe
    [Documentation]    GIVEN no cycle WHEN abort_cycle THEN no error
    [Tags]    unit    dsm    abort    safe
    ${result}=    Abort Cycle Without Cycle Is Safe
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[no_error]

# =============================================================================
# Status Tests
# =============================================================================

Get Status When Idle
    [Documentation]    GIVEN no cycle WHEN get_status THEN not active
    [Tags]    unit    dsm    status    idle
    ${result}=    Get Status When Idle
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_active]
    Should Be True    ${result}[has_message]

Get Status When Active
    [Documentation]    GIVEN active cycle WHEN get_status THEN active
    [Tags]    unit    dsm    status    active
    ${result}=    Get Status When Active
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_active]
    Should Be True    ${result}[batch_correct]
    Should Be True    ${result}[phase_correct]
    Should Be True    ${result}[has_progress]

Get Status Includes Required MCPs
    [Documentation]    GIVEN audit phase WHEN get_status THEN has MCPs
    [Tags]    unit    dsm    status    mcp
    ${result}=    Get Status Includes Required MCPs
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_claude_mem]
    Should Be True    ${result}[has_governance]
