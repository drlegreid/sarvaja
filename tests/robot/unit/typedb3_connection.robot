*** Settings ***
Documentation    TypeDB 3.x Connection Component Tests
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/component/test_typedb3_connection.py
...              Tests TypeDB 3.x connection, queries, schema, migration.
Library          Collections
Library          ../../libs/TypeDB3ConnectionLibrary.py
Resource         ../resources/common.resource
Force Tags             component    typedb3    connection    medium    typedb    validate    ARCH-INFRA-01-v1

*** Test Cases ***
# =============================================================================
# Connection Tests
# =============================================================================

Test Connect To TypeDB3
    [Documentation]    Test connection to TypeDB 3.x server
    [Tags]    connection
    ${result}=    Connect To TypeDB3
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB 3.x not available')}
    Should Be True    ${result['connect_returned_true']}
    Should Be True    ${result['is_connected']}

Test TypeDB3 Health Check
    [Documentation]    Test health check returns correct info
    [Tags]    connection    health
    ${result}=    TypeDB3 Health Check
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB 3.x not available')}
    Should Be True    ${result['healthy']}
    Should Be True    ${result['has_databases']}
    Should Be True    ${result['driver_version_3x']}

Test TypeDB3 Database Exists
    [Documentation]    Test target database exists
    [Tags]    connection    database
    ${result}=    TypeDB3 Database Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB 3.x not available')}
    Should Be True    ${result['database_exists']}

# =============================================================================
# Query Tests
# =============================================================================

Test TypeDB3 Simple Match Query
    [Documentation]    Test simple match query
    [Tags]    query    match
    ${result}=    TypeDB3 Simple Match Query
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB 3.x not available')}
    Should Be True    ${result['returns_list']}

Test TypeDB3 Query Returns List
    [Documentation]    Query should always return a list
    [Tags]    query
    ${result}=    TypeDB3 Query Returns List
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB 3.x not available')}
    Should Be True    ${result['returns_list']}

Test TypeDB3 Write Query Requires Write Mode
    [Documentation]    Insert queries need read_only=False
    [Tags]    query    write
    ${result}=    TypeDB3 Write Query Requires Write Mode
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB 3.x not available')}
    Should Be True    ${result['raises_exception']}

# =============================================================================
# Schema Tests
# =============================================================================

Test TypeDB3 Query Schema Types
    [Documentation]    Query schema types
    [Tags]    schema
    ${result}=    TypeDB3 Query Schema Types
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB 3.x not available')}
    Should Be True    ${result['returns_list']}

# =============================================================================
# Migration Verification Tests
# =============================================================================

Test TypeDB3 Rules Exist After Migration
    [Documentation]    All rules should exist after migration
    [Tags]    migration    rules
    ${result}=    TypeDB3 Rules Exist After Migration
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB 3.x not available')}
    Should Be True    ${result['returns_list']}
    Should Be True    ${result['has_rules']}

Test TypeDB3 Tasks Exist After Migration
    [Documentation]    All tasks should exist after migration
    [Tags]    migration    tasks
    ${result}=    TypeDB3 Tasks Exist After Migration
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB 3.x not available')}
    Should Be True    ${result['returns_list']}

Test TypeDB3 Sessions Exist After Migration
    [Documentation]    Sessions should exist after migration
    [Tags]    migration    sessions
    ${result}=    TypeDB3 Sessions Exist After Migration
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB 3.x not available')}
    Should Be True    ${result['returns_list']}
