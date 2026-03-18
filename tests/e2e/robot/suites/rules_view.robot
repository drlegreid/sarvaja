*** Settings ***
Documentation    Rules View E2E Tests
...              Per TEST-E2E-FRAMEWORK-01-v1: Robot Framework migration
...              Migrated from: tests/e2e/test_dashboard_e2e.py::TestRulesView

Resource    ../resources/common.resource

Suite Setup       Suite Setup Open Dashboard
Suite Teardown    Suite Teardown Close Browser
Test Setup        Setup Rules View

Default Tags    e2e    browser    rules

*** Keywords ***
Setup Rules View
    [Documentation]    Navigate to Rules view before each test.
    Test Setup Navigate Home
    Navigate And Verify Tab    rules    Governance Rules

*** Test Cases ***
Rules Data Table Is Rendered
    [Documentation]    Rules data table is visible.
    Wait For Elements State    ${RULES_TABLE}    visible    timeout=10s

Rules Table Has Data Rows
    [Documentation]    Rules table has at least one data row.
    Verify Data Table Has Rows

Add Rule Button Is Present
    [Documentation]    Add Rule button is visible.
    Wait For Elements State    ${RULES_ADD_BTN}    visible    timeout=10s

Search Input Is Available
    [Documentation]    Rules search input is visible.
    Wait For Elements State    ${RULES_SEARCH}    visible    timeout=10s

Clicking Rule Row Shows Detail
    [Documentation]    Clicking a rule row shows the detail view.
    Verify Data Table Has Rows
    Click Table Row    0
    # Detail should show Edit/Directive/Delete content
    ${edit_visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    text=Edit    visible    timeout=5s
    ${directive_visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    text=Directive    visible    timeout=2s
    Should Be True    ${edit_visible} or ${directive_visible}
    ...    Rule detail should show after clicking a row
