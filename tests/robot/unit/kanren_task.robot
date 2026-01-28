*** Settings ***
Documentation    RF-004: Unit Tests - Kanren Task Validation Constraints
...              Split from kanren_constraints.robot per DOC-SIZE-01-v1
...              Covers: Task Evidence Requirements, Task Assignment Validation
Library          Collections
Library          ../../libs/KanrenTaskLibrary.py
Force Tags        unit    kanren    tasks    high    task    validate    TASK-LIFE-01-v1

*** Test Cases ***
# =============================================================================
# Task Evidence Requirements Tests
# =============================================================================

Critical Requires Evidence
    [Documentation]    GIVEN CRITICAL task WHEN task_requires_evidence THEN True
    [Tags]    unit    kanren    evidence    critical
    ${result}=    Critical Requires Evidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[requires]

High Requires Evidence
    [Documentation]    GIVEN HIGH task WHEN task_requires_evidence THEN True
    [Tags]    unit    kanren    evidence    high
    ${result}=    High Requires Evidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[requires]

Medium No Evidence
    [Documentation]    GIVEN MEDIUM task WHEN task_requires_evidence THEN False
    [Tags]    unit    kanren    evidence    medium
    ${result}=    Medium No Evidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[no_evidence]

Low No Evidence
    [Documentation]    GIVEN LOW task WHEN task_requires_evidence THEN False
    [Tags]    unit    kanren    evidence    low
    ${result}=    Low No Evidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[no_evidence]

# =============================================================================
# Task Assignment Validation Tests
# =============================================================================

Expert Critical Valid
    [Documentation]    GIVEN expert agent WHEN valid_task_assignment CRITICAL THEN valid
    [Tags]    unit    kanren    assignment    expert    critical
    ${result}=    Expert Critical Valid
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[valid]
    Should Be True    ${result}[trust_level]
    Should Be True    ${result}[can_execute]
    Should Be True    ${result}[no_supervisor]
    Should Be True    ${result}[requires_evidence]

Supervised Critical Invalid
    [Documentation]    GIVEN supervised agent WHEN valid_task_assignment CRITICAL THEN invalid
    [Tags]    unit    kanren    assignment    supervised    critical
    ${result}=    Supervised Critical Invalid
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[invalid]
    Should Be True    ${result}[trust_level]
    Should Be True    ${result}[cannot_execute]
    Should Be True    ${result}[requires_supervisor]

Supervised Medium Valid
    [Documentation]    GIVEN supervised agent WHEN valid_task_assignment MEDIUM THEN valid
    [Tags]    unit    kanren    assignment    supervised    medium
    ${result}=    Supervised Medium Valid
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[valid]
    Should Be True    ${result}[trust_level]
    Should Be True    ${result}[can_execute]
    Should Be True    ${result}[requires_supervisor]
    Should Be True    ${result}[no_evidence]

Constraints Checked Included
    [Documentation]    GIVEN validation WHEN result THEN constraints_checked included
    [Tags]    unit    kanren    assignment    constraints
    ${result}=    Constraints Checked Included
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_constraints]
    Should Be True    ${result}[has_multiple]
    Should Be True    ${result}[has_rule_011]
