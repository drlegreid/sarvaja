*** Settings ***
Documentation    RF-004: Unit Tests - Task Lifecycle Status/Resolution
...              Migrated from tests/test_task_lifecycle.py
...              Per GAP-UI-046: Task status/resolution per Agile DoR/DoD
...              Status (lifecycle): OPEN -> IN_PROGRESS -> CLOSED
...              Resolution (outcome): DEFERRED, IMPLEMENTED, VALIDATED, CERTIFIED
Library          Collections
Library          ../../libs/TaskLifecycleLibrary.py

*** Test Cases ***
# =============================================================================
# Status Transitions Tests
# =============================================================================

Open To In Progress Valid
    [Documentation]    GIVEN OPEN WHEN transition to IN_PROGRESS THEN valid
    [Tags]    unit    lifecycle    status    transition
    ${result}=    Open To In Progress Valid
    Should Be True    ${result}[valid]

In Progress To Closed Valid
    [Documentation]    GIVEN IN_PROGRESS WHEN transition to CLOSED THEN valid
    [Tags]    unit    lifecycle    status    transition
    ${result}=    In Progress To Closed Valid
    Should Be True    ${result}[valid]

Closed To Open Valid
    [Documentation]    GIVEN CLOSED WHEN transition to OPEN THEN valid (reopen)
    [Tags]    unit    lifecycle    status    transition
    ${result}=    Closed To Open Valid
    Should Be True    ${result}[valid]

Open To Closed Valid
    [Documentation]    GIVEN OPEN WHEN transition to CLOSED THEN valid (skip)
    [Tags]    unit    lifecycle    status    transition
    ${result}=    Open To Closed Valid
    Should Be True    ${result}[valid]

Same Status Valid
    [Documentation]    GIVEN any status WHEN same status THEN valid
    [Tags]    unit    lifecycle    status    identity
    ${result}=    Same Status Valid
    Should Be True    ${result}[OPEN_same]
    Should Be True    ${result}[IN_PROGRESS_same]
    Should Be True    ${result}[CLOSED_same]

# =============================================================================
# Resolution Transitions Tests
# =============================================================================

None To Implemented Valid
    [Documentation]    GIVEN NONE WHEN transition to IMPLEMENTED THEN valid
    [Tags]    unit    lifecycle    resolution    transition
    ${result}=    None To Implemented Valid
    Should Be True    ${result}[valid]

Implemented To Validated Valid
    [Documentation]    GIVEN IMPLEMENTED WHEN transition to VALIDATED THEN valid
    [Tags]    unit    lifecycle    resolution    transition
    ${result}=    Implemented To Validated Valid
    Should Be True    ${result}[valid]

Validated To Certified Valid
    [Documentation]    GIVEN VALIDATED WHEN transition to CERTIFIED THEN valid
    [Tags]    unit    lifecycle    resolution    transition
    ${result}=    Validated To Certified Valid
    Should Be True    ${result}[valid]

None To Deferred Valid
    [Documentation]    GIVEN NONE WHEN transition to DEFERRED THEN valid
    [Tags]    unit    lifecycle    resolution    transition
    ${result}=    None To Deferred Valid
    Should Be True    ${result}[valid]

Deferred To Implemented Valid
    [Documentation]    GIVEN DEFERRED WHEN transition to IMPLEMENTED THEN valid
    [Tags]    unit    lifecycle    resolution    transition
    ${result}=    Deferred To Implemented Valid
    Should Be True    ${result}[valid]

Certified Cannot Skip To None
    [Documentation]    GIVEN CERTIFIED WHEN transition to NONE THEN invalid
    [Tags]    unit    lifecycle    resolution    constraint
    ${result}=    Certified Cannot Skip To None
    Should Be True    ${result}[invalid]

# =============================================================================
# Status/Resolution Combinations Tests
# =============================================================================

Open Must Have None Resolution
    [Documentation]    GIVEN OPEN THEN must have NONE resolution
    [Tags]    unit    lifecycle    combo    open
    ${result}=    Open Must Have None Resolution
    Should Be True    ${result}[none_valid]
    Should Be True    ${result}[implemented_invalid]

In Progress Must Have None Resolution
    [Documentation]    GIVEN IN_PROGRESS THEN must have NONE resolution
    [Tags]    unit    lifecycle    combo    progress
    ${result}=    In Progress Must Have None Resolution
    Should Be True    ${result}[none_valid]
    Should Be True    ${result}[validated_invalid]

Closed Must Have Resolution
    [Documentation]    GIVEN CLOSED THEN must have resolution (not NONE)
    [Tags]    unit    lifecycle    combo    closed
    ${result}=    Closed Must Have Resolution
    Should Be True    ${result}[none_invalid]
    Should Be True    ${result}[implemented_valid]
    Should Be True    ${result}[certified_valid]

Closed Deferred Is Valid
    [Documentation]    GIVEN CLOSED + DEFERRED THEN valid
    [Tags]    unit    lifecycle    combo    deferred
    ${result}=    Closed Deferred Is Valid
    Should Be True    ${result}[valid]

# =============================================================================
# Task Lifecycle Scenarios Tests
# =============================================================================

Happy Path To Certified
    [Documentation]    GIVEN OPEN WHEN full lifecycle THEN reaches CERTIFIED
    [Tags]    unit    lifecycle    scenario    happy
    ${result}=    Happy Path To Certified
    Should Be True    ${result}[start_valid]
    Should Be True    ${result}[trans1]
    Should Be True    ${result}[trans2]
    Should Be True    ${result}[trans3]
    Should Be True    ${result}[trans4]
    Should Be True    ${result}[trans5]
    Should Be True    ${result}[final_valid]

Defer And Resume
    [Documentation]    GIVEN task WHEN deferred then resumed THEN completes
    [Tags]    unit    lifecycle    scenario    defer
    ${result}=    Defer And Resume
    Should Be True    ${result}[defer_valid]
    Should Be True    ${result}[reopen_valid]
    Should Be True    ${result}[complete_valid]

Bug Found Downgrade
    [Documentation]    GIVEN CERTIFIED WHEN bug found THEN downgrade to VALIDATED
    [Tags]    unit    lifecycle    scenario    downgrade
    ${result}=    Bug Found Downgrade
    Should Be True    ${result}[downgrade_valid]
    Should Be True    ${result}[final_valid]

# =============================================================================
# TypeDB Schema Tests
# =============================================================================

Status Values Match Enum
    [Documentation]    GIVEN TypeDB status WHEN check THEN matches enum
    [Tags]    unit    lifecycle    schema    status
    ${result}=    Status Values Match Enum
    Should Be True    ${result}[all_match]

Resolution Values Match Enum
    [Documentation]    GIVEN TypeDB resolution WHEN check THEN matches enum
    [Tags]    unit    lifecycle    schema    resolution
    ${result}=    Resolution Values Match Enum
    Should Be True    ${result}[all_match]

Backward Compatible Status Mapping
    [Documentation]    GIVEN old status WHEN map THEN new status valid
    [Tags]    unit    lifecycle    schema    backward
    ${result}=    Backward Compatible Status Mapping
    Should Be True    ${result}[all_valid]

# =============================================================================
# BDD Scenario Tests
# =============================================================================

Scenario Developer Completes Task
    [Documentation]    GIVEN OPEN WHEN developer starts and finishes THEN complete
    [Tags]    unit    lifecycle    bdd    developer
    ${result}=    Scenario Developer Completes Task
    Should Be True    ${result}[working_valid]
    Should Be True    ${result}[complete_valid]

Scenario QA Validates Task
    [Documentation]    GIVEN IMPLEMENTED WHEN QA validates THEN VALIDATED
    [Tags]    unit    lifecycle    bdd    qa
    ${result}=    Scenario QA Validates Task
    Should Be True    ${result}[transition_valid]
    Should Be True    ${result}[combo_valid]

Scenario User Certifies Task
    [Documentation]    GIVEN VALIDATED WHEN user certifies THEN CERTIFIED
    [Tags]    unit    lifecycle    bdd    user
    ${result}=    Scenario User Certifies Task
    Should Be True    ${result}[transition_valid]
    Should Be True    ${result}[combo_valid]
