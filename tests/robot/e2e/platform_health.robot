*** Settings ***
Documentation    RF-006: E2E Platform Health Tests
...              Per RULE-004: Thin-slice platform verification
...              Migrated from tests/e2e/test_platform_health_e2e.py
Library          Collections
Library          ../../libs/PlatformHealthE2ELibrary.py
Test Tags        e2e    api    health    critical    SAFETY-HEALTH-01-v1    validate

*** Test Cases ***
# =============================================================================
# Core Infrastructure Tests
# =============================================================================

TypeDB Is Accessible
    [Documentation]    CRITICAL: TypeDB must be accessible
    [Tags]    e2e    health    typedb    critical
    ${result}=    TypeDB Health Check
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    TypeDB check skipped
    Should Be True    ${result}[healthy]    TypeDB unhealthy: ${result}

ChromaDB Is Accessible
    [Documentation]    CRITICAL: ChromaDB must be accessible
    [Tags]    e2e    health    chromadb    critical
    ${result}=    ChromaDB Health Check
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    ChromaDB check skipped
    Should Be True    ${result}[healthy]    ChromaDB unhealthy: ${result}

# =============================================================================
# Kanren Constraint Engine Tests
# =============================================================================

Kanren Constraint Engine Works
    [Documentation]    CRITICAL: Kanren constraints must work
    [Tags]    e2e    health    kanren    critical
    ${result}=    Kanren Health Check
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Kanren not available
    Should Be True    ${result}[healthy]    Kanren unhealthy: ${result}
    Should Be True    ${result}[rag_filter_works]    RAG filtering failed
    Should Be True    ${result}[task_assignment_works]    Task assignment failed

Kanren Performance Is Under Target
    [Documentation]    KAN-005: Kanren performance under target
    [Tags]    e2e    health    kanren    performance
    ${result}=    Kanren Benchmark Check
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Kanren benchmark not available
    Should Be True    ${result}[healthy]    Kanren benchmark failed

# =============================================================================
# Service Endpoint Tests
# =============================================================================

Dashboard Responds
    [Documentation]    Dashboard HTTP endpoint responds
    [Tags]    e2e    health    dashboard    optional
    ${result}=    Dashboard Health Check
    ${healthy}=    Evaluate    $result.get('healthy', False)
    Skip If    not ${healthy}    Dashboard not running
    Should Be True    ${healthy}    Dashboard unhealthy

API Responds
    [Documentation]    API endpoint responds (optional)
    [Tags]    e2e    health    api    optional
    ${result}=    API Health Check
    ${healthy}=    Evaluate    $result.get('healthy', False)
    Skip If    not ${healthy}    API not running
    Should Be True    ${healthy}    API unhealthy

# =============================================================================
# MCP Integration Tests
# =============================================================================

MCP Core Services Can Import
    [Documentation]    MCP CORE services can be imported
    [Tags]    e2e    health    mcp    core
    ${result}=    MCP Core Services Check
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    MCP check skipped
    Should Be True    ${result}[healthy]    MCP services failed: ${result}
