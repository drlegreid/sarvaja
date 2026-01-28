*** Settings ***
Documentation    MCP REST API Session Integration Tests
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/integration/test_mcp_rest_sessions.py
...              Tests session/task operations via REST API.
Library          Collections
Library          ../../libs/MCPRestSessionsLibrary.py
Resource         ../resources/common.resource
Force Tags             integration    mcp    rest    sessions    medium    session    read    ARCH-MCP-02-v1

*** Test Cases ***
# =============================================================================
# Session Tests
# =============================================================================

Test List Sessions Via REST
    [Documentation]    MCP-001-D: Can list sessions via REST API
    [Tags]    sessions    list
    ${result}=    List Sessions Via REST
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['returns_list']}

Test Create Session Via REST
    [Documentation]    MCP-001-A: Can create session via REST API
    [Tags]    sessions    create
    ${result}=    Create Session Via REST
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['status_201']}
    Should Be True    ${result['id_matches']}

Test Get Tasks With Sessions
    [Documentation]    MCP-002-A: Tasks and sessions can be queried together
    [Tags]    sessions    tasks
    ${result}=    Get Tasks With Sessions
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['tasks_ok']}
    Should Be True    ${result['sessions_ok']}

Test Health Includes TypeDB
    [Documentation]    MCP-003-A: Health endpoint shows TypeDB status
    [Tags]    health    typedb
    ${result}=    Health Includes TypeDB
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['has_typedb_field']}
    Should Be True    ${result['typedb_connected']}

# =============================================================================
# Task Tests
# =============================================================================

Test List Tasks Via REST
    [Documentation]    Can list tasks via REST API
    [Tags]    tasks    list
    ${result}=    List Tasks Via REST
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['status_200']}
    Should Be True    ${result['returns_list']}

Test Create Task Via REST
    [Documentation]    MCP-002-A: Can create task via REST API
    [Tags]    tasks    create
    ${result}=    Create Task Via REST
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['status_201']}
    Should Be True    ${result['id_matches']}

Test Task Persistence Round Trip
    [Documentation]    GAP-API-001 FIXED: Tasks persist to TypeDB
    [Tags]    tasks    persistence    GAP-API-001
    ${result}=    Task Persistence Round Trip
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['persisted']}

# =============================================================================
# Session-Task Relationship Tests
# =============================================================================

Test Session Tasks Endpoint Exists
    [Documentation]    GAP-UI-SESSION-TASKS-001: /api/sessions/{id}/tasks exists
    [Tags]    session-tasks    endpoint
    ${result}=    Session Tasks Endpoint Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['endpoint_exists']}

Test Session Tasks Returns Linked Tasks
    [Documentation]    GAP-UI-SESSION-TASKS-001: Session returns linked tasks
    [Tags]    session-tasks    linked
    ${result}=    Session Tasks Returns Linked Tasks
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['has_tasks']}

Test Session Tasks Count Matches
    [Documentation]    GAP-UI-SESSION-TASKS-001: task_count matches actual
    [Tags]    session-tasks    count
    ${result}=    Session Tasks Count Matches
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['count_matches']}

Test Task Has Linked Sessions
    [Documentation]    GAP-UI-TASK-SESSION-001: Task returns linked_sessions
    [Tags]    task-sessions    linked
    ${result}=    Task Has Linked Sessions
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['has_linked_sessions_field']}

# =============================================================================
# Rules Tests
# =============================================================================

Test List Rules Via REST
    [Documentation]    MCP-003-B: Can list rules via REST API
    [Tags]    rules    list
    ${result}=    List Rules Via REST
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['returns_list']}
    Should Be True    ${result['has_rules']}

Test Rules Have Structure
    [Documentation]    Rules have expected structure
    [Tags]    rules    structure
    ${result}=    Rules Have Structure
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['has_id']}
    Should Be True    ${result['has_content']}
