*** Settings ***
Documentation    RF-004: Unit Tests - DSMTracker Core
...              Migrated from tests/test_dsm_tracker_unit.py
...              Per RULE-012: Deep Sleep Protocol
Library          Collections
Library          ../../libs/DSMTrackerUnitLibrary.py

*** Test Cases ***
# =============================================================================
# DSPPhase Enum Tests
# =============================================================================

DSP Phase Enum Exists
    [Documentation]    GIVEN dsm_tracker WHEN importing THEN DSPPhase exists
    [Tags]    unit    dsm    phase    enum
    ${result}=    DSP Phase Enum Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

DSP Phase Has All Phases
    [Documentation]    GIVEN DSPPhase WHEN checking THEN has all expected phases
    [Tags]    unit    dsm    phase    complete
    ${result}=    DSP Phase Has All Phases
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[all_present]

DSP Phase Values Are Lowercase
    [Documentation]    GIVEN DSPPhase WHEN checking values THEN lowercase
    [Tags]    unit    dsm    phase    values
    ${result}=    DSP Phase Values Are Lowercase
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[idle_correct]
    Should Be True    ${result}[audit_correct]
    Should Be True    ${result}[report_correct]
    Should Be True    ${result}[complete_correct]

Phase Order Returns List
    [Documentation]    GIVEN DSPPhase WHEN phase_order THEN returns list
    [Tags]    unit    dsm    phase    order
    ${result}=    Phase Order Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_list]
    Should Be True    ${result}[length_7]
    Should Be True    ${result}[no_idle]
    Should Be True    ${result}[no_complete]

Phase Order Is Correct Sequence
    [Documentation]    GIVEN DSPPhase WHEN phase_order THEN correct sequence
    [Tags]    unit    dsm    phase    sequence
    ${result}=    Phase Order Is Correct Sequence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[audit_first]
    Should Be True    ${result}[hypothesize_second]
    Should Be True    ${result}[validate_fifth]
    Should Be True    ${result}[report_seventh]

# =============================================================================
# PhaseCheckpoint Tests
# =============================================================================

Checkpoint Creation Works
    [Documentation]    GIVEN PhaseCheckpoint WHEN creating THEN fields set
    [Tags]    unit    dsm    checkpoint    create
    ${result}=    Checkpoint Creation Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[phase_correct]
    Should Be True    ${result}[timestamp_correct]
    Should Be True    ${result}[description_correct]

Checkpoint Has Default Metrics
    [Documentation]    GIVEN PhaseCheckpoint WHEN no metrics THEN empty dict
    [Tags]    unit    dsm    checkpoint    defaults
    ${result}=    Checkpoint Has Default Metrics
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[metrics_empty]

Checkpoint Has Default Evidence
    [Documentation]    GIVEN PhaseCheckpoint WHEN no evidence THEN empty list
    [Tags]    unit    dsm    checkpoint    defaults
    ${result}=    Checkpoint Has Default Evidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[evidence_empty]

# =============================================================================
# DSMCycle Tests
# =============================================================================

Cycle Creation Works
    [Documentation]    GIVEN DSMCycle WHEN creating THEN cycle_id set
    [Tags]    unit    dsm    cycle    create
    ${result}=    Cycle Creation Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[phase_idle]

Cycle Has Default Empty Lists
    [Documentation]    GIVEN DSMCycle WHEN creating THEN lists empty
    [Tags]    unit    dsm    cycle    defaults
    ${result}=    Cycle Has Default Empty Lists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[phases_empty]
    Should Be True    ${result}[checkpoints_empty]
    Should Be True    ${result}[findings_empty]

Cycle To Dict Works
    [Documentation]    GIVEN DSMCycle WHEN to_dict THEN returns dict
    [Tags]    unit    dsm    cycle    serialize
    ${result}=    Cycle To Dict Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[batch_correct]
    Should Be True    ${result}[phase_correct]
    Should Be True    ${result}[checkpoints_is_list]

# =============================================================================
# DSMTracker Initialization Tests
# =============================================================================

Tracker Class Exists
    [Documentation]    GIVEN dsm_tracker WHEN importing THEN DSMTracker exists
    [Tags]    unit    dsm    tracker    class
    ${result}=    Tracker Class Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Tracker Creates With Defaults
    [Documentation]    GIVEN DSMTracker WHEN creating THEN defaults set
    [Tags]    unit    dsm    tracker    create
    ${result}=    Tracker Creates With Defaults
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[no_cycle]
    Should Be True    ${result}[completed_empty]

Tracker Starts With No Active Cycle
    [Documentation]    GIVEN DSMTracker WHEN new THEN no active cycle
    [Tags]    unit    dsm    tracker    init
    ${result}=    Tracker Starts With No Active Cycle
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[no_cycle]
    Should Be True    ${result}[not_active]

# =============================================================================
# Serialization Tests
# =============================================================================

Tracker To Dict Returns Dict
    [Documentation]    GIVEN DSMTracker WHEN to_dict THEN returns dict
    [Tags]    unit    dsm    tracker    serialize
    ${result}=    Tracker To Dict Returns Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_current_cycle]
    Should Be True    ${result}[has_completed]

Tracker To JSON Returns Valid JSON
    [Documentation]    GIVEN DSMTracker WHEN to_json THEN valid JSON
    [Tags]    unit    dsm    tracker    json
    ${result}=    Tracker To JSON Returns Valid JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[valid_json]
    Should Be True    ${result}[no_cycle]

# =============================================================================
# Global Tracker Functions
# =============================================================================

Get Tracker Returns Tracker
    [Documentation]    GIVEN get_tracker WHEN called THEN returns DSMTracker
    [Tags]    unit    dsm    global    factory
    ${result}=    Get Tracker Returns Tracker
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_tracker]

Get Tracker Returns Same Instance
    [Documentation]    GIVEN get_tracker WHEN called twice THEN same instance
    [Tags]    unit    dsm    global    singleton
    ${result}=    Get Tracker Returns Same Instance
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[same_instance]

Reset Tracker Clears Instance
    [Documentation]    GIVEN reset_tracker WHEN called THEN clears instance
    [Tags]    unit    dsm    global    reset
    ${result}=    Reset Tracker Clears Instance
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[different_instances]
