*** Settings ***
Documentation    RF-004: Unit Tests - MCP Tasks Tools
...              Migrated from tests/test_mcp_tasks.py
...              Per P10.4: Task CRUD MCP tools
Library          Collections
Library          ../../libs/MCPTasksLibrary.py
Force Tags        unit    mcp    tasks    high    ARCH-MCP-02-v1    task    validate

*** Test Cases ***
# =============================================================================
# Tools Existence Tests
# =============================================================================

Tasks Tools Importable
    [Documentation]    GIVEN mcp_tools.tasks WHEN import THEN works
    [Tags]    unit    mcp    tasks    tools    import
    ${result}=    Tasks Tools Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tasks tools not yet implemented
    Should Be True    ${result}[importable]

Tasks Tools Registered
    [Documentation]    GIVEN mcp_tools WHEN check THEN register_task_tools exported
    [Tags]    unit    mcp    tasks    tools    register
    ${result}=    Tasks Tools Registered
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    register_task_tools not exported
    Should Be True    ${result}[registered]

# =============================================================================
# Create Task Tests
# =============================================================================

Create Task Tool Exists
    [Documentation]    GIVEN compat WHEN check THEN governance_create_task callable
    [Tags]    unit    mcp    tasks    create    exists
    ${result}=    Create Task Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_create_task not yet exported
    Should Be True    ${result}[exists]

Create Task Returns JSON
    [Documentation]    GIVEN task data WHEN create THEN valid JSON
    [Tags]    integration    mcp    tasks    create    json
    ${result}=    Create Task Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_create_task not yet exported
    Should Be True    ${result}[is_dict]

Create Task Has Required Fields
    [Documentation]    GIVEN created task WHEN check THEN has fields
    [Tags]    integration    mcp    tasks    create    fields
    ${result}=    Create Task Has Required Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_create_task not yet exported
    Should Be True    ${result}[has_task_id]
    Should Be True    ${result}[has_name]
    Should Be True    ${result}[has_status]
    Should Be True    ${result}[has_message_or_no_error]

# =============================================================================
# Read Task Tests
# =============================================================================

Get Task Tool Exists
    [Documentation]    GIVEN compat WHEN check THEN governance_get_task callable
    [Tags]    unit    mcp    tasks    get    exists
    ${result}=    Get Task Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_get_task not yet exported
    Should Be True    ${result}[exists]

Get Task Returns JSON
    [Documentation]    GIVEN task_id WHEN get THEN valid JSON
    [Tags]    integration    mcp    tasks    get    json
    ${result}=    Get Task Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_get_task not yet exported
    Should Be True    ${result}[is_dict]

Get Task Returns Not Found
    [Documentation]    GIVEN nonexistent task WHEN get THEN handled
    [Tags]    integration    mcp    tasks    get    notfound
    ${result}=    Get Task Returns Not Found
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_get_task not yet exported
    Should Be True    ${result}[handled]

# =============================================================================
# Update Task Tests
# =============================================================================

Update Task Tool Exists
    [Documentation]    GIVEN compat WHEN check THEN governance_update_task callable
    [Tags]    unit    mcp    tasks    update    exists
    ${result}=    Update Task Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_update_task not yet exported
    Should Be True    ${result}[exists]

Update Task Status
    [Documentation]    GIVEN task WHEN update status THEN changed
    [Tags]    integration    mcp    tasks    update    status
    ${result}=    Update Task Status
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_update_task not yet exported
    Should Be True    ${result}[updated]

# =============================================================================
# Delete Task Tests
# =============================================================================

Delete Task Tool Exists
    [Documentation]    GIVEN compat WHEN check THEN governance_delete_task callable
    [Tags]    unit    mcp    tasks    delete    exists
    ${result}=    Delete Task Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_delete_task not yet exported
    Should Be True    ${result}[exists]

# =============================================================================
# TypeDB Operations Tests
# =============================================================================

Client Has Task Operations
    [Documentation]    GIVEN TypeDBClient WHEN check THEN has task CRUD
    [Tags]    integration    mcp    tasks    typedb    operations
    ${result}=    Client Has Task Operations
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    TypeDBClient not available
    Should Be True    ${result}[has_insert_task]
    Should Be True    ${result}[has_get_task]
    Should Be True    ${result}[has_update_task]
    Should Be True    ${result}[has_delete_task]

Insert Task To TypeDB
    [Documentation]    GIVEN task WHEN insert THEN persisted
    [Tags]    integration    mcp    tasks    typedb    insert
    ${result}=    Insert Task To TypeDB
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Cannot connect to TypeDB or not implemented
    Should Be True    ${result}[inserted]

Get All Tasks From TypeDB
    [Documentation]    GIVEN TypeDB WHEN get_all_tasks THEN returns list
    [Tags]    integration    mcp    tasks    typedb    query
    ${result}=    Get All Tasks From TypeDB
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Cannot connect to TypeDB or not implemented
    Should Be True    ${result}[is_list]
