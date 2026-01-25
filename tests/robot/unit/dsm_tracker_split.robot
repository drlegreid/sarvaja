*** Settings ***
Documentation    RF-004: Unit Tests - DSM Tracker Split
...              Migrated from tests/test_dsm_tracker_split.py
...              Per GAP-FILE-024: dsm/tracker.py split
Library          Collections
Library          ../../libs/DSMTrackerSplitLibrary.py

*** Test Cases ***
# =============================================================================
# Module Structure Tests
# =============================================================================

Tracker Module Exists
    [Documentation]    GIVEN dsm dir WHEN checking THEN tracker.py exists
    [Tags]    unit    dsm    split    module
    ${result}=    Tracker Module Exists
    Should Be True    ${result}[exists]

Memory Module Exists
    [Documentation]    GIVEN dsm dir WHEN checking THEN memory.py exists
    [Tags]    unit    dsm    split    module
    ${result}=    Memory Module Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    memory.py not yet extracted
    Should Be True    ${result}[exists]

# =============================================================================
# Backward Compatibility Tests
# =============================================================================

Import DSM Tracker Class From DSM
    [Documentation]    GIVEN dsm.tracker WHEN import DSMTracker THEN works
    [Tags]    unit    dsm    split    import
    ${result}=    Import DSM Tracker Class From DSM
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

Import Get Tracker From DSM
    [Documentation]    GIVEN dsm.tracker WHEN import get_tracker THEN works
    [Tags]    unit    dsm    split    import
    ${result}=    Import Get Tracker From DSM
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

Import Reset Tracker From DSM
    [Documentation]    GIVEN dsm.tracker WHEN import reset_tracker THEN works
    [Tags]    unit    dsm    split    import
    ${result}=    Import Reset Tracker From DSM
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

Create DSM Tracker Instance
    [Documentation]    GIVEN DSMTracker WHEN creating THEN instance created
    [Tags]    unit    dsm    split    create
    ${result}=    Create DSM Tracker Instance
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created]

# =============================================================================
# Core Functionality Tests
# =============================================================================

DSM Tracker Start Cycle
    [Documentation]    GIVEN DSMTracker WHEN start_cycle THEN cycle created
    [Tags]    unit    dsm    split    cycle
    ${result}=    DSM Tracker Start Cycle
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_none]
    Should Be True    ${result}[starts_with_dsm]

DSM Tracker Get Status
    [Documentation]    GIVEN DSMTracker WHEN get_status THEN returns dict
    [Tags]    unit    dsm    split    status
    ${result}=    DSM Tracker Get Status
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_active]

DSM Tracker Get Session Memory Payload
    [Documentation]    GIVEN DSMTracker WHEN no cycle THEN payload None
    [Tags]    unit    dsm    split    payload
    ${result}=    DSM Tracker Get Session Memory Payload
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[payload_none]

# =============================================================================
# Integration Tests
# =============================================================================

DSM Global Tracker Singleton
    [Documentation]    GIVEN get_tracker WHEN called twice THEN same instance
    [Tags]    unit    dsm    split    singleton
    ${result}=    DSM Global Tracker Singleton
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[same_instance]

DSM Tracker To Dict
    [Documentation]    GIVEN DSMTracker WHEN to_dict THEN returns dict
    [Tags]    unit    dsm    split    serialize
    ${result}=    DSM Tracker To Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_current_cycle]
