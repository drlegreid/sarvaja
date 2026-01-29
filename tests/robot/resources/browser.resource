*** Settings ***
Documentation    Shared Browser Keywords for E2E Tests
...              Per: RF-007 Robot Framework Migration
...              DRY: Shared navigation + SPA state handling
Library          Browser    auto_closing_level=SUITE
Resource         common.resource

*** Variables ***
${APP_TITLE}          Sarvaja Governance Dashboard
${PAGE_TIMEOUT}       10s
${ELEMENT_TIMEOUT}    10s

*** Keywords ***
Open Dashboard Browser
    [Documentation]    Open browser for test suite
    New Browser    chromium    headless=True
    New Context    viewport={'width': 1280, 'height': 720}
    New Page    ${DASHBOARD_URL}
    Wait For Elements State    text=${APP_TITLE}    visible    timeout=${PAGE_TIMEOUT}

Navigate To Dashboard Home
    [Documentation]    Navigate to dashboard and wait for app init
    Go To    ${DASHBOARD_URL}
    Reload
    Wait For Elements State    text=${APP_TITLE}    visible    timeout=20s

Click Back Button If Detail View
    [Documentation]    Click back button if in detail view (SPA state handling)
    [Arguments]    ${back_testid}=${EMPTY}
    # Try data-testid back button first (preferred)
    IF    '${back_testid}' != '${EMPTY}'
        ${testid_count}=    Get Element Count    [data-testid='${back_testid}']
        IF    ${testid_count} > 0
            Click    [data-testid='${back_testid}']
            RETURN
        END
    END
    # Fallback: generic icon back button
    ${btn_count}=    Get Element Count    button:has-text("󰁍")
    IF    ${btn_count} > 0
        Click    button:has-text("󰁍") >> nth=0
    END

Navigate To Rules List
    [Documentation]    Navigate to Rules list (handles detail-open SPA state)
    Navigate To Dashboard Home
    Click    [data-testid='nav-rules']
    ${list_count}=    Get Element Count    text=/\\d+ rules loaded/
    IF    ${list_count} == 0
        Click Back Button If Detail View    back_testid=rule-detail-back-btn
    END
    Wait For Elements State    text=/\\d+ rules loaded/    visible    timeout=20s

Navigate To Tasks List
    [Documentation]    Navigate to Tasks list (handles detail-open SPA state)
    Navigate To Dashboard Home
    Click    [data-testid='nav-tasks']
    Wait For Elements State    text=/\\d+ tasks loaded/    visible    timeout=20s

Navigate To Sessions List
    [Documentation]    Navigate to Sessions list (handles detail-open SPA state)
    Navigate To Dashboard Home
    Click    [data-testid='nav-sessions']
    ${list_count}=    Get Element Count    text=Session Evidence
    IF    ${list_count} == 0
        Click Back Button If Detail View    back_testid=session-detail-back-btn
    END
    Wait For Elements State    text=Session Evidence    visible    timeout=20s

Navigate To Trust View
    [Documentation]    Navigate to Trust view (handles detail-open SPA state)
    Navigate To Dashboard Home
    Click    [data-testid='nav-trust']
    Sleep    1s
    ${list_count}=    Get Element Count    text=Agent Trust Dashboard
    IF    ${list_count} == 0
        Click Back Button If Detail View    back_testid=agent-detail-back-btn
    END
    Wait For Elements State    text=Agent Trust Dashboard    visible    timeout=20s

Navigate To Agents List
    [Documentation]    Navigate to Agents list (handles detail-open SPA state)
    Navigate To Dashboard Home
    Click    [data-testid='nav-agents']
    Sleep    1s
    ${list_count}=    Get Element Count    text=/\\d+ agents registered/
    IF    ${list_count} == 0
        Click Back Button If Detail View    back_testid=agent-detail-back-btn
    END
    Wait For Elements State    text=/\\d+ agents registered/    visible    timeout=20s

Navigate To Decisions List
    [Documentation]    Navigate to Decisions list (handles detail-open SPA state)
    Navigate To Dashboard Home
    Click    [data-testid='nav-decisions']
    Sleep    1s
    ${list_count}=    Get Element Count    [data-testid='decision-log']
    IF    ${list_count} == 0
        Click Back Button If Detail View    back_testid=decision-detail-back-btn
    END
    Wait For Elements State    [data-testid='decision-log']    visible    timeout=20s

Navigate To Infra View
    [Documentation]    Navigate to Infrastructure view
    Navigate To Dashboard Home
    Click    [data-testid='nav-infra']
    Wait For Elements State    text=Infrastructure Health    visible    timeout=20s

Navigate To Search View
    [Documentation]    Navigate to Search view
    Navigate To Dashboard Home
    Click    [data-testid='nav-search']
    Wait For Elements State    text=Evidence Search    visible    timeout=${ELEMENT_TIMEOUT}

Navigate To Executive View
    [Documentation]    Navigate to Executive view
    Navigate To Dashboard Home
    Click    [data-testid='nav-executive']
    Wait For Elements State    text=Executive Report    visible    timeout=${ELEMENT_TIMEOUT}
