*** Settings ***
Documentation    RF-004: Unit Tests - Merge Conflict Checker
...              Migrated from tests/unit/test_conflict_checker.py
...              Per MULTI-007: Merge conflict detection for multi-agent workflows
Library          Collections
Library          ../../libs/ConflictCheckerLibrary.py

*** Test Cases ***
# =============================================================================
# Module Import Tests
# =============================================================================

Conflict Checker Module Imports
    [Documentation]    GIVEN conflict_checker module WHEN importing THEN all functions available
    [Tags]    unit    hooks    read    import
    ${result}=    Verify Module Imports
    Should Be True    ${result}

# =============================================================================
# check_merge_conflicts Tests
# =============================================================================

Check Merge Conflicts Returns Dict
    [Documentation]    GIVEN conflict_checker WHEN check_merge_conflicts THEN returns dict
    [Tags]    unit    hooks    validate    structure
    ${result}=    Check Merge Conflicts
    Should Be True    ${{ isinstance($result, dict) }}
    Dictionary Should Contain Key    ${result}    has_conflicts
    Dictionary Should Contain Key    ${result}    conflicts
    Should Be True    ${{ isinstance($result["has_conflicts"], bool) }}
    Should Be True    ${{ isinstance($result["conflicts"], list) }}

# =============================================================================
# get_conflict_summary Tests
# =============================================================================

Get Conflict Summary Returns Dict
    [Documentation]    GIVEN conflict_checker WHEN get_conflict_summary THEN returns dict
    [Tags]    unit    hooks    validate    structure
    ${result}=    Get Conflict Summary
    Should Be True    ${{ isinstance($result, dict) }}
    Dictionary Should Contain Key    ${result}    has_conflicts
    Dictionary Should Contain Key    ${result}    conflict_count
    Dictionary Should Contain Key    ${result}    conflicts
    Dictionary Should Contain Key    ${result}    marker_files
    Dictionary Should Contain Key    ${result}    merge_state
    Dictionary Should Contain Key    ${result}    alerts
    Dictionary Should Contain Key    ${result}    status

No Conflicts Returns OK Status
    [Documentation]    GIVEN clean repo WHEN get_conflict_summary THEN status is OK or WARNING
    [Tags]    unit    hooks    validate    status
    ${result}=    Get Conflict Summary
    Should Be True    ${{ $result["status"] in ["OK", "WARNING"] }}

# =============================================================================
# Mocked Git Conflict Detection Tests
# =============================================================================

Detects Unmerged Files UU Status
    [Documentation]    GIVEN UU status WHEN check_merge_conflicts THEN conflict detected
    [Tags]    unit    hooks    validate    mock
    ${result}=    Check Merge Conflicts With Mock    UU conflicted_file.py\n
    Should Be True    ${result}[has_conflicts]
    Should Be Equal As Integers    ${result}[conflict_count]    1
    ${conflict}=    Get From List    ${result}[conflicts]    0
    Should Be Equal    ${conflict}[file]    conflicted_file.py
    Should Be Equal    ${conflict}[status]    UU
    Should Be Equal    ${conflict}[status_meaning]    both modified

Detects Both Added AA Status
    [Documentation]    GIVEN AA status WHEN check_merge_conflicts THEN both added detected
    [Tags]    unit    hooks    validate    mock
    ${result}=    Check Merge Conflicts With Mock    AA new_file.py\n
    Should Be True    ${result}[has_conflicts]
    ${conflict}=    Get From List    ${result}[conflicts]    0
    Should Be Equal    ${conflict}[status]    AA
    Should Be Equal    ${conflict}[status_meaning]    both added

Ignores Normal Modifications
    [Documentation]    GIVEN normal M status WHEN check_merge_conflicts THEN no conflict
    [Tags]    unit    hooks    validate    mock
    ${result}=    Check Merge Conflicts With Mock    \ M modified_file.py\nM\ \ staged_file.py\n
    Should Not Be True    ${result}[has_conflicts]
    Should Be Equal As Integers    ${result}[conflict_count]    0

Handles Git Error Gracefully
    [Documentation]    GIVEN git error WHEN check_merge_conflicts THEN graceful handling
    [Tags]    unit    hooks    validate    reliability
    ${result}=    Check Merge Conflicts With Error    fatal: not a git repository
    Should Not Be True    ${result}[has_conflicts]
    Dictionary Should Contain Key    ${result}    error

# =============================================================================
# Merge State Detection Tests
# =============================================================================

Merge State Detection Returns Dict
    [Documentation]    GIVEN check_merge_state WHEN called THEN returns merge state info
    [Tags]    unit    hooks    validate    merge-state
    ${state}=    Check Merge State
    Should Be True    ${{ isinstance($state, dict) }}
    Dictionary Should Contain Key    ${state}    in_merge
    Dictionary Should Contain Key    ${state}    in_rebase
    Dictionary Should Contain Key    ${state}    in_cherry_pick
    Dictionary Should Contain Key    ${state}    in_revert
    Dictionary Should Contain Key    ${state}    in_conflicted_state

# =============================================================================
# API Endpoint Tests
# =============================================================================

API Endpoint Exists
    [Documentation]    GIVEN API routes WHEN checking THEN conflicts endpoint exists
    [Tags]    unit    hooks    agents    validate    api
    ${exists}=    Verify Api Endpoint Exists
    Should Be True    ${exists}

