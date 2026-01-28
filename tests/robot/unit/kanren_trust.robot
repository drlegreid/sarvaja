*** Settings ***
Documentation    RF-004: Unit Tests - Kanren Trust & Supervisor Constraints
...              Split from kanren_constraints.robot per DOC-SIZE-01-v1
...              Covers: Trust Level, Supervisor Requirements, Can Execute Priority
Library          Collections
Library          ../../libs/KanrenTrustLibrary.py
Force Tags        unit    kanren    trust    high    validate    GOV-BICAM-01-v1

*** Test Cases ***
# =============================================================================
# Trust Level Tests (RULE-011)
# =============================================================================

Trust Level Expert
    [Documentation]    GIVEN trust score >= 0.9 WHEN trust_level THEN expert
    [Tags]    unit    kanren    trust    expert
    ${result}=    Trust Level Expert
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[level_95]
    Should Be True    ${result}[level_90]
    Should Be True    ${result}[level_100]

Trust Level Trusted
    [Documentation]    GIVEN trust score >= 0.7 and < 0.9 WHEN trust_level THEN trusted
    [Tags]    unit    kanren    trust    trusted
    ${result}=    Trust Level Trusted
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[level_89]
    Should Be True    ${result}[level_75]
    Should Be True    ${result}[level_70]

Trust Level Supervised
    [Documentation]    GIVEN trust score >= 0.5 and < 0.7 WHEN trust_level THEN supervised
    [Tags]    unit    kanren    trust    supervised
    ${result}=    Trust Level Supervised
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[level_69]
    Should Be True    ${result}[level_55]
    Should Be True    ${result}[level_50]

Trust Level Restricted
    [Documentation]    GIVEN trust score < 0.5 WHEN trust_level THEN restricted
    [Tags]    unit    kanren    trust    restricted
    ${result}=    Trust Level Restricted
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[level_49]
    Should Be True    ${result}[level_25]
    Should Be True    ${result}[level_0]

# =============================================================================
# Supervisor Requirement Tests
# =============================================================================

Restricted Requires Supervisor
    [Documentation]    GIVEN restricted agent WHEN requires_supervisor THEN True
    [Tags]    unit    kanren    supervisor    restricted
    ${result}=    Restricted Requires Supervisor
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[requires]

Supervised Requires Supervisor
    [Documentation]    GIVEN supervised agent WHEN requires_supervisor THEN True
    [Tags]    unit    kanren    supervisor    supervised
    ${result}=    Supervised Requires Supervisor
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[requires]

Trusted No Supervisor
    [Documentation]    GIVEN trusted agent WHEN requires_supervisor THEN False
    [Tags]    unit    kanren    supervisor    trusted
    ${result}=    Trusted No Supervisor
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[no_supervisor]

Expert No Supervisor
    [Documentation]    GIVEN expert agent WHEN requires_supervisor THEN False
    [Tags]    unit    kanren    supervisor    expert
    ${result}=    Expert No Supervisor
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[no_supervisor]

# =============================================================================
# Can Execute Priority Tests
# =============================================================================

Critical Expert Can Execute
    [Documentation]    GIVEN expert WHEN can_execute CRITICAL THEN True
    [Tags]    unit    kanren    priority    critical    expert
    ${result}=    Critical Expert Can Execute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[can_execute]

Critical Trusted Can Execute
    [Documentation]    GIVEN trusted WHEN can_execute CRITICAL THEN True
    [Tags]    unit    kanren    priority    critical    trusted
    ${result}=    Critical Trusted Can Execute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[can_execute]

Critical Supervised Cannot Execute
    [Documentation]    GIVEN supervised WHEN can_execute CRITICAL THEN False
    [Tags]    unit    kanren    priority    critical    supervised
    ${result}=    Critical Supervised Cannot Execute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[cannot_execute]

Critical Restricted Cannot Execute
    [Documentation]    GIVEN restricted WHEN can_execute CRITICAL THEN False
    [Tags]    unit    kanren    priority    critical    restricted
    ${result}=    Critical Restricted Cannot Execute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[cannot_execute]

High Supervised Can Execute
    [Documentation]    GIVEN supervised WHEN can_execute HIGH THEN True
    [Tags]    unit    kanren    priority    high    supervised
    ${result}=    High Supervised Can Execute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[can_execute]

High Restricted Cannot Execute
    [Documentation]    GIVEN restricted WHEN can_execute HIGH THEN False
    [Tags]    unit    kanren    priority    high    restricted
    ${result}=    High Restricted Cannot Execute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[cannot_execute]

Medium All Can Execute
    [Documentation]    GIVEN any trust WHEN can_execute MEDIUM THEN True
    [Tags]    unit    kanren    priority    medium
    ${result}=    Medium All Can Execute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[expert_can]
    Should Be True    ${result}[trusted_can]
    Should Be True    ${result}[supervised_can]
    Should Be True    ${result}[restricted_can]

Low All Can Execute
    [Documentation]    GIVEN any trust WHEN can_execute LOW THEN True
    [Tags]    unit    kanren    priority    low
    ${result}=    Low All Can Execute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[expert_can]
    Should Be True    ${result}[trusted_can]
    Should Be True    ${result}[supervised_can]
    Should Be True    ${result}[restricted_can]

# =============================================================================
# Validate Agent For Task Tests
# =============================================================================

Validate Expert Critical
    [Documentation]    GIVEN expert score WHEN validate_agent_for_task CRITICAL THEN valid
    [Tags]    unit    kanren    validation    expert
    ${result}=    Validate Expert Critical
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[valid]

Validate Restricted Critical
    [Documentation]    GIVEN restricted score WHEN validate_agent_for_task CRITICAL THEN invalid
    [Tags]    unit    kanren    validation    restricted
    ${result}=    Validate Restricted Critical
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[invalid]
