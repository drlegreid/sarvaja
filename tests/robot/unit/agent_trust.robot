*** Settings ***
Documentation    RF-004: Unit Tests - Agent Trust Dashboard
...              Migrated from tests/test_agent_trust.py
...              Per P9.5: Agent trust tracking and RULE-011 compliance
Library          Collections
Library          ../../libs/AgentTrustLibrary.py

*** Test Cases ***
# =============================================================================
# Module Existence Tests
# =============================================================================

Agent Trust Module Exists
    [Documentation]    GIVEN agent/ WHEN checking THEN agent_trust.py exists
    [Tags]    unit    agent-trust    validate    module
    ${result}=    Agent Trust Module Exists
    Should Be True    ${result}[exists]

Agent Trust Class Importable
    [Documentation]    GIVEN agent_trust WHEN importing THEN AgentTrustDashboard available
    [Tags]    unit    agent-trust    validate    module
    ${result}=    Agent Trust Class Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[instantiable]

Dashboard Has Required Methods
    [Documentation]    GIVEN dashboard WHEN checking THEN has required methods
    [Tags]    unit    agent-trust    validate    module
    ${result}=    Dashboard Has Required Methods
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_get_trust_score]
    Should Be True    ${result}[has_get_compliance_status]
    Should Be True    ${result}[has_record_action]
    Should Be True    ${result}[has_get_trust_history]

# =============================================================================
# Trust Scoring Tests
# =============================================================================

Get Trust Score Works
    [Documentation]    GIVEN agent_id WHEN get_trust_score THEN returns valid score
    [Tags]    unit    agent-trust    validate    scoring
    ${result}=    Get Trust Score Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_number]
    Should Be True    ${result}[in_range]

Default Trust Score Works
    [Documentation]    GIVEN new agent WHEN get_trust_score THEN returns default
    [Tags]    unit    agent-trust    validate    scoring
    ${result}=    Default Trust Score Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_default]

Get All Trust Scores Works
    [Documentation]    GIVEN dashboard WHEN get_all_trust_scores THEN returns dict
    [Tags]    unit    agent-trust    validate    scoring
    ${result}=    Get All Trust Scores Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]

# =============================================================================
# Compliance Tracking Tests
# =============================================================================

Get Compliance Status Works
    [Documentation]    GIVEN agent_id WHEN get_compliance_status THEN returns status
    [Tags]    unit    agent-trust    validate    compliance
    ${result}=    Get Compliance Status Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_compliant]

