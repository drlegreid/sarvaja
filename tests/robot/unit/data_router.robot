*** Settings ***
Documentation    RF-004: Unit Tests - Data Router
...              Migrated from tests/test_data_router.py
...              Per P7.3: Routing new data to TypeDB
Library          Collections
Library          ../../libs/DataRouterLibrary.py
Force Tags        unit    data    routing    medium    rule    read    ARCH-MCP-02-v1

*** Test Cases ***
# =============================================================================
# Module Existence Tests
# =============================================================================

Data Router Module Exists
    [Documentation]    GIVEN governance/ WHEN checking THEN data_router.py exists
    [Tags]    unit    data-router    validate    module
    ${result}=    Data Router Module Exists
    Should Be True    ${result}[exists]

Data Router Class Importable
    [Documentation]    GIVEN data_router WHEN importing THEN DataRouter available
    [Tags]    unit    data-router    validate    module
    ${result}=    Data Router Class Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[instantiable]

Router Has Required Methods
    [Documentation]    GIVEN router WHEN checking THEN has required methods
    [Tags]    unit    data-router    validate    module
    ${result}=    Router Has Required Methods
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_route_rule]
    Should Be True    ${result}[has_route_decision]
    Should Be True    ${result}[has_route_session]
    Should Be True    ${result}[has_route_auto]

# =============================================================================
# Rule Routing Tests
# =============================================================================

Route New Rule Works
    [Documentation]    GIVEN rule data WHEN route_rule THEN routes to TypeDB
    [Tags]    unit    data-router    validate    routing
    ${result}=    Route New Rule Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[success]
    Should Be True    ${result}[destination_typedb]

Route Rule Generates Embedding
    [Documentation]    GIVEN embed=True WHEN route_rule THEN generates embedding
    [Tags]    unit    data-router    validate    routing    embedding
    ${result}=    Route Rule Generates Embedding
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[embedded]

Route Rule Validates Data
    [Documentation]    GIVEN invalid data WHEN route_rule THEN rejects
    [Tags]    unit    data-router    validate    routing    validation
    ${result}=    Route Rule Validates Data
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[rejects_invalid]
    Should Be True    ${result}[has_error]

# =============================================================================
# Decision Routing Tests
# =============================================================================

Route New Decision Works
    [Documentation]    GIVEN decision data WHEN route_decision THEN routes to TypeDB
    [Tags]    unit    data-router    validate    routing
    ${result}=    Route New Decision Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[success]
    Should Be True    ${result}[destination_typedb]

