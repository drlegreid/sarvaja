*** Settings ***
Documentation    TypeDB-Document Sync Verification E2E Tests
...              Verifies EPIC-RULES-V3-P8: GET /api/rules/sync/verify
...              compares TypeDB rules, leaf markdown, and RULES-*.md indexes.
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
# SYNC VERIFICATION — EPIC-RULES-V3-P8
# =============================================================================

Sync Verify Returns 200
    [Documentation]    GET /api/rules/sync/verify must return 200.
    [Tags]    sync    critical    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/sync/verify
    Should Be Equal As Integers    ${response.status_code}    200

Sync Report Has Required Fields
    [Documentation]    Response must contain all SyncReport fields.
    [Tags]    sync    critical    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/sync/verify
    ${json}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${json}    typedb_only
    Dictionary Should Contain Key    ${json}    leaf_only
    Dictionary Should Contain Key    ${json}    index_gaps
    Dictionary Should Contain Key    ${json}    all_synced_count
    Dictionary Should Contain Key    ${json}    typedb_count
    Dictionary Should Contain Key    ${json}    leaf_count
    Dictionary Should Contain Key    ${json}    index_count
    Dictionary Should Contain Key    ${json}    synced

Sync Report Has Positive Counts
    [Documentation]    TypeDB and leaf counts must be positive (rules exist).
    [Tags]    sync    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/sync/verify
    ${json}=    Set Variable    ${response.json()}
    ${typedb_count}=    Get From Dictionary    ${json}    typedb_count
    ${leaf_count}=    Get From Dictionary    ${json}    leaf_count
    Should Be True    ${typedb_count} > 0    msg=TypeDB should have rules
    Should Be True    ${leaf_count} > 0    msg=Leaf directory should have rule files

Sync Report Discrepancy Lists Are Arrays
    [Documentation]    typedb_only, leaf_only, index_gaps must be lists.
    [Tags]    sync    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/sync/verify
    ${json}=    Set Variable    ${response.json()}
    ${typedb_only}=    Get From Dictionary    ${json}    typedb_only
    ${leaf_only}=    Get From Dictionary    ${json}    leaf_only
    ${index_gaps}=    Get From Dictionary    ${json}    index_gaps
    Should Be True    type($typedb_only) == list
    Should Be True    type($leaf_only) == list
    Should Be True    type($index_gaps) == list
