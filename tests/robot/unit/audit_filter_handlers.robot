*** Settings ***
Documentation    RF-004: Unit Tests - Audit Filter Handlers
...              Migrated from tests/unit/test_audit_filter_handlers.py
...              Per UI-AUDIT-004: Audit trail filterable by entity
Library          Collections
Library          ../../libs/AuditFilterHandlersLibrary.py
Force Tags        unit    audit    filters    medium    GOV-TRANSP-01-v1    GAP-UI-AUDIT-004    session    read

*** Test Cases ***
# =============================================================================
# Handler Existence Tests
# =============================================================================

Audit Filter Handler Function Exists
    [Documentation]    GIVEN common_handlers WHEN checking THEN audit filter defined
    [Tags]    unit    ui    validate    audit    handlers
    ${result}=    Audit Filter Handler Function Exists
    Should Be True    ${result}[has_audit_filter]

Audit Filter Handler Watches Entity Type
    [Documentation]    GIVEN handlers WHEN checking THEN watches entity_type
    [Tags]    unit    ui    validate    audit    handlers
    ${result}=    Audit Filter Handler Watches Entity Type
    Should Be True    ${result}[watches_entity_type]

Audit Filter Handler Watches Action Type
    [Documentation]    GIVEN handlers WHEN checking THEN watches action_type
    [Tags]    unit    ui    validate    audit    handlers
    ${result}=    Audit Filter Handler Watches Action Type
    Should Be True    ${result}[watches_action_type]

Audit Filter Handler Watches Entity Id
    [Documentation]    GIVEN handlers WHEN checking THEN watches entity_id
    [Tags]    unit    ui    validate    audit    handlers
    ${result}=    Audit Filter Handler Watches Entity Id
    Should Be True    ${result}[watches_entity_id]

Audit Filter Handler Watches Correlation Id
    [Documentation]    GIVEN handlers WHEN checking THEN watches correlation_id
    [Tags]    unit    ui    validate    audit    handlers
    ${result}=    Audit Filter Handler Watches Correlation Id
    Should Be True    ${result}[watches_correlation_id]

# =============================================================================
# Audit Filter State Tests
# =============================================================================

Filter State Variables In Initial
    [Documentation]    GIVEN initial_state WHEN checking THEN filter vars defined
    [Tags]    unit    ui    validate    audit    state
    ${result}=    Filter State Variables In Initial
    Should Be True    ${result}[has_entity_type]
    Should Be True    ${result}[has_action_type]
    Should Be True    ${result}[has_entity_id]
    Should Be True    ${result}[has_correlation_id]

Filter Type Lists In Initial
    [Documentation]    GIVEN initial_state WHEN checking THEN option lists defined
    [Tags]    unit    ui    validate    audit    state
    ${result}=    Filter Type Lists In Initial
    Should Be True    ${result}[has_entity_types]
    Should Be True    ${result}[has_action_types]

# =============================================================================
# Audit Filter API Integration Tests
# =============================================================================

Audit API Accepts Entity Type Filter
    [Documentation]    GIVEN API WHEN entity_type param THEN accepted
    [Tags]    unit    ui    validate    audit    api    integration
    ${result}=    Audit Api Accepts Entity Type Filter
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    API not available
    Should Be True    ${result}[accepted]

Audit API Accepts Action Type Filter
    [Documentation]    GIVEN API WHEN action_type param THEN accepted
    [Tags]    unit    ui    validate    audit    api    integration
    ${result}=    Audit Api Accepts Action Type Filter
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    API not available
    Should Be True    ${result}[accepted]

Audit API Accepts Entity Id Filter
    [Documentation]    GIVEN API WHEN entity_id param THEN accepted
    [Tags]    unit    ui    validate    audit    api    integration
    ${result}=    Audit Api Accepts Entity Id Filter
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    API not available
    Should Be True    ${result}[accepted]

Audit API Accepts Correlation Id Filter
    [Documentation]    GIVEN API WHEN correlation_id param THEN accepted
    [Tags]    unit    ui    validate    audit    api    integration
    ${result}=    Audit Api Accepts Correlation Id Filter
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    API not available
    Should Be True    ${result}[accepted]

