*** Settings ***
Documentation    Infrastructure Health Dashboard E2E Tests
...              Per TEST-E2E-FRAMEWORK-01-v1: Robot Framework migration
...              Migrated from: tests/e2e/test_dashboard_e2e.py::TestInfraView

Resource    ../resources/common.resource

Suite Setup       Suite Setup Open Dashboard
Suite Teardown    Suite Teardown Close Browser
Test Setup        Setup Infra View

Default Tags    e2e    browser    infra

*** Keywords ***
Setup Infra View
    [Documentation]    Navigate to Infrastructure view before each test.
    Test Setup Navigate Home
    Navigate And Verify Tab    infra    Infrastructure Health

*** Test Cases ***
Infrastructure Dashboard Loads
    [Documentation]    Infrastructure dashboard loads with header.
    Wait For Elements State    text=Infrastructure Health    visible    timeout=10s

Service Status Cards Are Displayed
    [Documentation]    TypeDB and ChromaDB service cards are visible.
    Wait For Elements State    ${INFRA_CARD_TYPEDB}    visible    timeout=10s
    Wait For Elements State    ${INFRA_CARD_CHROMADB}    visible    timeout=10s

System Stats Are Displayed
    [Documentation]    Memory and hash stats are visible.
    Wait For Elements State    ${INFRA_STAT_MEMORY}    visible    timeout=10s
    Wait For Elements State    ${INFRA_STAT_HASH}    visible    timeout=10s

Refresh Button Is Clickable
    [Documentation]    Refresh button is visible and can be clicked.
    Wait For Elements State    ${INFRA_REFRESH_BTN}    visible    timeout=10s
    Click    ${INFRA_REFRESH_BTN}

Recovery Action Buttons Are Present
    [Documentation]    Start All, Restart, and Cleanup buttons are visible.
    Wait For Elements State    ${INFRA_START_ALL}    visible    timeout=10s
    Wait For Elements State    ${INFRA_RESTART}    visible    timeout=10s
    Wait For Elements State    ${INFRA_CLEANUP}    visible    timeout=10s
