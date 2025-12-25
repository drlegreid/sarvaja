*** Settings ***
Documentation    Governance Dashboard Resources
...              Per RULE-004: Page Object Model (POM)
...              Per UI-FIRST-SPRINT-WORKFLOW.md: Spec-First TDD

Library          Browser    auto_closing_level=KEEP
Library          Collections
Library          String

*** Variables ***
${GOVERNANCE_URL}        http://localhost:8081/index.html
${TIMEOUT}               30s
${HEADLESS}              true

# Expected data-testid selectors (GAP-UI-001: Currently missing)
${NAV_RULES}             [data-testid="nav-rules"]
${NAV_DECISIONS}         [data-testid="nav-decisions"]
${NAV_SESSIONS}          [data-testid="nav-sessions"]
${NAV_TASKS}             [data-testid="nav-tasks"]
${NAV_SEARCH}            [data-testid="nav-search"]

# Rules List selectors - fallback to Vuetify classes when data-testid unavailable
${RULES_TABLE}           [data-testid="rules-table"], .v-data-table, .v-list
${RULES_ROW}             [data-testid="rule-row"], .v-data-table tbody tr, .v-list-item
${RULES_COL_ID}          [data-testid="rule-col-id"]
${RULES_COL_TITLE}       [data-testid="rule-col-title"]
${RULES_COL_STATUS}      [data-testid="rule-col-status"]
${RULES_ADD_BTN}         [data-testid="rules-add-btn"]

# Rules Detail selectors
${RULE_DETAIL}           [data-testid="rule-detail"]
${RULE_DETAIL_ID}        [data-testid="rule-detail-id"]
${RULE_DETAIL_TITLE}     [data-testid="rule-detail-title"]
${RULE_DETAIL_DIRECTIVE}    [data-testid="rule-detail-directive"]
${RULE_EDIT_BTN}         [data-testid="rule-detail-edit-btn"]

# Rules Form selectors
${RULE_FORM}             [data-testid="rule-form"]
${RULE_FORM_ID}          [data-testid="rule-form-id"]
${RULE_FORM_TITLE}       [data-testid="rule-form-title"]
${RULE_FORM_DIRECTIVE}   [data-testid="rule-form-directive"]
${RULE_FORM_SUBMIT}      [data-testid="rule-form-submit"]
${RULE_FORM_CANCEL}      [data-testid="rule-form-cancel"]

# Common selectors
${LOADING_SPINNER}       [data-testid="loading-spinner"]
${ERROR_BANNER}          [data-testid="error-banner"]
${EMPTY_STATE}           [data-testid="empty-state"]
${CONFIRM_DIALOG}        [data-testid="confirm-dialog"]

*** Keywords ***
# =============================================================================
# SETUP & TEARDOWN
# =============================================================================

Open Governance Dashboard
    [Documentation]    Open the Sim.ai Governance Dashboard
    New Browser    chromium    headless=${HEADLESS}
    New Context    viewport={'width': 1280, 'height': 720}
    New Page    ${GOVERNANCE_URL}
    Wait For Load State    networkidle    timeout=${TIMEOUT}

Close All Browsers Safely
    [Documentation]    Close all browsers with error handling
    ${status}=    Run Keyword And Return Status    Close Browser    ALL
    Log    Browser close status: ${status}

# =============================================================================
# NAVIGATION KEYWORDS
# =============================================================================

Navigate To Rules Tab
    [Documentation]    Click on Rules tab in navigation (or verify already there)
    # Rules is default view - just wait for content to be visible
    # Look for the card title "Governance Rules"
    Wait For Elements State    text=Governance Rules    visible    timeout=${TIMEOUT}

Navigate To Decisions Tab
    [Documentation]    Click on Decisions tab in navigation
    Click    ${NAV_DECISIONS}

Navigate To Sessions Tab
    [Documentation]    Click on Sessions tab in navigation
    Click    ${NAV_SESSIONS}

Navigate To Tasks Tab
    [Documentation]    Click on Tasks tab in navigation
    Click    ${NAV_TASKS}

Navigate To Search Tab
    [Documentation]    Click on Search tab in navigation
    Click    ${NAV_SEARCH}

# =============================================================================
# RULES LIST KEYWORDS
# =============================================================================

Rules List Should Be Visible
    [Documentation]    Verify rules list is displayed
    # Look for content that indicates rules are visible
    Wait For Elements State    text=Governance Rules    visible    timeout=${TIMEOUT}
    # Verify at least one rule is visible using first match
    ${count}=    Get Element Count    text=ACTIVE
    Should Be True    ${count} > 0    msg=No ACTIVE rules visible

Get Rules Count
    [Documentation]    Get number of rules in the table/list
    # Count list items or table rows depending on layout
    ${list_items}=    Get Element Count    .v-list-item
    IF    ${list_items} > 0
        RETURN    ${list_items}
    END
    ${rows}=    Get Elements    table tbody tr
    ${count}=    Get Length    ${rows}
    RETURN    ${count}

Rule Should Have ID Column
    [Documentation]    Verify rule_id column is present - GAP-UI-006: WILL FAIL
    Wait For Elements State    ${RULES_COL_ID}    visible    timeout=${TIMEOUT}

Rule Row Should Be Clickable
    [Documentation]    Verify rule rows are clickable - GAP-UI-007: WILL FAIL
    ${row}=    Get Element    ${RULES_ROW}
    Click    ${row}
    # Should navigate to detail view
    Wait For Elements State    ${RULE_DETAIL}    visible    timeout=${TIMEOUT}

Click Rule By ID
    [Documentation]    Click on a specific rule by ID - GAP-UI-007: WILL FAIL
    [Arguments]    ${rule_id}
    Click    text=${rule_id}
    Wait For Elements State    ${RULE_DETAIL}    visible    timeout=${TIMEOUT}

Click Rule By Index
    [Documentation]    Click on a rule by row index - GAP-UI-007: WILL FAIL
    [Arguments]    ${index}
    ${rows}=    Get Elements    table tbody tr
    Click    ${rows}[${index}]
    Wait For Elements State    ${RULE_DETAIL}    visible    timeout=${TIMEOUT}

# =============================================================================
# RULES DETAIL KEYWORDS - GAP-UI-003: Missing
# =============================================================================

Rule Detail Should Be Visible
    [Documentation]    Verify rule detail view is displayed - GAP-UI-003: WILL FAIL
    Wait For Elements State    ${RULE_DETAIL}    visible    timeout=${TIMEOUT}

Get Rule Detail ID
    [Documentation]    Get rule ID from detail view
    ${id}=    Get Text    ${RULE_DETAIL_ID}
    RETURN    ${id}

Get Rule Detail Title
    [Documentation]    Get rule title from detail view
    ${title}=    Get Text    ${RULE_DETAIL_TITLE}
    RETURN    ${title}

Get Rule Detail Directive
    [Documentation]    Get rule directive content from detail view
    ${directive}=    Get Text    ${RULE_DETAIL_DIRECTIVE}
    RETURN    ${directive}

Click Edit Rule Button
    [Documentation]    Click edit button on detail view
    Click    ${RULE_EDIT_BTN}
    Wait For Elements State    ${RULE_FORM}    visible    timeout=${TIMEOUT}

# =============================================================================
# RULES FORM KEYWORDS - GAP-UI-002: Missing
# =============================================================================

Click Add Rule Button
    [Documentation]    Click Add Rule button - GAP-UI-002: WILL FAIL
    Click    ${RULES_ADD_BTN}
    Wait For Elements State    ${RULE_FORM}    visible    timeout=${TIMEOUT}

Rule Form Should Be Visible
    [Documentation]    Verify rule form is displayed
    Wait For Elements State    ${RULE_FORM}    visible    timeout=${TIMEOUT}

Fill Rule Form
    [Documentation]    Fill out the rule form with provided data
    [Arguments]    ${rule_id}    ${title}    ${directive}
    Fill Text    ${RULE_FORM_ID}    ${rule_id}
    Fill Text    ${RULE_FORM_TITLE}    ${title}
    Fill Text    ${RULE_FORM_DIRECTIVE}    ${directive}

Submit Rule Form
    [Documentation]    Submit the rule form
    Click    ${RULE_FORM_SUBMIT}
    Wait For Elements State    ${RULE_FORM}    hidden    timeout=${TIMEOUT}

Cancel Rule Form
    [Documentation]    Cancel the rule form
    Click    ${RULE_FORM_CANCEL}
    Wait For Elements State    ${RULE_FORM}    hidden    timeout=${TIMEOUT}

# =============================================================================
# FILTER & SORT KEYWORDS - GAP-UI-010, GAP-UI-011: Missing
# =============================================================================

Filter Rules By Status
    [Documentation]    Filter rules by status - GAP-UI-011: WILL FAIL
    [Arguments]    ${status}
    Click    [data-testid="rules-filter-status"]
    Click    text=${status}

Sort Rules By Column
    [Documentation]    Sort rules by column header - GAP-UI-010: WILL FAIL
    [Arguments]    ${column}
    Click    [data-testid="rules-sort-${column}"]

Search Rules
    [Documentation]    Search rules by text - GAP-UI-011: WILL FAIL
    [Arguments]    ${query}
    Fill Text    [data-testid="rules-search"]    ${query}
    Press Keys    None    Enter

# =============================================================================
# COMMON ASSERTIONS
# =============================================================================

Should Not Have Errors
    [Documentation]    Verify no error messages are displayed
    ${has_error}=    Get Element Count    ${ERROR_BANNER}
    Should Be Equal As Integers    ${has_error}    0    msg=Error message displayed

Should Show Loading State
    [Documentation]    Verify loading spinner is displayed - GAP-UI-005
    Wait For Elements State    ${LOADING_SPINNER}    visible    timeout=5s

Should Hide Loading State
    [Documentation]    Verify loading spinner is hidden
    Wait For Elements State    ${LOADING_SPINNER}    hidden    timeout=${TIMEOUT}

Should Show Empty State
    [Documentation]    Verify empty state is displayed when no data
    Wait For Elements State    ${EMPTY_STATE}    visible    timeout=${TIMEOUT}
