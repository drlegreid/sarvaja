*** Settings ***
Documentation    Rules CRUD E2E Tests - Spec-First TDD (RED Phase)
...              Per RULE-004: Page Object Model (POM)
...              Per UI-FIRST-SPRINT-WORKFLOW.md: Spec-First TDD
...              Per ENTITY-API-UI-MAP.md: Rule entity specification
...
...              These tests define the EXPECTED behavior of the Rules UI.
...              Currently in RED phase - all tests SHOULD FAIL until UI implemented.
...
...              Gaps addressed:
...              - GAP-UI-001: No data-testid attributes (all locators)
...              - GAP-UI-002: No CRUD forms (CREATE/UPDATE tests)
...              - GAP-UI-003: No detail drill-down (READ detail tests)
...              - GAP-UI-006: Rules list missing rule_id column
...              - GAP-UI-007: List rows not clickable
...              - GAP-UI-010: No column sorting
...              - GAP-UI-011: No filtering/faceted search

Resource         resources/governance.resource
Library          Browser    auto_closing_level=KEEP
Library          Collections

Suite Setup      Open Governance Dashboard
Suite Teardown   Close All Browsers Safely
Test Timeout     60 seconds

*** Variables ***
${TEST_RULE_ID}      RULE-TEST-001
${TEST_RULE_TITLE}   Test Rule for TDD
${TEST_RULE_DIR}     This is a test directive for TDD verification.

*** Test Cases ***
# =============================================================================
# LIST VIEW TESTS
# =============================================================================

Rules Tab Loads Successfully
    [Documentation]    Smoke test: Rules tab loads without errors
    [Tags]    smoke    list    P0
    Navigate To Rules Tab
    Rules List Should Be Visible
    Should Not Have Errors

Rules List Shows All Rules
    [Documentation]    Rules list displays expected number of rules
    [Tags]    list    P0
    Navigate To Rules Tab
    ${count}=    Get Rules Count
    Should Be True    ${count} >= 11    msg=Expected at least 11 rules (per exploration)

Rules List Has Rule ID Column
    [Documentation]    GAP-UI-006: Rule ID column should be visible
    [Tags]    list    gap-ui-006    will-fail
    Navigate To Rules Tab
    Rule Should Have ID Column

Rules List Has All Expected Columns
    [Documentation]    List should have all DSM-specified columns
    [Tags]    list    dsm    will-fail
    Navigate To Rules Tab
    # Per ENTITY-API-UI-MAP.md: columns [rule_id, title, status, category, priority]
    Wait For Elements State    [data-testid="rule-col-id"]    visible
    Wait For Elements State    [data-testid="rule-col-title"]    visible
    Wait For Elements State    [data-testid="rule-col-status"]    visible
    Wait For Elements State    [data-testid="rule-col-category"]    visible
    Wait For Elements State    [data-testid="rule-col-priority"]    visible

Rules List Rows Are Clickable
    [Documentation]    GAP-UI-007: Clicking rule row navigates to detail
    [Tags]    list    navigation    gap-ui-007    will-fail
    Navigate To Rules Tab
    Rule Row Should Be Clickable

Rules List Has Add Button
    [Documentation]    GAP-UI-002: Add Rule button should be visible
    [Tags]    list    crud    gap-ui-002    will-fail
    Navigate To Rules Tab
    Wait For Elements State    ${RULES_ADD_BTN}    visible

# =============================================================================
# DETAIL VIEW TESTS - GAP-UI-003
# =============================================================================

Rule Detail View Exists
    [Documentation]    GAP-UI-003: Detail view accessible when clicking rule
    [Tags]    detail    gap-ui-003    will-fail
    Navigate To Rules Tab
    Click Rule By ID    RULE-001
    Rule Detail Should Be Visible

Rule Detail Shows All Fields
    [Documentation]    Detail view displays all rule fields
    [Tags]    detail    dsm    will-fail
    Navigate To Rules Tab
    Click Rule By ID    RULE-001
    # Per ENTITY-API-UI-MAP.md: Header, metadata, content, relations
    ${id}=    Get Rule Detail ID
    Should Be Equal    ${id}    RULE-001
    ${title}=    Get Rule Detail Title
    Should Not Be Empty    ${title}
    ${directive}=    Get Rule Detail Directive
    Should Not Be Empty    ${directive}

Rule Detail Has Edit Button
    [Documentation]    Detail view has edit action
    [Tags]    detail    crud    will-fail
    Navigate To Rules Tab
    Click Rule By ID    RULE-001
    Wait For Elements State    ${RULE_EDIT_BTN}    visible

Rule Detail Shows Related Decisions
    [Documentation]    Detail view shows related decisions
    [Tags]    detail    relations    will-fail
    Navigate To Rules Tab
    Click Rule By ID    RULE-001
    Wait For Elements State    [data-testid="rule-detail-related-decisions"]    visible

# =============================================================================
# CREATE TESTS - GAP-UI-002
# =============================================================================

Create Rule Form Opens
    [Documentation]    GAP-UI-002: Add Rule button opens create form
    [Tags]    create    form    gap-ui-002    will-fail
    Navigate To Rules Tab
    Click Add Rule Button
    Rule Form Should Be Visible

Create Rule Form Has Required Fields
    [Documentation]    Create form has all DSM-specified fields
    [Tags]    create    form    will-fail
    Navigate To Rules Tab
    Click Add Rule Button
    # Per ENTITY-API-UI-MAP.md: [rule_id, title, directive, category, priority]
    Wait For Elements State    ${RULE_FORM_ID}    visible
    Wait For Elements State    ${RULE_FORM_TITLE}    visible
    Wait For Elements State    ${RULE_FORM_DIRECTIVE}    visible
    Wait For Elements State    [data-testid="rule-form-category"]    visible
    Wait For Elements State    [data-testid="rule-form-priority"]    visible

Create Rule Form Validates Required Fields
    [Documentation]    Form shows validation for required fields
    [Tags]    create    validation    will-fail
    Navigate To Rules Tab
    Click Add Rule Button
    # Submit empty form
    Submit Rule Form
    # Should show validation errors
    Wait For Elements State    [data-testid="rule-form-error-title"]    visible

Create Rule Successfully Adds To List
    [Documentation]    Creating rule adds it to the list
    [Tags]    create    functional    will-fail
    Navigate To Rules Tab
    ${before_count}=    Get Rules Count
    Click Add Rule Button
    Fill Rule Form    ${TEST_RULE_ID}    ${TEST_RULE_TITLE}    ${TEST_RULE_DIR}
    Submit Rule Form
    # Back to list
    Rules List Should Be Visible
    ${after_count}=    Get Rules Count
    Should Be True    ${after_count} == ${before_count} + 1

Create Rule Cancel Does Not Add
    [Documentation]    Canceling create form doesn't add rule
    [Tags]    create    functional    will-fail
    Navigate To Rules Tab
    ${before_count}=    Get Rules Count
    Click Add Rule Button
    Fill Rule Form    ${TEST_RULE_ID}    ${TEST_RULE_TITLE}    ${TEST_RULE_DIR}
    Cancel Rule Form
    # Back to list
    Rules List Should Be Visible
    ${after_count}=    Get Rules Count
    Should Be Equal As Integers    ${after_count}    ${before_count}

# =============================================================================
# UPDATE TESTS - GAP-UI-002
# =============================================================================

Edit Rule Form Opens From Detail
    [Documentation]    Edit button opens form with pre-filled data
    [Tags]    update    form    will-fail
    Navigate To Rules Tab
    Click Rule By ID    RULE-001
    Click Edit Rule Button
    Rule Form Should Be Visible
    # Form should be pre-filled
    ${title}=    Get Text    ${RULE_FORM_TITLE}
    Should Not Be Empty    ${title}

Edit Rule Updates Successfully
    [Documentation]    Editing rule updates the data
    [Tags]    update    functional    will-fail
    Navigate To Rules Tab
    Click Rule By ID    RULE-001
    Click Edit Rule Button
    # Modify title
    Fill Text    ${RULE_FORM_TITLE}    Updated Title
    Submit Rule Form
    # Verify change
    Rule Detail Should Be Visible
    ${title}=    Get Rule Detail Title
    Should Contain    ${title}    Updated

# =============================================================================
# DELETE TESTS
# =============================================================================

Delete Rule Shows Confirmation
    [Documentation]    Delete action shows confirmation dialog
    [Tags]    delete    will-fail
    Navigate To Rules Tab
    Click Rule By ID    RULE-001
    Click    [data-testid="rule-detail-delete-btn"]
    Wait For Elements State    ${CONFIRM_DIALOG}    visible

Delete Rule Removes From List
    [Documentation]    Confirming delete removes rule from list
    [Tags]    delete    functional    will-fail
    Navigate To Rules Tab
    ${before_count}=    Get Rules Count
    Click Rule By ID    RULE-001
    Click    [data-testid="rule-detail-delete-btn"]
    Click    [data-testid="confirm-yes"]
    # Back to list
    Rules List Should Be Visible
    ${after_count}=    Get Rules Count
    Should Be True    ${after_count} == ${before_count} - 1

# =============================================================================
# FILTER & SORT TESTS - GAP-UI-010, GAP-UI-011
# =============================================================================

Filter Rules By Status Works
    [Documentation]    GAP-UI-011: Status filter reduces list
    [Tags]    filter    gap-ui-011    will-fail
    Navigate To Rules Tab
    ${before_count}=    Get Rules Count
    Filter Rules By Status    ACTIVE
    ${after_count}=    Get Rules Count
    Should Be True    ${after_count} <= ${before_count}

Filter Rules By Category Works
    [Documentation]    GAP-UI-011: Category filter reduces list
    [Tags]    filter    gap-ui-011    will-fail
    Navigate To Rules Tab
    ${before_count}=    Get Rules Count
    Click    [data-testid="rules-filter-category"]
    Click    text=governance
    ${after_count}=    Get Rules Count
    Should Be True    ${after_count} <= ${before_count}

Search Rules Works
    [Documentation]    GAP-UI-011: Search filters list by text
    [Tags]    search    gap-ui-011    will-fail
    Navigate To Rules Tab
    Search Rules    Session
    ${count}=    Get Rules Count
    Should Be True    ${count} > 0

Sort Rules By ID Works
    [Documentation]    GAP-UI-010: Sorting by ID column
    [Tags]    sort    gap-ui-010    will-fail
    Navigate To Rules Tab
    Sort Rules By Column    id
    # First rule should be RULE-001
    ${first_id}=    Get Text    table tbody tr:first-child [data-testid="rule-col-id"]
    Should Be Equal    ${first_id}    RULE-001

Sort Rules By Title Works
    [Documentation]    GAP-UI-010: Sorting by title column
    [Tags]    sort    gap-ui-010    will-fail
    Navigate To Rules Tab
    Sort Rules By Column    title
    # Should be alphabetical
    ${first_title}=    Get Text    table tbody tr:first-child [data-testid="rule-col-title"]
    Should Not Be Empty    ${first_title}

# =============================================================================
# LOADING & ERROR STATES - GAP-UI-005
# =============================================================================

Loading State Shows During Fetch
    [Documentation]    GAP-UI-005: Loading spinner during data fetch
    [Tags]    loading    ux    gap-ui-005    will-fail
    # Refresh to trigger fetch
    Reload
    Should Show Loading State
    Should Hide Loading State

Error State Shows On API Failure
    [Documentation]    GAP-UI-005: Error message when API fails
    [Tags]    error    ux    gap-ui-005    will-fail
    # This would require mocking API to fail
    [Tags]    skip
    Skip    Requires API mocking
