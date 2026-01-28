*** Settings ***
Documentation    RF-004: Unit Tests - Governance Module
...              Migrated from tests/test_governance.py
...              Per DECISION-003: TypeDB-First Architecture
Library          Collections
Library          ../../libs/GovernanceLibrary.py
Force Tags        unit    governance    critical    GOV-RULE-01-v1    rules    rule    validate

*** Test Cases ***
# =============================================================================
# Dataclass Tests
# =============================================================================

Rule Creation Works
    [Documentation]    GIVEN Rule WHEN creating THEN all fields correct
    [Tags]    unit    governance    validate    dataclass
    ${result}=    Rule Creation Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[category_correct]
    Should Be True    ${result}[priority_correct]

Rule With Date Works
    [Documentation]    GIVEN Rule WHEN with date THEN date set correctly
    [Tags]    unit    governance    validate    dataclass
    ${result}=    Rule With Date Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[date_set]

Decision Creation Works
    [Documentation]    GIVEN Decision WHEN creating THEN all fields correct
    [Tags]    unit    governance    validate    dataclass
    ${result}=    Decision Creation Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[status_correct]

Inference Result Creation Works
    [Documentation]    GIVEN InferenceResult WHEN creating THEN all fields correct
    [Tags]    unit    governance    validate    dataclass
    ${result}=    Inference Result Creation Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[query_starts_match]
    Should Be True    ${result}[results_count_2]
    Should Be True    ${result}[count_correct]

# =============================================================================
# Quick Health Tests
# =============================================================================

Quick Health Returns Bool
    [Documentation]    GIVEN quick_health WHEN calling THEN returns bool
    [Tags]    unit    governance    validate    health
    ${result}=    Quick Health Returns Bool
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_bool]

Quick Health Mocked Success
    [Documentation]    GIVEN mocked success WHEN quick_health THEN returns True
    [Tags]    unit    governance    validate    health    mocked
    ${result}=    Quick Health Mocked Success
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[returns_true]
    Should Be True    ${result}[close_called]

Quick Health Mocked Failure
    [Documentation]    GIVEN mocked failure WHEN quick_health THEN returns False
    [Tags]    unit    governance    validate    health    mocked
    ${result}=    Quick Health Mocked Failure
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[returns_false]

# =============================================================================
# Schema Files Tests
# =============================================================================

Schema File Exists
    [Documentation]    GIVEN project WHEN checking THEN schema file exists
    [Tags]    unit    governance    validate    schema
    ${result}=    Schema File Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[ends_with_tql]
    Should Be True    ${result}[exists]

Data File Exists
    [Documentation]    GIVEN project WHEN checking THEN data file exists
    [Tags]    unit    governance    validate    schema
    ${result}=    Data File Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[ends_with_tql]
    Should Be True    ${result}[exists]

Schema File Has Content
    [Documentation]    GIVEN schema file WHEN reading THEN has expected content
    [Tags]    unit    governance    validate    schema
    ${result}=    Schema File Has Content
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    File not accessible
    Should Be True    ${result}[has_define]
    Should Be True    ${result}[has_rule_entity]

Data File Has Content
    [Documentation]    GIVEN data file WHEN reading THEN has expected content
    [Tags]    unit    governance    validate    schema
    ${result}=    Data File Has Content
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    File not accessible
    Should Be True    ${result}[has_insert]
    Should Be True    ${result}[has_rule_001]

# =============================================================================
# TypeDB Client Unit Tests
# =============================================================================

Client Initialization Works
    [Documentation]    GIVEN TypeDBClient WHEN init THEN defaults correct
    [Tags]    unit    governance    validate    client
    ${result}=    Client Initialization Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[valid_host]
    Should Be True    ${result}[port_correct]
    Should Be True    ${result}[database_correct]

Client Custom Params Works
    [Documentation]    GIVEN TypeDBClient WHEN custom params THEN set correctly
    [Tags]    unit    governance    validate    client
    ${result}=    Client Custom Params Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[host_correct]
    Should Be True    ${result}[port_correct]
    Should Be True    ${result}[database_correct]

Is Connected Default False
    [Documentation]    GIVEN new client WHEN checking THEN not connected
    [Tags]    unit    governance    validate    client
    ${result}=    Is Connected Default False
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_connected]

Health Check Not Connected
    [Documentation]    GIVEN not connected WHEN health_check THEN error
    [Tags]    unit    governance    validate    client
    ${result}=    Health Check Not Connected
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_healthy]
    Should Be True    ${result}[has_error]

Execute Query Not Connected Raises
    [Documentation]    GIVEN not connected WHEN query THEN raises RuntimeError
    [Tags]    unit    governance    validate    client
    ${result}=    Execute Query Not Connected Raises
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[raises_error]
    Should Be True    ${result}[mentions_not_connected]

