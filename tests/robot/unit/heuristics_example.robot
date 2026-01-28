*** Settings ***
Documentation    Heuristics Example Tests - SFDIPOT and CRUCSS Frameworks
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/heuristics/test_heuristics_example.py
...              Demonstrates systematic gap discovery.
Library          Collections
Library          ../../libs/HeuristicsExampleLibrary.py
Resource         ../resources/common.resource
Force Tags             unit    heuristics    sfdipot    crucss    low    validate    TEST-COMP-01-v1

*** Test Cases ***
# =============================================================================
# SFDIPOT: Structure Tests
# =============================================================================

Test TypeDB Entities Exist
    [Documentation]    Verify TypeDB schema includes required entities
    [Tags]    sfdipot    structure    schema
    ${result}=    TypeDB Entities Exist
    Should Be True    ${result['count_correct']}

Test API Routes Match Spec
    [Documentation]    Verify API routes are documented
    [Tags]    sfdipot    structure    api
    ${result}=    API Routes Match Spec
    Should Be True    ${result['has_minimum_routes']}

# =============================================================================
# SFDIPOT: Data Tests
# =============================================================================

Test Task Description Integrity
    [Documentation]    Tasks should have descriptions (GAP-DATA-001)
    [Tags]    sfdipot    data    task    GAP-DATA-001
    ${result}=    Task Description Integrity
    Should Be True    ${result['integrity_check']}

Test Rule Directive Length
    [Documentation]    Rules must have meaningful directives
    [Tags]    sfdipot    data    rule
    ${result}=    Rule Directive Length
    Should Be True    ${result['length_valid']}

# =============================================================================
# SFDIPOT: Function Tests
# =============================================================================

Test Rules CRUD Flow
    [Documentation]    Verify rules can be created, read, updated, deleted
    [Tags]    sfdipot    function    crud
    ${result}=    Rules CRUD Flow
    Should Be True    ${result['crud_flow_valid']}

Test Task Status Workflow
    [Documentation]    Tasks: pending → in_progress → completed
    [Tags]    sfdipot    function    workflow
    ${result}=    Task Status Workflow
    Should Be True    ${result['has_minimum_transitions']}

# =============================================================================
# CRUCSS: Security Tests
# =============================================================================

Test API Auth Required
    [Documentation]    API should require authentication (GAP-SEC-001)
    [Tags]    crucss    security    auth    GAP-SEC-001
    ${result}=    API Auth Required
    Should Be True    ${result['auth_check']}

Test No Secrets In Repo
    [Documentation]    Secrets should never be committed
    [Tags]    crucss    security    secrets
    ${result}=    No Secrets In Repo
    Should Be True    ${result['secrets_check']}

# =============================================================================
# CRUCSS: Reliability Tests
# =============================================================================

Test TypeDB Failover
    [Documentation]    System should handle TypeDB restart gracefully
    [Tags]    crucss    reliability    failover
    ${result}=    TypeDB Failover
    Should Be True    ${result['failover_check']}

Test Health Check Detection
    [Documentation]    Healthcheck should detect down services
    [Tags]    crucss    reliability    health
    ${result}=    Health Check Detection
    Should Be True    ${result['health_detection_check']}

# =============================================================================
# CRUCSS: Capability Tests
# =============================================================================

Test Rule Management Capability
    [Documentation]    End-to-end rule management
    [Tags]    crucss    capability    rule
    ${result}=    Rule Management Capability
    Should Be True    ${result['capability_check']}

Test Chat Capability
    [Documentation]    User can interact with agents via chat
    [Tags]    crucss    capability    chat
    ${result}=    Chat Capability
    Should Be True    ${result['chat_check']}

# =============================================================================
# CRUCSS: Usability Tests
# =============================================================================

Test Navigation Usability
    [Documentation]    Users can find features easily
    [Tags]    crucss    usability    navigation
    ${result}=    Navigation Usability
    Should Be True    ${result['navigation_check']}

Test Error Messages Usability
    [Documentation]    Errors explain what went wrong
    [Tags]    crucss    usability    errors
    ${result}=    Error Messages Usability
    Should Be True    ${result['error_messages_check']}

# =============================================================================
# Coverage Report Tests
# =============================================================================

Test Coverage Report Generation
    [Documentation]    Coverage report should include all heuristics
    [Tags]    coverage    report
    ${result}=    Coverage Report Generation
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_sfdipot']}
    Should Be True    ${result['has_crucss']}

Test Gap Detection
    [Documentation]    Coverage report should identify missing aspects
    [Tags]    coverage    gaps
    ${result}=    Gap Detection
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['gaps_is_dict']}
    Should Be True    ${result['has_sfdipot_gaps']}
    Should Be True    ${result['has_crucss_gaps']}
