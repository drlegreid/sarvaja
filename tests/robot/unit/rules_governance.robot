*** Settings ***
Documentation    Rules Governance Tests in ChromaDB
...              Tests for rules CRUD, indexing, and retrieval
...              Migrated from tests/test_rules_governance.py
Library          Collections
Library          ../../libs/RulesGovernanceLibrary.py
Resource         ../resources/common.resource
Force Tags             unit    integration    chromadb    rules    high    rule    validate    GOV-RULE-01-v1

*** Test Cases ***
# =============================================================================
# Rules Collection Tests
# =============================================================================

Test Rules Collection Create
    [Documentation]    Create rules collection in ChromaDB
    [Tags]    collection
    ${result}=    Rules Collection Create
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'ChromaDB unavailable')}
    Should Be True    ${result['success']}

Test Create Rule
    [Documentation]    Test creating a new rule
    [Tags]    crud    skip
    ${result}=    Create Rule
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Skipped')}
    Should Be True    ${result['success']}

Test Query Rules By Category
    [Documentation]    Test querying rules by category
    [Tags]    query    skip
    ${result}=    Query Rules By Category
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Skipped')}
    Should Be True    ${result['success']}

Test Update Rule Effectiveness
    [Documentation]    Test updating rule effectiveness score
    [Tags]    crud    skip
    ${result}=    Update Rule Effectiveness
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Skipped')}
    Should Be True    ${result['success']}

Test List All Rules
    [Documentation]    Test listing all rules
    [Tags]    query
    ${result}=    List All Rules
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'ChromaDB unavailable')}
    Should Be True    ${result['success']}

Test Delete Rule
    [Documentation]    Test deleting a rule (soft delete via status)
    [Tags]    crud    skip
    ${result}=    Delete Rule
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Skipped')}
    Should Be True    ${result['success']}

# =============================================================================
# Memory Management Tests
# =============================================================================

Test Memories Collection Create
    [Documentation]    Create memories collection in ChromaDB
    [Tags]    collection    memories
    ${result}=    Memories Collection Create
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'ChromaDB unavailable')}
    Should Be True    ${result['success']}

Test Store Memory
    [Documentation]    Test storing a memory
    [Tags]    memories    skip
    ${result}=    Store Memory
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Skipped')}
    Should Be True    ${result['success']}

Test Query Memories By Session
    [Documentation]    Test querying memories by session
    [Tags]    memories    skip
    ${result}=    Query Memories By Session
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Skipped')}
    Should Be True    ${result['success']}

# =============================================================================
# Session Logs Tests
# =============================================================================

Test Sessions Collection Create
    [Documentation]    Create sessions collection in ChromaDB
    [Tags]    collection    sessions
    ${result}=    Sessions Collection Create
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'ChromaDB unavailable')}
    Should Be True    ${result['success']}

Test Log Task
    [Documentation]    Test logging a task execution
    [Tags]    sessions    skip
    ${result}=    Log Task
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Skipped')}
    Should Be True    ${result['success']}

Test Query Tasks By Agent
    [Documentation]    Test querying tasks by agent
    [Tags]    sessions    skip
    ${result}=    Query Tasks By Agent
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Skipped')}
    Should Be True    ${result['success']}
