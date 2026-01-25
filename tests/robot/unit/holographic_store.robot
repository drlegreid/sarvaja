*** Settings ***
Documentation    RF-004: Unit Tests - Holographic Test Store
...              Migrated from tests/unit/test_holographic_store.py
...              Per EPIC-TEST-COMPRESS-001 + FH-001: Multi-resolution evidence
Library          Collections
Library          ../../libs/HolographicStoreLibrary.py

*** Test Cases ***
# =============================================================================
# EvidenceRecord Tests
# =============================================================================

Evidence Record Creates Hash
    [Documentation]    GIVEN EvidenceRecord WHEN creating THEN hash auto-generated
    [Tags]    unit    evidence    create    holographic
    ${result}=    Evidence Record Creates Hash
    Should Be True    ${result}[has_hash]
    Should Be Equal As Integers    ${result}[hash_length]    16

Evidence Record To Summary Dict
    [Documentation]    GIVEN EvidenceRecord WHEN to_summary_dict THEN level 1-2 fields
    [Tags]    unit    evidence    validate    holographic
    ${result}=    Evidence Record To Summary Dict
    Should Be True    ${result}[has_test_id]
    Should Be True    ${result}[has_status]
    Should Be True    ${result}[no_fixtures]

Evidence Record To Full Dict
    [Documentation]    GIVEN EvidenceRecord WHEN to_full_dict THEN all fields
    [Tags]    unit    evidence    validate    holographic
    ${result}=    Evidence Record To Full Dict
    Should Be True    ${result}[has_fixtures]
    Should Be Equal    ${result}[fixtures_input]    data

# =============================================================================
# HolographicTestStore Tests
# =============================================================================

Push Event Basic
    [Documentation]    GIVEN store WHEN push_event THEN returns hash
    [Tags]    unit    evidence    create    holographic
    ${result}=    Push Event Basic
    Should Be True    ${result}[has_hash]
    Should Be Equal As Integers    ${result}[count]    1

Push Event With Fixtures
    [Documentation]    GIVEN store WHEN push with fixtures THEN stored at level 3
    [Tags]    unit    evidence    create    holographic
    ${result}=    Push Event With Fixtures
    Should Be Equal    ${result}[method]    GET
    Should Be Equal As Integers    ${result}[user_id]    1

Query Zoom 0 Oneline
    [Documentation]    GIVEN events WHEN zoom 0 THEN one-line summary
    [Tags]    unit    evidence    query    holographic
    ${result}=    Query Zoom 0 Oneline
    Should Be Equal As Integers    ${result}[zoom]    0
    Should Be Equal As Integers    ${result}[total]    3
    Should Be Equal As Integers    ${result}[passed]    2
    Should Be Equal As Integers    ${result}[failed]    1
    Should Be True    ${result}[has_summary]

Query Zoom 1 Compact
    [Documentation]    GIVEN events WHEN zoom 1 THEN compact with failures
    [Tags]    unit    evidence    query    holographic
    ${result}=    Query Zoom 1 Compact
    Should Be Equal As Integers    ${result}[zoom]    1
    Should Be True    ${result}[has_stats]
    Should Be Equal As Integers    ${result}[failed]    1
    Should Be Equal As Integers    ${result}[failure_count]    1
    Should Be True    ${result}[has_assertion_error]

Query Zoom 2 List
    [Documentation]    GIVEN events WHEN zoom 2 THEN per-test list
    [Tags]    unit    evidence    query    holographic
    ${result}=    Query Zoom 2 List
    Should Be Equal As Integers    ${result}[zoom]    2
    Should Be Equal As Integers    ${result}[count]    2
    Should Be Equal As Integers    ${result}[test_count]    2
    Should Be Equal    ${result}[first_name]    test_one

Query Zoom 3 Full Single
    [Documentation]    GIVEN event WHEN zoom 3 with test_id THEN full detail
    [Tags]    unit    evidence    query    holographic
    ${result}=    Query Zoom 3 Full Single
    Should Be Equal As Integers    ${result}[zoom]    3
    Should Be True    ${result}[has_evidence]
    Should Be Equal    ${result}[fixtures_user]    admin

Query Filter By Category
    [Documentation]    GIVEN events WHEN filter by category THEN filtered
    [Tags]    unit    evidence    query    holographic
    ${result}=    Query Filter By Category
    Should Be Equal As Integers    ${result}[total]    2

Query Filter By Status
    [Documentation]    GIVEN events WHEN filter by status THEN filtered
    [Tags]    unit    evidence    query    holographic
    ${result}=    Query Filter By Status
    Should Be Equal As Integers    ${result}[total]    1
    Should Be Equal As Integers    ${result}[failed]    1

Get By Hash
    [Documentation]    GIVEN events WHEN get_by_hash THEN retrieves specific
    [Tags]    unit    evidence    query    holographic
    ${result}=    Get By Hash
    Should Be True    ${result}[found]
    Should Be Equal    ${result}[test_id]    t2
    Should Be Equal    ${result}[status]    failed

Get By Hash Not Found
    [Documentation]    GIVEN invalid hash WHEN get_by_hash THEN returns None
    [Tags]    unit    evidence    query    holographic
    ${result}=    Get By Hash Not Found
    Should Be True    ${result}[is_none]

Clear Store
    [Documentation]    GIVEN events WHEN clear THEN all removed
    [Tags]    unit    evidence    delete    holographic
    ${result}=    Clear
    Should Be Equal As Integers    ${result}[cleared_count]    2
    Should Be Equal As Integers    ${result}[store_count]    0

Persist And Load
    [Documentation]    GIVEN events WHEN persist THEN can load
    [Tags]    unit    evidence    persist    holographic
    ${result}=    Persist And Load
    Should Be Equal As Integers    ${result}[loaded_count]    2
    Should Be Equal As Integers    ${result}[store_count]    2

Thread Safety
    [Documentation]    GIVEN concurrent pushes WHEN running THEN no errors
    [Tags]    unit    evidence    validate    holographic    threadsafe
    ${result}=    Thread Safety
    Should Be True    ${result}[no_errors]
    Should Be Equal As Integers    ${result}[count]    500

# =============================================================================
# Global Store Tests
# =============================================================================

Global Store Singleton
    [Documentation]    GIVEN get_global_store WHEN called twice THEN same instance
    [Tags]    unit    evidence    validate    holographic
    ${result}=    Global Store Singleton
    Should Be True    ${result}[is_same]

Reset Global Store
    [Documentation]    GIVEN store with data WHEN reset THEN cleared
    [Tags]    unit    evidence    delete    holographic
    ${result}=    Reset Global Store
    Should Be Equal As Integers    ${result}[count_after_reset]    0

