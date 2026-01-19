*** Settings ***
Documentation    Exploratory Testing Heuristics for Sarvaja
...              Uses Playwright-based Browser Library with heuristic patterns
...              Per RULE-019: UI/UX Design Standards
Library          Browser    auto_closing_level=KEEP
Library          Collections
Library          String

*** Variables ***
${BASE_URL}              http://localhost:8081
${API_BASE_URL}          http://localhost:8082
${UI_URL}                ${BASE_URL}
${API_URL}               ${API_BASE_URL}/api/tasks
${TIMEOUT}               30s
${EXPLORATION_DEPTH}     3

# Heuristic patterns for UI exploration
@{INTERACTIVE_SELECTORS}    button    input    select    textarea    a[href]    [role="button"]
@{FORM_SELECTORS}           form    [role="form"]    .form    .task-form
@{STATUS_INDICATORS}        .status    [role="status"]    .badge    .chip    [aria-live]

*** Keywords ***
# =============================================================================
# SETUP & TEARDOWN
# =============================================================================

Open Task Console
    [Documentation]    Open the Sarvaja Task Console UI
    New Browser    chromium    headless=true
    New Context    viewport={'width': 1280, 'height': 720}
    New Page    ${UI_URL}
    Wait For Load State    networkidle    timeout=${TIMEOUT}

Close All Browsers Safely
    [Documentation]    Close all browsers with error handling
    ${status}=    Run Keyword And Return Status    Close Browser    ALL
    Log    Browser close status: ${status}

# =============================================================================
# EXPLORATORY HEURISTICS
# =============================================================================

Explore Page Structure
    [Documentation]    Heuristic: Discover page structure and key elements
    [Arguments]    ${depth}=${EXPLORATION_DEPTH}
    ${elements}=    Create Dictionary

    # Find all interactive elements
    FOR    ${selector}    IN    @{INTERACTIVE_SELECTORS}
        ${count}=    Get Element Count    ${selector}
        Set To Dictionary    ${elements}    ${selector}    ${count}
    END

    # Find forms
    ${forms}=    Get Element Count    form
    Set To Dictionary    ${elements}    forms    ${forms}

    # Find headings for structure
    ${headings}=    Get Element Count    h1, h2, h3
    Set To Dictionary    ${elements}    headings    ${headings}

    Log    Page structure: ${elements}
    RETURN    ${elements}

Discover Interactive Elements
    [Documentation]    Heuristic: Find and catalog all interactive UI elements
    ${buttons}=    Get Elements    button, [role="button"]
    ${inputs}=    Get Elements    input, textarea
    ${selects}=    Get Elements    select, [role="combobox"]
    ${links}=    Get Elements    a[href]

    ${interactive}=    Create Dictionary
    ...    buttons=${buttons}
    ...    inputs=${inputs}
    ...    selects=${selects}
    ...    links=${links}

    RETURN    ${interactive}

Check Accessibility Basics
    [Documentation]    Heuristic: Quick accessibility audit (per RULE-019 WCAG 2.1 AA)
    ${issues}=    Create List

    # Check for images without alt text
    ${img_no_alt}=    Get Element Count    img:not([alt])
    Run Keyword If    ${img_no_alt} > 0
    ...    Append To List    ${issues}    ${img_no_alt} images missing alt text

    # Check for form inputs without labels
    ${inputs}=    Get Elements    input:not([type="hidden"])
    FOR    ${input}    IN    @{inputs}
        ${has_label}=    Run Keyword And Return Status
        ...    Get Element    label[for="${input.id}"]
        Run Keyword If    not ${has_label}
        ...    Append To List    ${issues}    Input missing label
    END

    # Check for sufficient color contrast (basic)
    ${low_contrast}=    Get Element Count    [style*="color: #999"], [style*="color: gray"]
    Run Keyword If    ${low_contrast} > 0
    ...    Append To List    ${issues}    Potential low contrast text

    Log    Accessibility issues: ${issues}
    RETURN    ${issues}

Explore Form Behavior
    [Documentation]    Heuristic: Test form validation and submission patterns
    [Arguments]    ${form_selector}=form
    ${form_exists}=    Get Element Count    ${form_selector}
    Return From Keyword If    ${form_exists} == 0    ${EMPTY}

    ${results}=    Create Dictionary

    # Find submit button
    ${submit}=    Get Element Count    ${form_selector} button[type="submit"], ${form_selector} button:has-text("Submit")
    Set To Dictionary    ${results}    has_submit    ${submit > 0}

    # Find required fields
    ${required}=    Get Element Count    ${form_selector} [required], ${form_selector} [aria-required="true"]
    Set To Dictionary    ${results}    required_fields    ${required}

    # Check for validation messages
    ${validation}=    Get Element Count    ${form_selector} .error, ${form_selector} [role="alert"]
    Set To Dictionary    ${results}    has_validation    ${validation > 0}

    RETURN    ${results}

# =============================================================================
# TASK UI SPECIFIC KEYWORDS
# =============================================================================

Wait For Task Console Ready
    [Documentation]    Wait for Task Console to be fully loaded
    Wait For Elements State    header    visible    timeout=${TIMEOUT}
    Wait For Elements State    .task-form, form    visible    timeout=${TIMEOUT}

Get Available Agents
    [Documentation]    Get list of available agents from dropdown
    ${select}=    Get Element    select#agent, select[name="agent"], [role="combobox"]
    ${options}=    Get Select Options    ${select}
    RETURN    ${options}

Submit Task
    [Documentation]    Submit a task to an agent
    [Arguments]    ${prompt}    ${agent}=orchestrator

    # Select agent if dropdown exists
    ${has_select}=    Get Element Count    select#agent, select[name="agent"]
    Run Keyword If    ${has_select} > 0
    ...    Select Options By    select#agent    value    ${agent}

    # Fill prompt
    Fill Text    textarea#prompt, textarea[name="prompt"]    ${prompt}

    # Click submit
    Click    button:has-text("Submit"), button[type="submit"]

    # Wait for task creation
    Wait For Response    ${API_URL}    timeout=${TIMEOUT}

Wait For Task Event
    [Documentation]    Wait for specific AG-UI event type
    [Arguments]    ${event_type}    ${timeout}=${TIMEOUT}
    ${event_found}=    Set Variable    ${FALSE}

    Wait Until Keyword Succeeds    ${timeout}    1s
    ...    Element Should Contain Event Type    ${event_type}

    RETURN    ${event_found}

Element Should Contain Event Type
    [Documentation]    Check if event stream contains event type
    [Arguments]    ${event_type}
    ${text}=    Get Text    .event-stream, #eventStream, .event
    Should Contain    ${text}    ${event_type}

Get Task Status
    [Documentation]    Get current task status from UI
    ${status}=    Get Text    .task-status, [class*="status"], .badge
    RETURN    ${status}

# =============================================================================
# API EXPLORATION
# =============================================================================

Explore API Endpoints
    [Documentation]    Heuristic: Discover and test API endpoints
    ${results}=    Create Dictionary

    # Test health endpoint
    ${health}=    Http    GET    ${BASE_URL}/health
    Set To Dictionary    ${results}    health    ${health.status}

    # Test tasks list
    ${tasks}=    Http    GET    ${API_URL}
    Set To Dictionary    ${results}    tasks_list    ${tasks.status}

    # Test docs endpoint
    ${docs}=    Http    GET    ${BASE_URL}/docs
    Set To Dictionary    ${results}    docs    ${docs.status}

    RETURN    ${results}

Submit Task Via API
    [Documentation]    Submit task directly via API
    [Arguments]    ${prompt}    ${agent}=orchestrator
    ${body}=    Create Dictionary    prompt=${prompt}    agent=${agent}
    ${response}=    Http    POST    ${API_URL}    ${body}
    RETURN    ${response}

# =============================================================================
# SCREENSHOT & EVIDENCE
# =============================================================================

Capture Exploration Evidence
    [Documentation]    Capture screenshot and page state for evidence
    [Arguments]    ${name}=exploration
    ${timestamp}=    Get Time    epoch
    Take Screenshot    ${name}_${timestamp}
    ${html}=    Get Page Source
    Log    Page source captured: ${name}
