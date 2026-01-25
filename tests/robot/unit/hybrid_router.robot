*** Settings ***
Documentation    RF-004: Unit Tests - Hybrid Query Router
...              Migrated from tests/test_hybrid_router.py
...              Tests routing logic between TypeDB and ChromaDB
Library          Collections
Library          ../../libs/HybridRouterLibrary.py

*** Test Cases ***
# =============================================================================
# Query Type Detection Tests
# =============================================================================

Detect Inference Query Depends On
    [Documentation]    Inference: 'depends on' keyword
    [Tags]    unit    router    inference    detection
    ${type}=    Detect Query Type    What depends on RULE-001?
    Should Be Equal    ${type}    inference

Detect Inference Query Conflicts
    [Documentation]    Inference: 'conflicts' keyword
    [Tags]    unit    router    inference    detection
    ${type}=    Detect Query Type    Show conflicts between RULE-001 and RULE-002
    Should Be Equal    ${type}    inference

Detect Inference Query Rule ID
    [Documentation]    Inference: RULE-XXX pattern
    [Tags]    unit    router    inference    detection
    ${type}=    Detect Query Type    Show me RULE-012
    Should Be Equal    ${type}    inference

Detect Semantic Query About
    [Documentation]    Semantic: 'about' keyword
    [Tags]    unit    router    semantic    detection
    ${type}=    Detect Query Type    Tell me about authentication
    Should Be Equal    ${type}    semantic

Detect Semantic Query Find
    [Documentation]    Semantic: 'find' keyword
    [Tags]    unit    router    semantic    detection
    ${type}=    Detect Query Type    Find documents about security
    Should Be Equal    ${type}    semantic

Detect Semantic Query What Is
    [Documentation]    Semantic: 'what is' + question mark
    [Tags]    unit    router    semantic    detection
    ${type}=    Detect Query Type    What is the best practice for logging?
    Should Be Equal    ${type}    semantic

Ambiguous Query Defaults To Semantic
    [Documentation]    Ambiguous query defaults to semantic
    [Tags]    unit    router    semantic    default
    ${type}=    Detect Query Type    stuff
    Should Be Equal    ${type}    semantic

# =============================================================================
# ID Extraction Tests
# =============================================================================

Extract Rule ID From Text
    [Documentation]    Extract RULE-XXX from text
    [Tags]    unit    router    extraction    rule
    ${id}=    Extract Rule Id    What depends on RULE-001?
    Should Be Equal    ${id}    RULE-001
    ${id2}=    Extract Rule Id    No rule here
    Should Be Equal    ${id2}    None

Extract Decision ID From Text
    [Documentation]    Extract DECISION-XXX from text
    [Tags]    unit    router    extraction    decision
    ${id}=    Extract Decision Id    Per DECISION-001
    Should Be Equal    ${id}    DECISION-001
    ${id2}=    Extract Decision Id    No decision here
    Should Be Equal    ${id2}    None

# =============================================================================
# QueryResult Tests
# =============================================================================

QueryResult Creation
    [Documentation]    QueryResult with all fields
    [Tags]    unit    router    dataclass    result
    ${result}=    Test Query Result Creation
    Should Be Equal    ${result}[query]    test query
    Should Be Equal    ${result}[source]    chromadb
    Should Be Equal As Integers    ${result}[count]    1
    Should Be Equal    ${result}[fallback_used]    ${FALSE}
    Should Be Equal    ${result}[error]    ${NONE}

QueryResult With Error
    [Documentation]    QueryResult with error field
    [Tags]    unit    router    dataclass    error
    ${result}=    Test Query Result With Error
    Should Be Equal    ${result}[error]    Connection failed
    Should Be Equal As Integers    ${result}[count]    0

# =============================================================================
# Configuration Tests
# =============================================================================

Default Configuration
    [Documentation]    Default configuration from environment
    [Tags]    unit    router    config    default
    ${config}=    Test Default Config
    Should Be Equal    ${config}[typedb_host]    localhost
    Should Be Equal As Integers    ${config}[typedb_port]    1729
    Should Be Equal    ${config}[chromadb_host]    localhost
    Should Be Equal As Integers    ${config}[chromadb_port]    8001

Custom Configuration
    [Documentation]    Custom configuration override
    [Tags]    unit    router    config    custom
    ${config}=    Test Custom Config
    Should Be Equal    ${config}[typedb_host]    typedb.local
    Should Be Equal As Integers    ${config}[typedb_port]    1730
    Should Be Equal    ${config}[chromadb_host]    chroma.local
    Should Be Equal As Integers    ${config}[chromadb_port]    8002

# =============================================================================
# Query Execution Tests
# =============================================================================

Semantic Query No Client Returns Error
    [Documentation]    Semantic query without ChromaDB returns error
    [Tags]    unit    router    semantic    error
    ${result}=    Test Semantic Query No Client
    Should Be Equal    ${result}[error]    ChromaDB not connected
    Should Be Equal As Integers    ${result}[count]    0

Inference Query Fallback
    [Documentation]    Inference query without TypeDB falls back
    [Tags]    unit    router    inference    fallback
    ${result}=    Test Inference Query Fallback
    Should Be True    ${result}[fallback_used]

# =============================================================================
# Health Check Tests
# =============================================================================

Health Check No Connections
    [Documentation]    Health check with no active connections
    [Tags]    unit    router    health    check
    ${result}=    Test Health Check No Connections
    Should Be True    ${result}[has_typedb]
    Should Be True    ${result}[has_chromadb]
    Should Not Be True    ${result}[typedb_connected]
    Should Not Be True    ${result}[chromadb_connected]

# =============================================================================
# Memory Sync Bridge Tests
# =============================================================================

SyncStatus Creation
    [Documentation]    SyncStatus dataclass creation
    [Tags]    unit    router    sync    status
    ${result}=    Test Sync Status Creation
    Should Be Equal    ${result}[source]    typedb
    Should Be Equal As Integers    ${result}[synced_count]    10
    Should Be True    ${result}[errors_empty]

Memory Sync Bridge Rules
    [Documentation]    MemorySyncBridge sync_rules_to_chromadb
    [Tags]    unit    router    sync    rules
    ${result}=    Test Memory Sync Bridge
    Should Be Equal As Integers    ${result}[synced_count]    0
    Should Be True    ${result}[has_error]

Sync All Returns All Types
    [Documentation]    sync_all returns dict with all entity types
    [Tags]    unit    router    sync    all
    ${result}=    Test Sync All
    Should Be True    ${result}[has_rules]
    Should Be True    ${result}[has_decisions]
    Should Be True    ${result}[has_agents]
