*** Settings ***
Documentation    RF-004: Unit Tests - Decision Dates
...              Migrated from tests/test_decision_dates.py
...              Per GAP-UI-EXP-001: Decisions missing dates
Library          Collections
Library          ../../libs/DecisionDatesLibrary.py
Force Tags        unit    decisions    dates    low    decision    read    SESSION-EVID-01-v1

*** Test Cases ***
# =============================================================================
# Decision Entity Tests
# =============================================================================

Decision Entity Has Date Field
    [Documentation]    GIVEN Decision dataclass WHEN checking THEN has decision_date
    [Tags]    unit    decision    dates    entity
    ${result}=    Decision Entity Has Date Field
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_decision_date]

Get All Decisions Returns Dates
    [Documentation]    GIVEN get_all_decisions WHEN called THEN includes dates
    [Tags]    unit    decision    dates    client    integration
    ${result}=    Get All Decisions Returns Dates
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    TypeDB not available or no decisions
    Should Be True    ${result}[has_decisions]
    Should Be True    ${result}[has_dates]

Decision Date Is Datetime
    [Documentation]    GIVEN decision_date WHEN present THEN is datetime type
    [Tags]    unit    decision    dates    type    integration
    ${result}=    Decision Date Is Datetime
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    TypeDB not available
    Should Be True    ${result}[is_datetime]

# =============================================================================
# Query Structure Tests
# =============================================================================

Query Fetches Date Attribute
    [Documentation]    GIVEN DecisionQueries WHEN checking THEN has decision-date
    [Tags]    unit    decision    dates    query
    ${result}=    Query Fetches Date Attribute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import or attribute failed
    Should Be True    ${result}[has_decision_date]
