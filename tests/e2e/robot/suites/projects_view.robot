*** Settings ***
Documentation    Projects View E2E Tests
...              Per TEST-E2E-FRAMEWORK-01-v1: Robot Framework migration
...              Projects view for CC session project grouping

Resource    ../resources/common.resource

Suite Setup       Suite Setup Open Dashboard
Suite Teardown    Suite Teardown Close Browser
Test Setup        Setup Projects View

Default Tags    e2e    browser    projects

*** Keywords ***
Setup Projects View
    [Documentation]    Navigate to Projects view before each test.
    Test Setup Navigate Home
    Navigate To Tab    projects
    Wait For Elements State    ${PROJECTS_LIST}    visible    timeout=10s

*** Test Cases ***
Projects View Loads
    [Documentation]    Projects view renders with the projects list.
    Wait For Elements State    ${PROJECTS_LIST}    visible    timeout=10s

New Project Button Is Present
    [Documentation]    New Project button is visible.
    Wait For Elements State    ${PROJECTS_ADD_BTN}    visible    timeout=10s

Projects Table Has Header Columns
    [Documentation]    Projects table shows expected column headers.
    Wait For Elements State    ${PROJECTS_TABLE} >> text=Project ID    visible    timeout=10s
    Wait For Elements State    ${PROJECTS_TABLE} >> text=Name    visible    timeout=10s
    Wait For Elements State    ${PROJECTS_TABLE} >> text=Path    visible    timeout=10s

Stats Cards Are Displayed
    [Documentation]    Project stats cards show Projects, Plans, and Sessions counts.
    # Use nth=0 to target stat cards, avoiding duplicates in table headers
    Wait For Elements State    main >> text=Plans >> nth=0    visible    timeout=10s
    Wait For Elements State    main >> text=Sessions >> nth=0    visible    timeout=10s
