*** Settings ***
Documentation    RF-004: Unit Tests - DSM Tracker Module
...              Migrated from tests/test_dsm_tracker_unit.py
...              Per RULE-012: Deep Sleep Protocol (DSP) governance
Library          Collections
Library          ../../libs/DSMTrackerLibrary.py

Suite Setup      Setup DSM Test Environment
Suite Teardown   Cleanup DSM Test Environment

*** Keywords ***
Setup DSM Test Environment
    [Documentation]    Create temp directory for tests
    ${tmpdir}=    Create Temp Directory
    Set Suite Variable    ${TMPDIR}    ${tmpdir}
    Reset Global Tracker

Cleanup DSM Test Environment
    [Documentation]    Clean up temp directory
    Reset Global Tracker
    Cleanup Temp Directory

*** Test Cases ***
# =============================================================================
# DSPPhase Enum Tests
# =============================================================================

DSPPhase Enum Exists
    [Documentation]    DSPPhase enum exists and is importable
    [Tags]    unit    sessions    validate    dsm
    ${exists}=    Dsp Phase Exists
    Should Be True    ${exists}

DSPPhase IDLE Value Is Lowercase
    [Documentation]    DSPPhase.IDLE.value == "idle"
    [Tags]    unit    sessions    validate    dsm
    ${value}=    Get Dsp Phase Value    IDLE
    Should Be Equal    ${value}    idle

DSPPhase AUDIT Value Is Lowercase
    [Documentation]    DSPPhase.AUDIT.value == "audit"
    [Tags]    unit    sessions    validate    dsm
    ${value}=    Get Dsp Phase Value    AUDIT
    Should Be Equal    ${value}    audit

DSPPhase HYPOTHESIZE Value Is Lowercase
    [Documentation]    DSPPhase.HYPOTHESIZE.value == "hypothesize"
    [Tags]    unit    sessions    validate    dsm
    ${value}=    Get Dsp Phase Value    HYPOTHESIZE
    Should Be Equal    ${value}    hypothesize

DSPPhase MEASURE Value Is Lowercase
    [Documentation]    DSPPhase.MEASURE.value == "measure"
    [Tags]    unit    sessions    validate    dsm
    ${value}=    Get Dsp Phase Value    MEASURE
    Should Be Equal    ${value}    measure

Phase Order Returns List Of Seven
    [Documentation]    phase_order returns list of 7 active phases
    [Tags]    unit    sessions    validate    dsm
    ${order}=    Get Phase Order
    ${length}=    Get Length    ${order}
    Should Be Equal As Integers    ${length}    7

Phase Order Starts With Audit
    [Documentation]    First phase in order is audit
    [Tags]    unit    sessions    validate    dsm
    ${order}=    Get Phase Order
    ${first}=    Get From List    ${order}    0
    Should Be Equal    ${first}    audit

Phase Order Excludes Idle
    [Documentation]    IDLE is not in phase order
    [Tags]    unit    sessions    validate    dsm
    ${order}=    Get Phase Order
    List Should Not Contain Value    ${order}    idle

# =============================================================================
# Phase Required MCPs Tests
# =============================================================================

Audit Phase Requires Claude Mem
    [Documentation]    AUDIT phase requires claude-mem MCP
    [Tags]    unit    sessions    mcp    dsm
    ${mcps}=    Get Phase Required Mcps    AUDIT
    List Should Contain Value    ${mcps}    claude-mem

Audit Phase Requires Governance
    [Documentation]    AUDIT phase requires governance MCP
    [Tags]    unit    sessions    mcp    dsm
    ${mcps}=    Get Phase Required Mcps    AUDIT
    List Should Contain Value    ${mcps}    governance

Hypothesize Phase Requires Sequential Thinking
    [Documentation]    HYPOTHESIZE phase requires sequential-thinking MCP
    [Tags]    unit    sessions    mcp    dsm
    ${mcps}=    Get Phase Required Mcps    HYPOTHESIZE
    List Should Contain Value    ${mcps}    sequential-thinking

Validate Phase Requires Pytest
    [Documentation]    VALIDATE phase requires pytest MCP
    [Tags]    unit    sessions    mcp    dsm
    ${mcps}=    Get Phase Required Mcps    VALIDATE
    List Should Contain Value    ${mcps}    pytest

Idle Phase Has No Required MCPs
    [Documentation]    IDLE phase has empty required MCPs
    [Tags]    unit    sessions    mcp    dsm
    ${mcps}=    Get Phase Required Mcps    IDLE
    ${length}=    Get Length    ${mcps}
    Should Be Equal As Integers    ${length}    0

# =============================================================================
# PhaseCheckpoint Tests
# =============================================================================

Checkpoint Creation With Required Fields
    [Documentation]    PhaseCheckpoint creates with required fields
    [Tags]    unit    sessions    create    dsm
    ${cp}=    Create Phase Checkpoint    audit    2024-12-24T12:00:00    Audited 5 modules
    Should Be Equal    ${cp}[phase]    audit
    Should Be Equal    ${cp}[timestamp]    2024-12-24T12:00:00
    Should Be Equal    ${cp}[description]    Audited 5 modules

Checkpoint Has Default Empty Metrics
    [Documentation]    PhaseCheckpoint has default empty metrics
    [Tags]    unit    sessions    validate    dsm
    ${cp}=    Create Phase Checkpoint    audit    2024-12-24T12:00:00    Test
    ${metrics}=    Get From Dictionary    ${cp}    metrics
    ${length}=    Get Length    ${metrics}
    Should Be Equal As Integers    ${length}    0

Checkpoint Has Default Empty Evidence
    [Documentation]    PhaseCheckpoint has default empty evidence list
    [Tags]    unit    sessions    validate    dsm
    ${cp}=    Create Phase Checkpoint    audit    2024-12-24T12:00:00    Test
    ${evidence}=    Get From Dictionary    ${cp}    evidence
    Should Be Empty    ${evidence}

Checkpoint With Metrics And Evidence
    [Documentation]    PhaseCheckpoint accepts metrics and evidence
    [Tags]    unit    sessions    create    dsm
    &{metrics}=    Create Dictionary    latency_ms=15    throughput=100
    @{evidence}=    Create List    benchmark.log    perf_report.md
    ${cp}=    Create Phase Checkpoint    measure    2024-12-24T12:00:00    Measured performance    ${metrics}    ${evidence}
    Should Be Equal As Integers    ${cp}[metrics][latency_ms]    15
    ${ev_length}=    Get Length    ${cp}[evidence]
    Should Be Equal As Integers    ${ev_length}    2

# =============================================================================
# DSMCycle Tests
# =============================================================================

DSMCycle Creation With ID
    [Documentation]    DSMCycle creates with cycle_id
    [Tags]    unit    sessions    create    dsm
    ${cycle}=    Create Dsm Cycle    DSM-2024-12-24-120000
    Should Be Equal    ${cycle}[cycle_id]    DSM-2024-12-24-120000
    Should Be Equal    ${cycle}[current_phase]    idle

DSMCycle Has Default Empty Lists
    [Documentation]    DSMCycle has default empty lists
    [Tags]    unit    sessions    validate    dsm
    ${cycle}=    Create Dsm Cycle    TEST-001
    Should Be Empty    ${cycle}[phases_completed]
    Should Be Empty    ${cycle}[checkpoints]
    Should Be Empty    ${cycle}[findings]

DSMCycle To Dict Returns Dict
    [Documentation]    DSMCycle.to_dict returns dictionary
    [Tags]    unit    sessions    serialize    dsm
    ${cycle}=    Create Dsm Cycle    TEST-001    batch_id=1001-1100    current_phase=audit
    Should Be Equal    ${cycle}[cycle_id]    TEST-001
    Should Be Equal    ${cycle}[batch_id]    1001-1100
    Should Be Equal    ${cycle}[current_phase]    audit

# =============================================================================
# DSMTracker Initialization Tests
# =============================================================================

Tracker Creates With Defaults
    [Documentation]    DSMTracker creates with default paths
    [Tags]    unit    sessions    create    dsm
    ${created}=    Create Dsm Tracker    ${TMPDIR}
    Should Be True    ${created}

Tracker Starts With No Active Cycle
    [Documentation]    DSMTracker starts with no active cycle
    [Tags]    unit    sessions    validate    dsm
    Create Dsm Tracker    ${TMPDIR}
    ${no_cycle}=    Tracker Has No Active Cycle
    Should Be True    ${no_cycle}

Tracker Status Shows Inactive
    [Documentation]    New tracker status shows active=False
    [Tags]    unit    sessions    validate    dsm
    Create Dsm Tracker    ${TMPDIR}
    ${status}=    Get Tracker Status
    Should Not Be True    ${status}[active]

# =============================================================================
# DSMTracker Serialization Tests
# =============================================================================

Tracker To Dict Returns Dict
    [Documentation]    to_dict returns dictionary
    [Tags]    unit    sessions    serialize    dsm
    Create Dsm Tracker    ${TMPDIR}
    ${d}=    Tracker To Dict
    Dictionary Should Contain Key    ${d}    current_cycle
    Dictionary Should Contain Key    ${d}    completed_cycles_count

Tracker To JSON Returns Valid JSON
    [Documentation]    to_json returns valid JSON string
    [Tags]    unit    sessions    serialize    dsm
    Create Dsm Tracker    ${TMPDIR}
    ${json_str}=    Tracker To Json
    ${length}=    Get Length    ${json_str}
    Should Be True    ${length} > 0

# =============================================================================
# Global Tracker Function Tests
# =============================================================================

Get Tracker Returns Tracker Instance
    [Documentation]    get_tracker returns DSMTracker instance
    [Tags]    unit    sessions    validate    dsm
    Reset Global Tracker
    ${is_tracker}=    Get Global Tracker    ${TMPDIR}
    Should Be True    ${is_tracker}
    Reset Global Tracker

Get Tracker Returns Same Instance
    [Documentation]    get_tracker returns same instance on multiple calls
    [Tags]    unit    sessions    validate    dsm
    Reset Global Tracker
    ${same}=    Global Trackers Are Same Instance
    Should Be True    ${same}
    Reset Global Tracker

Reset Tracker Creates New Instance
    [Documentation]    reset_tracker clears and creates new instance
    [Tags]    unit    sessions    validate    dsm
    Reset Global Tracker
    ${different}=    Global Trackers Are Different After Reset
    Should Be True    ${different}

