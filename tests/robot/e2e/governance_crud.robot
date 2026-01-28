*** Settings ***
Documentation    RF-006: E2E Governance CRUD Tests
...              Per GAP-UI-028: Tests must verify actual functionality
...              Migrated from tests/e2e/test_governance_crud_e2e.py
Library          Collections
Library          ../../libs/GovernanceCRUDE2ELibrary.py
Test Tags        e2e    api    governance    high    rules    rule    task    create    read    delete    GOV-RULE-01-v1

Suite Teardown    Cleanup Test Data

*** Variables ***
${TEST_RULE_ID}       ${EMPTY}
${TEST_TASK_ID}       ${EMPTY}

*** Test Cases ***
# =============================================================================
# API Health Check
# =============================================================================

API Health Returns Status
    [Documentation]    Test health endpoint returns expected fields
    [Tags]    e2e    crud    health    smoke
    ${result}=    API Health Check
    ${healthy}=    Evaluate    $result.get('healthy', False)
    ${status_code}=    Set Variable    ${result}[status_code]
    Should Be Equal As Integers    ${status_code}    200
    ...    msg=Health check returned ${status_code}, expected 200 when services are running
    Should Be Equal    ${result}[status]    ok
    ...    msg=Expected status 'ok', got '${result.get("status", "MISSING")}'
    Should Be True    'typedb_connected' in $result
    ...    msg=Health response missing 'typedb_connected' field

# =============================================================================
# Rules CRUD Tests
# =============================================================================

Create Rule Via API
    [Documentation]    Test creating a new rule through API
    [Tags]    e2e    crud    rules    typedb
    ${typedb}=    Check TypeDB Available
    Skip If    not ${typedb}    TypeDB not connected
    ${rule_id}=    Generate Unique ID    TEST
    Set Suite Variable    ${TEST_RULE_ID}    ${rule_id}
    ${result}=    Create Rule    ${rule_id}    Test Rule ${rule_id}
    ...    category=technical    priority=HIGH    status=DRAFT
    Should Be True    ${result}[success]    Create failed: ${result}
    Should Be Equal    ${result}[rule][id]    ${rule_id}

List Rules Via API
    [Documentation]    Test listing rules through API
    [Tags]    e2e    crud    rules    typedb
    ${typedb}=    Check TypeDB Available
    Skip If    not ${typedb}    TypeDB not connected
    ${result}=    List Rules
    Should Be True    ${result}[success]    List failed: ${result}
    Should Be True    ${result}[count] >= 30
    ...    msg=Expected at least 30 rules (system has 36+), got ${result}[count]

Update Rule Via API
    [Documentation]    Test updating a rule through API
    [Tags]    e2e    crud    rules    typedb
    ${typedb}=    Check TypeDB Available
    Skip If    not ${typedb}    TypeDB not connected
    # Create first
    ${rule_id}=    Generate Unique ID    TEST
    ${create}=    Create Rule    ${rule_id}    Original Name
    Should Be True    ${create}[success]    Create failed
    # Update
    ${result}=    Update Rule    ${rule_id}    name=Updated Name    status=ACTIVE
    Should Be True    ${result}[success]    Update failed: ${result}
    Should Be Equal    ${result}[rule][name]    Updated Name
    Should Be Equal    ${result}[rule][status]    ACTIVE

Delete Rule Via API
    [Documentation]    Test deleting a rule through API
    [Tags]    e2e    crud    rules    typedb
    ${typedb}=    Check TypeDB Available
    Skip If    not ${typedb}    TypeDB not connected
    # Create first
    ${rule_id}=    Generate Unique ID    TEST
    ${create}=    Create Rule    ${rule_id}    To Delete
    Should Be True    ${create}[success]    Create failed
    # Delete
    ${result}=    Delete Rule    ${rule_id}
    Should Be True    ${result}[success]    Delete failed: ${result}
    # Verify deleted
    ${get}=    Get Rule    ${rule_id}
    Should Be Equal As Integers    ${get}[status_code]    404

# =============================================================================
# Tasks CRUD Tests
# =============================================================================

Create Task Via API
    [Documentation]    Test creating a new task through API
    [Tags]    e2e    crud    tasks
    ${task_id}=    Generate Unique ID    TEST
    Set Suite Variable    ${TEST_TASK_ID}    ${task_id}
    ${result}=    Create Task    ${task_id}    E2E Test Task ${task_id}
    ...    phase=P10    status=TODO
    Should Be True    ${result}[success]    Create failed: ${result}
    Should Be Equal    ${result}[task][task_id]    ${task_id}
    Should Be Equal    ${result}[task][status]    TODO

List Tasks Via API
    [Documentation]    Test listing tasks through API
    [Tags]    e2e    crud    tasks
    ${result}=    List Tasks
    Should Be True    ${result}[success]    List failed: ${result}
    Should Be True    ${result}[count] >= 10
    ...    msg=Expected at least 10 tasks (system has 50+), got ${result}[count]

Update Task Status Via API
    [Documentation]    Test updating task status through API
    [Tags]    e2e    crud    tasks
    ${task_id}=    Generate Unique ID    TEST
    ${create}=    Create Task    ${task_id}    Task to update    status=TODO
    Should Be True    ${create}[success]    Create failed
    # Update
    ${result}=    Update Task    ${task_id}    status=DONE    agent_id=code-agent
    Should Be True    ${result}[success]    Update failed: ${result}
    Should Be Equal    ${result}[task][status]    DONE
    Should Be Equal    ${result}[task][agent_id]    code-agent

Delete Task Via API
    [Documentation]    Test deleting a task through API
    [Tags]    e2e    crud    tasks
    ${task_id}=    Generate Unique ID    TEST
    ${create}=    Create Task    ${task_id}    Task to delete
    Should Be True    ${create}[success]    Create failed
    # Delete
    ${result}=    Delete Task    ${task_id}
    Should Be True    ${result}[success]    Delete failed: ${result}

Filter Tasks By Status
    [Documentation]    Test filtering tasks by status
    [Tags]    e2e    crud    tasks    filter
    # Create tasks with different statuses
    ${id1}=    Generate Unique ID    TEST
    ${id2}=    Generate Unique ID    TEST
    Create Task    ${id1}    TODO task    status=TODO
    Create Task    ${id2}    DONE task    status=DONE
    # Filter
    ${result}=    List Tasks    status=TODO
    Should Be True    ${result}[success]
    FOR    ${task}    IN    @{result}[tasks]
        Should Be Equal    ${task}[status]    TODO
    END

# =============================================================================
# Agent Task Backlog Tests
# =============================================================================

List Available Tasks
    [Documentation]    Test listing tasks available for agents
    [Tags]    e2e    crud    backlog    agents
    ${task_id}=    Generate Unique ID    TEST
    ${create}=    Create Task    ${task_id}    Available task
    Should Be True    ${create}[success]
    ${result}=    Get Available Tasks
    Should Be True    ${result}[success]    List available failed: ${result}
    ${task_ids}=    Evaluate    [t['task_id'] for t in $result['tasks']]
    Should Contain    ${task_ids}    ${task_id}

Claim Task By Agent
    [Documentation]    Test agent claiming a task
    [Tags]    e2e    crud    backlog    claim
    ${task_id}=    Generate Unique ID    TEST
    ${create}=    Create Task    ${task_id}    Task to claim
    Should Be True    ${create}[success]
    # Claim
    ${result}=    Claim Task    ${task_id}    code-agent
    Should Be True    ${result}[success]    Claim failed: ${result}
    Should Be Equal    ${result}[task][agent_id]    code-agent
    Should Be Equal    ${result}[task][status]    IN_PROGRESS

Claim Already Claimed Task Fails
    [Documentation]    Test that claiming an already-claimed task fails
    [Tags]    e2e    crud    backlog    conflict
    ${task_id}=    Generate Unique ID    TEST
    Create Task    ${task_id}    Already claimed task
    Claim Task    ${task_id}    code-agent
    # Try to claim again
    ${result}=    Claim Task    ${task_id}    review-agent
    ${success}=    Evaluate    $result.get('success', True)
    Should Not Be True    ${success}    Should fail with conflict
    Should Be Equal As Integers    ${result}[status_code]    409

Complete Task
    [Documentation]    Test completing a claimed task
    [Tags]    e2e    crud    backlog    complete
    ${task_id}=    Generate Unique ID    TEST
    Create Task    ${task_id}    Task to complete
    Claim Task    ${task_id}    code-agent
    # Complete
    ${result}=    Complete Task    ${task_id}    evidence=Tests passed
    Should Be True    ${result}[success]    Complete failed: ${result}
    Should Be Equal    ${result}[task][status]    DONE
    Should Be Equal    ${result}[task][evidence]    Tests passed

Claimed Task Not In Available
    [Documentation]    Test that claimed tasks don't appear in available list
    [Tags]    e2e    crud    backlog    availability
    ${task_id}=    Generate Unique ID    TEST
    Create Task    ${task_id}    Claimed task should not be available
    Claim Task    ${task_id}    code-agent
    # Check available
    ${result}=    Get Available Tasks
    ${task_ids}=    Evaluate    [t['task_id'] for t in $result['tasks']]
    Should Not Contain    ${task_ids}    ${task_id}

# =============================================================================
# Agents API Tests
# =============================================================================

List Agents Via API
    [Documentation]    Test listing registered agents
    [Tags]    e2e    crud    agents
    ${result}=    List Agents
    Should Be True    ${result}[success]    List failed: ${result}
    Should Be True    ${result}[count] > 0    Should have pre-configured agents
    ${agent}=    Get From List    ${result}[agents]    0
    Should Contain    ${agent}    agent_id
    Should Contain    ${agent}    name
    Should Contain    ${agent}    agent_type
    Should Contain    ${agent}    status
    Should Contain    ${agent}    trust_score

Get Specific Agent
    [Documentation]    Test getting a specific agent by ID
    [Tags]    e2e    crud    agents
    ${result}=    Get Agent    task-orchestrator
    Should Be True    ${result}[success]    Get failed: ${result}
    Should Be Equal    ${result}[agent][agent_id]    task-orchestrator
    Should Be Equal    ${result}[agent][name]    Task Orchestrator

Record Agent Task Execution
    [Documentation]    Test recording an agent task execution
    [Tags]    e2e    crud    agents    metrics
    # Get current state
    ${before}=    Get Agent    code-agent
    ${tasks_before}=    Set Variable    ${before}[agent][tasks_executed]
    # Record task
    ${result}=    Record Agent Task    code-agent
    Should Be True    ${result}[success]    Record failed: ${result}
    ${tasks_after}=    Evaluate    $result['agent']['tasks_executed']
    Should Be Equal As Integers    ${tasks_after}    ${${tasks_before} + 1}
