*** Settings ***
Documentation    RF-004: Unit Tests - Rules Search Module
...              Migrated from tests/unit/test_rules_search.py
...              Per GAP-UI-SEARCH-001: Server-side rule search testing
Library          Collections
Library          ../../libs/RulesSearchLibrary.py

Suite Setup      Initialize Mock Rules

*** Test Cases ***
# =============================================================================
# Search by ID Tests
# =============================================================================

Search By Exact ID Returns Single Match
    [Documentation]    GIVEN rules WHEN searching by exact ID THEN returns matching rule
    [Tags]    unit    rules    search    id
    ${result}=    Filter Rules By Search    CONTAINER-LIFECYCLE-01-v1
    ${count}=    Get Result Count    ${result}
    Should Be Equal As Integers    ${count}    1
    ${ids}=    Get Result Ids    ${result}
    List Should Contain Value    ${ids}    CONTAINER-LIFECYCLE-01-v1

Search By Partial ID Returns Match
    [Documentation]    GIVEN rules WHEN searching by partial ID THEN returns matching rules
    [Tags]    unit    rules    search    id
    ${result}=    Filter Rules By Search    container
    ${count}=    Get Result Count    ${result}
    Should Be Equal As Integers    ${count}    1
    ${ids}=    Get Result Ids    ${result}
    List Should Contain Value    ${ids}    CONTAINER-LIFECYCLE-01-v1

# =============================================================================
# Search by Name Tests
# =============================================================================

Search By Name Returns Match
    [Documentation]    GIVEN rules WHEN searching by name THEN returns matching rules
    [Tags]    unit    rules    search    name
    ${result}=    Filter Rules By Search    Evidence
    ${count}=    Get Result Count    ${result}
    Should Be Equal As Integers    ${count}    1

# =============================================================================
# Search by Directive Tests
# =============================================================================

Search By Directive Content Returns Match
    [Documentation]    GIVEN rules WHEN searching by directive THEN returns matching rules
    [Tags]    unit    rules    search    directive
    ${result}=    Filter Rules By Search    podman
    ${count}=    Get Result Count    ${result}
    Should Be Equal As Integers    ${count}    1
    ${ids}=    Get Result Ids    ${result}
    List Should Contain Value    ${ids}    CONTAINER-LIFECYCLE-01-v1

# =============================================================================
# Case Sensitivity Tests
# =============================================================================

Search Is Case Insensitive
    [Documentation]    GIVEN rules WHEN searching with different case THEN returns matches
    [Tags]    unit    rules    search    case
    ${result}=    Filter Rules By Search    SESSION
    ${count}=    Get Result Count    ${result}
    Should Be Equal As Integers    ${count}    1

# =============================================================================
# Multiple Match Tests
# =============================================================================

Search Returns Multiple Matches
    [Documentation]    GIVEN rules WHEN term matches multiple THEN returns all
    [Tags]    unit    rules    search    multiple
    ${result}=    Filter Rules By Search    MUST
    ${count}=    Get Result Count    ${result}
    Should Be True    ${count} >= 2    Multiple rules should have MUST in directive

# =============================================================================
# Edge Cases
# =============================================================================

Search No Match Returns Empty
    [Documentation]    GIVEN rules WHEN searching non-existent term THEN returns empty
    [Tags]    unit    rules    search    edge
    ${result}=    Filter Rules By Search    nonexistentterm12345
    ${count}=    Get Result Count    ${result}
    Should Be Equal As Integers    ${count}    0

Search Empty Query Returns All
    [Documentation]    GIVEN rules WHEN query is empty THEN returns all rules
    [Tags]    unit    rules    search    edge
    ${result}=    Filter Rules By Search    ${EMPTY}
    ${count}=    Get Result Count    ${result}
    Should Be Equal As Integers    ${count}    4

*** Keywords ***
Initialize Mock Rules
    [Documentation]    Create mock rules for all tests
    Create Mock Rules
