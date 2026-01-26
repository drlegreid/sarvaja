*** Settings ***
Documentation    Rules Integration and Edge Case Tests
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/rules/test_integration.py
...              Tests complete CRUD cycle and edge cases.
Library          Collections
Library          ../../libs/RulesIntegrationLibrary.py
Resource         ../resources/common.resource
Tags             unit    rules    integration

*** Test Cases ***
# =============================================================================
# Integration Tests (Require TypeDB)
# =============================================================================

Test Full CRUD Cycle
    [Documentation]    Test complete CRUD cycle: create, read, update, deprecate, delete
    [Tags]    integration    typedb    crud
    ${result}=    Full CRUD Cycle Requires TypeDB
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB not available')}
    Should Be True    ${result['create_ok']}
    Should Be True    ${result['read_ok']}
    Should Be True    ${result['update_ok']}
    Should Be True    ${result['deprecate_ok']}
    Should Be True    ${result['delete_ok']}
    Should Be True    ${result['verify_deleted_ok']}

# =============================================================================
# Edge Case Tests
# =============================================================================

Test Valid Categories
    [Documentation]    Test all valid categories are defined
    [Tags]    edge-case    categories
    ${result}=    Valid Categories List
    Should Be True    ${result['count_correct']}

Test Valid Priorities
    [Documentation]    Test all valid priorities are defined
    [Tags]    edge-case    priorities
    ${result}=    Valid Priorities List
    Should Be True    ${result['count_correct']}

Test Valid Statuses
    [Documentation]    Test all valid statuses are defined
    [Tags]    edge-case    statuses
    ${result}=    Valid Statuses List
    Should Be True    ${result['count_correct']}

Test Rule Dataclass Fields
    [Documentation]    Test Rule dataclass has expected fields
    [Tags]    edge-case    dataclass
    ${result}=    Rule Dataclass Has Fields
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_id']}
    Should Be True    ${result['has_name']}
    Should Be True    ${result['has_category']}
    Should Be True    ${result['has_priority']}
    Should Be True    ${result['has_status']}
    Should Be True    ${result['has_directive']}

Test Rule To Dict
    [Documentation]    Test Rule can be converted to dict
    [Tags]    edge-case    serialization
    ${result}=    Rule To Dict Conversion
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['id_matches']}
    Should Be True    ${result['name_matches']}
    Should Be True    ${result['category_matches']}
