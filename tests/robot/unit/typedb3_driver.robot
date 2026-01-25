*** Settings ***
Documentation    RF-004: Unit Tests - TypeDB 3.x Driver Migration
...              Migrated from tests/unit/test_typedb3_driver.py
...              Per GAP-TYPEDB-DRIVER-001: TypeDB 3.x upgrade path
Library          Collections
Library          ../../libs/TypeDB3DriverLibrary.py

*** Test Cases ***
# =============================================================================
# TypeDB3 Driver API Tests
# =============================================================================

Driver Import Succeeds
    [Documentation]    GIVEN typedb-driver WHEN importing THEN succeeds
    [Tags]    unit    typedb    validate    driver
    ${result}=    Driver Import Succeeds
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    typedb-driver not installed
    Should Be True    ${result}[import_success]

Driver Requires Credentials
    [Documentation]    GIVEN TypeDB 3.x WHEN connecting THEN requires Credentials
    [Tags]    unit    typedb    validate    driver
    ${result}=    Driver Requires Credentials
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    typedb-driver 3.x not installed
    Should Be True    ${result}[credentials_available]

Driver Requires Options
    [Documentation]    GIVEN TypeDB 3.x WHEN connecting THEN requires DriverOptions
    [Tags]    unit    typedb    validate    driver
    ${result}=    Driver Requires Options
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    typedb-driver 3.x not installed
    Should Be True    ${result}[options_available]

# =============================================================================
# Schema Compatibility Tests
# =============================================================================

Cardinality Annotations Required
    [Documentation]    GIVEN TypeDB 3.x WHEN schema THEN cardinality required
    [Tags]    unit    typedb    validate    schema
    ${result}=    Cardinality Annotations Required
    Should Be True    ${result}[patterns_defined]
    ${len}=    Get Length    ${result}[patterns]
    Should Be Equal As Integers    ${len}    3

# =============================================================================
# API Changes Documentation Tests
# =============================================================================

API Changes Documented
    [Documentation]    GIVEN 2.x to 3.x migration WHEN checking THEN documented
    [Tags]    unit    typedb    validate    migration
    ${result}=    Api Changes Documented
    Should Be Equal As Integers    ${result}[changes_count]    5
    Should Be True    ${result}[all_documented]

Concept Rename Thing To Instance
    [Documentation]    GIVEN TypeDB 3.x WHEN checking THEN Thing renamed to Instance
    [Tags]    unit    typedb    validate    migration
    ${result}=    Concept Rename
    Should Be True    ${result}[thing_to_instance]

# =============================================================================
# Migration Steps Tests
# =============================================================================

Export Import Available
    [Documentation]    GIVEN TypeDB 3.x WHEN checking THEN export/import available
    [Tags]    unit    typedb    validate    migration
    ${result}=    Export Import Available
    Should Be True    ${result}[has_export]

Schema Migration Steps Defined
    [Documentation]    GIVEN migration WHEN checking THEN steps defined
    [Tags]    unit    typedb    validate    migration
    ${result}=    Schema Migration Steps
    Should Be Equal As Integers    ${result}[steps_count]    6
    Should Be True    ${result}[all_defined]

