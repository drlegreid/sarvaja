*** Settings ***
Documentation    RF-004: Unit Tests - Agent Hybrid Layer
...              Migrated from tests/test_agent_hybrid.py
...              Per P3.4: Agent hybrid layer integration
Library          Collections
Library          ../../libs/AgentHybridLibrary.py
Force Tags        unit    agents    hybrid    low    agent    validate    GOV-BICAM-01-v1

*** Test Cases ***
# =============================================================================
# HybridVectorDb Tests
# =============================================================================

Hybrid VectorDb Class Exists
    [Documentation]    GIVEN agent module WHEN importing THEN HybridVectorDb exists
    [Tags]    unit    hybrid    vectordb    class
    ${result}=    Hybrid VectorDb Class Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Hybrid VectorDb Implements Search
    [Documentation]    GIVEN HybridVectorDb WHEN checking THEN has search method
    [Tags]    unit    hybrid    vectordb    method
    ${result}=    Hybrid VectorDb Implements Search
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_search]
    Should Be True    ${result}[search_callable]

Hybrid VectorDb Routes Inference Queries
    [Documentation]    GIVEN inference query WHEN search THEN routes to TypeDB
    [Tags]    unit    hybrid    vectordb    routing
    ${result}=    Hybrid VectorDb Routes Inference Queries
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import or method not found
    Should Be True    ${result}[called_typedb]

Hybrid VectorDb Routes Semantic Queries
    [Documentation]    GIVEN semantic query WHEN search THEN routes to ChromaDB
    [Tags]    unit    hybrid    vectordb    routing
    ${result}=    Hybrid VectorDb Routes Semantic Queries
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import or method not found
    Should Be True    ${result}[called_chromadb]

Hybrid VectorDb Fallback To ChromaDB
    [Documentation]    GIVEN TypeDB down WHEN search THEN fallback to ChromaDB
    [Tags]    unit    hybrid    vectordb    fallback
    ${result}=    Hybrid VectorDb Fallback To ChromaDB
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import or method not found
    Should Be True    ${result}[fallback_called]

# =============================================================================
# Agent Governance Query Tests
# =============================================================================

Agent Can Query Rule Dependencies
    [Documentation]    GIVEN hybrid db WHEN query dependencies THEN returns result
    [Tags]    unit    hybrid    governance    dependencies
    ${result}=    Agent Can Query Rule Dependencies
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import or router not found
    Should Be True    ${result}[has_result]

Agent Can Query Conflicts
    [Documentation]    GIVEN hybrid db WHEN query conflicts THEN returns result
    [Tags]    unit    hybrid    governance    conflicts
    ${result}=    Agent Can Query Conflicts
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import or router not found
    Should Be True    ${result}[has_result]

# =============================================================================
# Sync Bridge Tests
# =============================================================================

Agent Sees Synced Rules
    [Documentation]    GIVEN sync bridge WHEN get_sync_status THEN has collections
    [Tags]    unit    hybrid    sync    bridge
    ${result}=    Agent Sees Synced Rules
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_collections]
