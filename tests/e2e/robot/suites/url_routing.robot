*** Settings ***
Documentation    URL Routing E2E Tests (FEAT-008)
...              Verifies hash-based URI routing for dashboard navigation.
...              Per TEST-E2E-01-v1: Tier 3 browser verification.

Resource    ../resources/common.resource

Suite Setup       Suite Setup Open Dashboard
Suite Teardown    Suite Teardown Close Browser
Test Setup        Test Setup Navigate Home

Default Tags    e2e    browser    routing    FEAT-008

*** Test Cases ***
Route Sync JS Is Loaded
    [Documentation]    The route_sync.js script should be injected and sarvaja_push_hash available.
    ${result}=    Evaluate JavaScript    ${None}    typeof window.sarvaja_push_hash
    Should Be Equal    ${result}    function

Navigate To Tasks Updates URL Hash
    [Documentation]    Clicking Tasks tab should update browser hash to include /tasks.
    Navigate To Tab    tasks
    Sleep    1s
    ${hash}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${hash}    tasks

Navigate To Sessions Updates URL Hash
    [Documentation]    Clicking Sessions tab should update browser hash.
    Navigate To Tab    sessions
    Sleep    1s
    ${hash}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${hash}    sessions

Navigate To Rules Updates URL Hash
    [Documentation]    Clicking Rules tab should update browser hash.
    Navigate To Tab    rules
    Sleep    1s
    ${hash}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${hash}    rules

Standalone View Executive Has Simple Hash
    [Documentation]    Executive view should produce #/executive hash.
    Navigate To Tab    executive
    Sleep    1s
    ${hash}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Be Equal    ${hash}    #/executive

Standalone View Monitor Has Simple Hash
    [Documentation]    Monitor view should produce #/monitor hash.
    Navigate To Tab    monitor
    Sleep    1s
    ${hash}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Be Equal    ${hash}    #/monitor

Direct Hash Navigation To Tasks
    [Documentation]    Setting hash directly should navigate to tasks view.
    Evaluate JavaScript    ${None}    window.location.hash = '#/projects/WS-9147535A/tasks'
    Sleep    2s
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=10s

Direct Hash Navigation To Sessions
    [Documentation]    Setting hash directly should navigate to sessions view.
    Evaluate JavaScript    ${None}    window.location.hash = '#/projects/WS-9147535A/sessions'
    Sleep    2s
    Wait For Elements State    [data-testid='sessions-table']    visible    timeout=10s

Direct Hash Navigation To Executive
    [Documentation]    Standalone view via hash.
    Evaluate JavaScript    ${None}    window.location.hash = '#/executive'
    Sleep    2s
    Element Should Be Visible With Backoff    text=Executive

Hash Changes On Tab Switch Sequence
    [Documentation]    Rapid tab switching updates hash each time.
    Navigate To Tab    tasks
    Sleep    1s
    ${h1}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${h1}    tasks
    Navigate To Tab    sessions
    Sleep    1s
    ${h2}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${h2}    sessions
    Navigate To Tab    rules
    Sleep    1s
    ${h3}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${h3}    rules
