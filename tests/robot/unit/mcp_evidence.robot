*** Settings ***
Documentation    RF-004: Unit Tests - MCP Evidence Tools
...              Migrated from tests/test_mcp_evidence.py
...              Per P9.1: Task/Session/Evidence MCP tools
Library          Collections
Library          ../../libs/MCPEvidenceLibrary.py
Library          ../../libs/MCPEvidenceAdvancedLibrary.py
Force Tags        unit    mcp    evidence    high    ARCH-MCP-02-v1    evidence-file    validate

*** Test Cases ***
# =============================================================================
# Tools Existence Tests
# =============================================================================

Compat Module Exists
    [Documentation]    GIVEN governance WHEN check THEN compat/__init__.py exists
    [Tags]    unit    mcp    evidence    compat    exists
    ${result}=    Compat Module Exists
    Should Be True    ${result}[exists]

Evidence Tools Defined
    [Documentation]    GIVEN compat WHEN check THEN evidence tools defined
    [Tags]    unit    mcp    evidence    tools    defined
    ${result}=    Evidence Tools Defined
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_list_sessions]
    Should Be True    ${result}[has_get_session]
    Should Be True    ${result}[has_list_decisions]
    Should Be True    ${result}[has_get_decision]
    Should Be True    ${result}[has_list_tasks]
    Should Be True    ${result}[has_get_task_deps]
    Should Be True    ${result}[has_evidence_search]

Evidence Tools Are Callable
    [Documentation]    GIVEN evidence tools WHEN check THEN all callable
    [Tags]    unit    mcp    evidence    tools    callable
    ${result}=    Evidence Tools Are Callable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[list_sessions_callable]
    Should Be True    ${result}[get_session_callable]
    Should Be True    ${result}[list_decisions_callable]
    Should Be True    ${result}[get_decision_callable]
    Should Be True    ${result}[list_tasks_callable]
    Should Be True    ${result}[get_task_deps_callable]
    Should Be True    ${result}[evidence_search_callable]

# =============================================================================
# Session Listing Tests
# =============================================================================

List Sessions Returns JSON
    [Documentation]    GIVEN governance_list_sessions WHEN call THEN valid JSON
    [Tags]    unit    mcp    evidence    session    list
    ${result}=    List Sessions Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[has_sessions]
    Should Be True    ${result}[has_count]
    Should Be True    ${result}[sessions_is_list]

List Sessions With Limit
    [Documentation]    GIVEN limit=5 WHEN list_sessions THEN respects limit
    [Tags]    unit    mcp    evidence    session    limit
    ${result}=    List Sessions With Limit
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[respects_limit]

Session Has Required Fields
    [Documentation]    GIVEN session WHEN check THEN has required fields
    [Tags]    unit    mcp    evidence    session    fields
    ${result}=    Session Has Required Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No sessions or tool unavailable
    Should Be True    ${result}[has_session_id]
    Should Be True    ${result}[has_date_or_topic]

# =============================================================================
# Session Retrieval Tests
# =============================================================================

Get Session Returns JSON
    [Documentation]    GIVEN session_id WHEN get_session THEN valid JSON
    [Tags]    unit    mcp    evidence    session    get
    ${result}=    Get Session Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[is_dict]

Get Session Not Found
    [Documentation]    GIVEN nonexistent session WHEN get THEN error
    [Tags]    unit    mcp    evidence    session    notfound
    ${result}=    Get Session Not Found
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[has_error]

# =============================================================================
# Decision Listing Tests
# =============================================================================

List Decisions Returns JSON
    [Documentation]    GIVEN governance_list_decisions WHEN call THEN valid JSON
    [Tags]    unit    mcp    evidence    decision    list
    ${result}=    List Decisions Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[has_decisions]
    Should Be True    ${result}[has_count]

Decision Has Required Fields
    [Documentation]    GIVEN decision WHEN check THEN has required fields
    [Tags]    unit    mcp    evidence    decision    fields
    ${result}=    Decision Has Required Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No decisions or tool unavailable
    Should Be True    ${result}[has_decision_id]
    Should Be True    ${result}[has_name_or_title]

# =============================================================================
# Decision Retrieval Tests
# =============================================================================

Get Decision Returns JSON
    [Documentation]    GIVEN decision_id WHEN get_decision THEN valid JSON
    [Tags]    unit    mcp    evidence    decision    get
    ${result}=    Get Decision Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[is_dict]

Get Decision Not Found
    [Documentation]    GIVEN nonexistent decision WHEN get THEN handled
    [Tags]    unit    mcp    evidence    decision    notfound
    ${result}=    Get Decision Not Found
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[handled]

# =============================================================================
# Task Listing Tests
# =============================================================================

List Tasks Returns JSON
    [Documentation]    GIVEN governance_list_tasks WHEN call THEN valid JSON
    [Tags]    unit    mcp    evidence    task    list
    ${result}=    List Tasks Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[has_tasks]
    Should Be True    ${result}[has_count]

List Tasks Filter By Phase
    [Documentation]    GIVEN phase=P7 WHEN list_tasks THEN filtered
    [Tags]    unit    mcp    evidence    task    filter
    ${result}=    List Tasks Filter By Phase
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[filtered]

List Tasks Filter By Status
    [Documentation]    GIVEN status=DONE WHEN list_tasks THEN filtered
    [Tags]    unit    mcp    evidence    task    status
    ${result}=    List Tasks Filter By Status
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[filtered]

Task Has Required Fields
    [Documentation]    GIVEN task WHEN check THEN has required fields
    [Tags]    unit    mcp    evidence    task    fields
    ${result}=    Task Has Required Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No tasks or tool unavailable
    Should Be True    ${result}[has_task_id]
    Should Be True    ${result}[has_status]
    Should Be True    ${result}[has_phase]

# =============================================================================
# Task Dependencies Tests
# =============================================================================

Get Task Deps Returns JSON
    [Documentation]    GIVEN task_id WHEN get_task_deps THEN valid JSON
    [Tags]    unit    mcp    evidence    task    deps
    ${result}=    Get Task Deps Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[has_task_id]
    Should Be True    ${result}[has_blocked_by]
    Should Be True    ${result}[has_blocks]

Task Deps Infers Phase Order
    [Documentation]    GIVEN P9.1 WHEN get_deps THEN has phase dependencies
    [Tags]    unit    mcp    evidence    task    phase
    ${result}=    Task Deps Infers Phase Order
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[has_dependencies]

# =============================================================================
# Evidence Search Tests
# =============================================================================

Evidence Search Returns JSON
    [Documentation]    GIVEN query WHEN evidence_search THEN valid JSON
    [Tags]    unit    mcp    evidence    search    json
    ${result}=    Evidence Search Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[has_query]
    Should Be True    ${result}[has_results]
    Should Be True    ${result}[has_search_method]

Evidence Search Respects Top K
    [Documentation]    GIVEN top_k=3 WHEN search THEN respects limit
    [Tags]    unit    mcp    evidence    search    topk
    ${result}=    Evidence Search Respects Top K
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[respects_top_k]

Evidence Search Result Has Fields
    [Documentation]    GIVEN search result WHEN check THEN has fields
    [Tags]    unit    mcp    evidence    search    fields
    ${result}=    Evidence Search Result Has Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No results or tool unavailable
    Should Be True    ${result}[has_source]
    Should Be True    ${result}[has_score]

# =============================================================================
# Evidence Directory Structure Tests
# =============================================================================

Evidence Dir Exists
    [Documentation]    GIVEN project WHEN check THEN evidence/ exists
    [Tags]    unit    mcp    evidence    directory    exists
    ${result}=    Evidence Dir Exists
    Should Be True    ${result}[exists]

Has Session Files
    [Documentation]    GIVEN evidence/ WHEN check THEN has SESSION-*.md
    [Tags]    unit    mcp    evidence    directory    sessions
    ${result}=    Has Session Files
    Should Be True    ${result}[has_sessions]

Backlog File Exists
    [Documentation]    GIVEN docs/backlog WHEN check THEN R&D-BACKLOG.md exists
    [Tags]    unit    mcp    evidence    directory    backlog
    ${result}=    Backlog File Exists
    Should Be True    ${result}[exists]

# =============================================================================
# Integration Tests
# =============================================================================

List Then Get Session
    [Documentation]    GIVEN list sessions WHEN get one THEN success
    [Tags]    unit    mcp    evidence    integration    session
    ${result}=    List Then Get Session
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No sessions or tool unavailable
    Should Be True    ${result}[success]

List Then Get Decision
    [Documentation]    GIVEN list decisions WHEN get one THEN success
    [Tags]    unit    mcp    evidence    integration    decision
    ${result}=    List Then Get Decision
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No decisions or tool unavailable
    Should Be True    ${result}[success]

Task List Filter Combinations
    [Documentation]    GIVEN phase+status WHEN filter THEN combined
    [Tags]    unit    mcp    evidence    integration    filter
    ${result}=    Task List Filter Combinations
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Tool unavailable
    Should Be True    ${result}[filtered]
