*** Settings ***
Documentation    Semantic-Only Rule CRUD E2E Tests
...              Verifies EPIC-RULES-V3-P7: Semantic-only rules (no legacy mapping)
...              resolve correctly via REST API without legacy fallback.
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

*** Test Cases ***
# =============================================================================
# SEMANTIC-ONLY RULE GET — EPIC-RULES-V3-P7
# =============================================================================

GET Semantic-Only Rule By ID Returns 200
    [Documentation]    GET /api/rules/CONTAINER-TYPEDB-01-v1 must return 200.
    ...                This is a semantic-only ID (no RULE-XXX legacy mapping).
    [Tags]    semantic_only    crud    critical    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/CONTAINER-TYPEDB-01-v1
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    Should Be Equal As Strings    ${body}[id]    CONTAINER-TYPEDB-01-v1
    Should Be Equal As Strings    ${body}[status]    ACTIVE
    Should Be Equal As Strings    ${body}[category]    devops

GET Another Semantic-Only Rule Returns 200
    [Documentation]    GET /api/rules/PKG-LATEST-01-v1 must return 200.
    ...                Verifies a second semantic-only rule resolves correctly.
    [Tags]    semantic_only    crud    high    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/PKG-LATEST-01-v1
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    Should Be Equal As Strings    ${body}[id]    PKG-LATEST-01-v1

Rule List Includes Semantic-Only Rules
    [Documentation]    GET /api/rules (full list) must include semantic-only rules.
    ...                Verifies no regression from extracting SEMANTIC_ONLY_RULES.
    [Tags]    semantic_only    list    high    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules    params=limit=200
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    ${rules}=    Get From Dictionary    ${body}    items
    ${ids}=    Evaluate    [r["id"] for r in $rules]
    List Should Contain Value    ${ids}    CONTAINER-TYPEDB-01-v1
    List Should Contain Value    ${ids}    PKG-LATEST-01-v1
    List Should Contain Value    ${ids}    GAP-DOC-01-v1

Legacy-Mapped Rule Still Resolves
    [Documentation]    GET /api/rules/SESSION-EVID-01-v1 must still work.
    ...                Verifies extraction of semantic-only didn't break legacy mapping.
    [Tags]    semantic_only    regression    critical    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/SESSION-EVID-01-v1
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    # Should resolve — either direct or via legacy fallback
    Should Not Be Empty    ${body}[name]
