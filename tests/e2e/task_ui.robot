*** Settings ***
Documentation    E2E Tests for Sarvaja Task UI
...              Uses Robot Framework + Playwright with exploratory heuristics
...              Per Phase 7: E2E Testing Infrastructure
...              Per RULE-019: UI/UX Design Standards

Resource         resources/exploratory.resource
Library          Browser    auto_closing_level=KEEP
Library          Collections
Library          OperatingSystem

Suite Setup      Suite Initialization
Suite Teardown   Close All Browsers Safely
Test Timeout     60 seconds

*** Variables ***
${AGENT_URL}     http://localhost:8081
${UI_URL}        ${AGENT_URL}
${HEADLESS}      true

*** Test Cases ***
# =============================================================================
# SMOKE TESTS
# =============================================================================

Task Console Loads Successfully
    [Documentation]    Verify Task Console UI loads without errors
    [Tags]    smoke    ui
    Open Task Console
    Wait For Task Console Ready
    Page Should Not Contain    Error
    Page Should Not Contain    500
    Capture Exploration Evidence    smoke_load

Page Structure Is Valid
    [Documentation]    Verify page has expected structure (exploratory heuristic)
    [Tags]    smoke    exploratory
    ${structure}=    Explore Page Structure
    Dictionary Should Contain Key    ${structure}    button
    Should Be True    ${structure['button']} > 0    msg=No buttons found

# =============================================================================
# FORM TESTS
# =============================================================================

Task Form Is Present
    [Documentation]    Verify task submission form exists
    [Tags]    form    ui
    Wait For Elements State    form, .task-form    visible
    ${form_info}=    Explore Form Behavior
    Should Be True    ${form_info['has_submit']}    msg=No submit button found

Agent Dropdown Has Options
    [Documentation]    Verify agent dropdown is populated
    [Tags]    form    ui
    ${agents}=    Get Available Agents
    ${count}=    Get Length    ${agents}
    Should Be True    ${count} >= 1    msg=No agents in dropdown
    Log    Available agents: ${agents}

Empty Prompt Shows Validation
    [Documentation]    Verify form validates empty prompt
    [Tags]    form    validation
    # Clear prompt and try submit
    Fill Text    textarea#prompt, textarea[name="prompt"]    ${EMPTY}
    Click    button:has-text("Submit"), button[type="submit"]
    # Either form doesn't submit or shows validation
    ${submitted}=    Run Keyword And Return Status
    ...    Wait For Response    ${AGENT_URL}/tasks    timeout=2s
    IF    ${submitted}
        Fail    Empty prompt should not submit
    END

# =============================================================================
# TASK SUBMISSION TESTS
# =============================================================================

Submit Simple Task
    [Documentation]    Submit a basic task and verify response
    [Tags]    task    functional
    ${prompt}=    Set Variable    Hello, this is a test task
    Submit Task    ${prompt}    orchestrator

    # Wait for task to appear in list
    Wait For Elements State    .task-item, .task-list *    visible    timeout=10s
    Capture Exploration Evidence    task_submitted

Task Appears In Recent List
    [Documentation]    Verify submitted task appears in task list
    [Tags]    task    functional
    ${prompt}=    Set Variable    Test task for list verification
    Submit Task    ${prompt}

    # Task should appear in list
    Wait Until Keyword Succeeds    10s    1s
    ...    Page Should Contain    TASK-

Verify Task ID Format
    [Documentation]    Task IDs should follow TASK-XXXXXXXX format
    [Tags]    task    format
    Submit Task    Format test task
    Wait For Elements State    .task-id, [class*="task-id"]    visible    timeout=10s

    ${task_id}=    Get Text    .task-id, [class*="task-id"]
    Should Match Regexp    ${task_id}    TASK-[A-Z0-9]{8}

# =============================================================================
# AG-UI EVENT STREAM TESTS
# =============================================================================

Event Stream Shows RUN_STARTED
    [Documentation]    Verify RUN_STARTED event appears after task submit
    [Tags]    events    agui
    Submit Task    Event stream test

    # Wait for RUN_STARTED event
    Wait Until Keyword Succeeds    15s    1s
    ...    Page Should Contain    RUN_STARTED

Event Stream Shows Progress
    [Documentation]    Verify progress events appear during execution
    [Tags]    events    agui
    Submit Task    Progress tracking test

    # Look for any progress indicator
    Wait Until Keyword Succeeds    20s    2s
    ...    Page Should Contain One Of    STATE_DELTA    TEXT_MESSAGE

Event Stream Completes
    [Documentation]    Verify RUN_FINISHED or RUN_ERROR event appears
    [Tags]    events    agui
    Submit Task    Completion test

    # Wait for completion event
    Wait Until Keyword Succeeds    30s    2s
    ...    Page Should Contain One Of    RUN_FINISHED    RUN_ERROR

# =============================================================================
# ACCESSIBILITY TESTS
# =============================================================================

Basic Accessibility Check
    [Documentation]    Quick accessibility audit per RULE-019
    [Tags]    accessibility    a11y
    ${issues}=    Check Accessibility Basics
    ${count}=    Get Length    ${issues}
    Log    Accessibility issues found: ${count}
    # Warn but don't fail (informational)
    IF    ${count} > 0
        Log    WARNING: ${count} accessibility issues: ${issues}    WARN
    END

Keyboard Navigation Works
    [Documentation]    Verify form can be navigated with keyboard
    [Tags]    accessibility    keyboard
    # Focus on first input
    Keyboard Key    press    Tab
    ${focused}=    Get Element State    :focus    visible
    Should Be True    ${focused}

    # Tab through form
    Keyboard Key    press    Tab
    Keyboard Key    press    Tab
    # Should still be able to interact
    ${focused2}=    Get Element State    :focus    visible
    Should Be True    ${focused2}

# =============================================================================
# API TESTS (via Browser)
# =============================================================================

API Health Check
    [Documentation]    Verify API is healthy
    [Tags]    api    health
    ${response}=    Http    ${AGENT_URL}/health    method=GET
    Should Be Equal As Integers    ${response.status}    200

API Tasks Endpoint Works
    [Documentation]    Verify tasks API returns valid response
    [Tags]    api    functional
    ${response}=    Http    ${AGENT_URL}/tasks    method=GET
    Should Be Equal As Integers    ${response.status}    200

API Task Submission Works
    [Documentation]    Verify task can be submitted via API
    [Tags]    api    functional
    ${body}=    Create Dictionary    prompt=API test task    agent=orchestrator
    ${response}=    Http    ${AGENT_URL}/tasks    method=POST    body=${body}
    Should Be Equal As Integers    ${response.status}    200
    Dictionary Should Contain Key    ${response.body}    task_id

# =============================================================================
# EXPLORATORY SESSION
# =============================================================================

Full Exploratory Audit
    [Documentation]    Complete exploratory testing session
    [Tags]    exploratory    audit
    # Explore structure
    ${structure}=    Explore Page Structure
    Log    Structure: ${structure}

    # Explore interactions
    ${interactive}=    Discover Interactive Elements
    Log    Interactive elements: ${interactive}

    # Explore forms
    ${forms}=    Explore Form Behavior
    Log    Form behavior: ${forms}

    # Explore API
    ${api}=    Explore API Endpoints
    Log    API endpoints: ${api}

    # Capture evidence
    Capture Exploration Evidence    full_audit

*** Keywords ***
Suite Initialization
    [Documentation]    Initialize test suite
    Log    Starting E2E tests for Sarvaja Task UI
    Log    Target: ${AGENT_URL}
    New Browser    chromium    headless=${HEADLESS}
    New Context    viewport={'width': 1280, 'height': 720}
    New Page    ${UI_URL}
    Wait For Load State    networkidle    timeout=30s

Page Should Contain One Of
    [Documentation]    Verify page contains at least one of the given texts
    [Arguments]    @{texts}
    FOR    ${text}    IN    @{texts}
        ${status}=    Run Keyword And Return Status
        ...    Page Should Contain    ${text}
        IF    ${status}    RETURN
    END
    Fail    Page should contain one of: ${texts}
