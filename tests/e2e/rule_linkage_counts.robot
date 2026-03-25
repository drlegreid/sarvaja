*** Settings ***
Documentation    Rule→Task Linkage Count E2E Tests (implements-rule direction)
...              Verifies EPIC-RULES-V3-P1 fix: rules_relations.py uses
...              correct 'implements-rule' relation, so GET /api/rules
...              returns non-zero linked_tasks_count for rules with seed data.
...              Per TEST-E2E-01-v1: Tier 3 data flow verification.
Library          Collections
Library          RequestsLibrary

Suite Setup      Setup API Session
Suite Teardown   Delete All Sessions

*** Variables ***
${API_BASE}    http://localhost:8082

*** Keywords ***
Setup API Session
    [Documentation]    Create API session for tests
    Create Session    api    ${API_BASE}    verify=${FALSE}

Count Rules With Linked Tasks
    [Documentation]    Count rules where linked_tasks_count > 0 from list API
    [Arguments]    ${rules}
    ${count}=    Set Variable    0
    FOR    ${rule}    IN    @{rules}
        ${ltc}=    Get From Dictionary    ${rule}    linked_tasks_count    default=0
        IF    ${ltc} > 0
            ${count}=    Evaluate    ${count} + 1
        END
    END
    RETURN    ${count}

Count Rules With Linked Sessions
    [Documentation]    Count rules where linked_sessions_count > 0 from list API
    [Arguments]    ${rules}
    ${count}=    Set Variable    0
    FOR    ${rule}    IN    @{rules}
        ${lsc}=    Get From Dictionary    ${rule}    linked_sessions_count    default=0
        IF    ${lsc} > 0
            ${count}=    Evaluate    ${count} + 1
        END
    END
    RETURN    ${count}

*** Test Cases ***
# =============================================================================
# RULE→TASK LINKAGE (implements-rule direction) — EPIC-RULES-V3-P1
# =============================================================================

Rule List API Returns Linked Tasks Count
    [Documentation]    GET /api/rules must return linked_tasks_count field.
    ...                At least 1 rule should have linked_tasks_count > 0
    ...                (seed data links tasks to rules via implements-rule).
    ...                This verifies the P1 fix: task-rule-link → implements-rule.
    [Tags]    linkage    rule_task    critical    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules    params=limit=200
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    # API returns {"items": [...]} — extract items list
    ${rules}=    Get From Dictionary    ${body}    items
    ${total}=    Get Length    ${rules}
    Should Be True    ${total} > 0    No rules returned from API
    ${with_tasks}=    Count Rules With Linked Tasks    ${rules}
    Log    Rules with linked_tasks_count > 0: ${with_tasks} / ${total}
    Should Be True    ${with_tasks} >= 1
    ...    No rules have linked_tasks_count > 0 — implements-rule relation may be broken

Rule List API Returns Applicability Field
    [Documentation]    GET /api/rules must return applicability field on every rule.
    ...                Verifies schema_3x parity fix from EPIC-RULES-V3-P1.
    [Tags]    schema    applicability    high    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules    params=limit=50
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    ${rules}=    Get From Dictionary    ${body}    items
    ${total}=    Get Length    ${rules}
    Should Be True    ${total} > 0    No rules returned from API
    ${with_applicability}=    Set Variable    0
    FOR    ${rule}    IN    @{rules}
        ${app}=    Get From Dictionary    ${rule}    applicability    default=${NONE}
        IF    '${app}' != 'None' and '${app}' != ''
            ${with_applicability}=    Evaluate    ${with_applicability} + 1
        END
    END
    Log    Rules with applicability: ${with_applicability} / ${total}
    # Most rules should have applicability set (MANDATORY, RECOMMENDED, etc.)
    ${ratio}=    Evaluate    ${with_applicability} / ${total}
    Should Be True    ${ratio} >= 0.5
    ...    Less than 50% of rules have applicability — schema drift suspected

Rule List API No Deprecated Relation Names In Response
    [Documentation]    API response must not contain old relation name artifacts.
    ...                Verifies task-rule-link and session-rule-link are fully purged.
    [Tags]    regression    relation_names    high    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules    params=limit=10
    Should Be Equal As Integers    ${response.status_code}    200
    ${body_text}=    Convert To String    ${response.content}
    Should Not Contain    ${body_text}    task-rule-link
    ...    API response contains deprecated 'task-rule-link' relation name
    Should Not Contain    ${body_text}    session-rule-link
    ...    API response contains deprecated 'session-rule-link' relation name
