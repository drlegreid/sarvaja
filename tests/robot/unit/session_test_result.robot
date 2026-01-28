*** Settings ***
Documentation    RF-004: Unit Tests - Session Test Result Capture
...              Migrated from tests/unit/test_session_test_result.py
...              Per GAP-TEST-EVIDENCE-002: Event-based test reporting
Library          Collections
Library          String
Library          ../../libs/SessionTestResultLibrary.py

Suite Setup      Setup Session Test Library
Force Tags             unit    sessions    GAP-TEST-EVIDENCE-002    medium    session    validate    TEST-EVID-01-v1

*** Variables ***
${SESSION_ID}    SESSION-2026-01-21-TEST

*** Keywords ***
Setup Session Test Library
    [Documentation]    Check session availability and create mock collector
    ${available}=    Check Session Available
    IF    not ${available}
        Skip    SessionCollector not available
    END
    Create Mock Collector    ${SESSION_ID}

*** Test Cases ***
# =============================================================================
# Basic Capture Tests
# =============================================================================

Capture Test Result Creates Event
    [Documentation]    GIVEN mock collector WHEN capture_test_result THEN event created
    [Tags]    unit    sessions    create    capture
    Capture Test Result
    ...    test_id=tests/unit/test_auth.py::test_login
    ...    name=test_login
    ...    category=unit
    ...    status=passed
    ...    duration_ms=150.0
    ...    intent=User login with valid credentials
    ${count}=    Get Event Count
    Should Be Equal As Integers    ${count}    1
    ${event}=    Get Last Event
    Should Be Equal    ${event}[event_type]    test_result
    ${content_ok}=    Event Content Contains    PASSED: test_login
    Should Be True    ${content_ok}

Capture Test Result Has Metadata
    [Documentation]    GIVEN captured test WHEN checking metadata THEN all fields present
    [Tags]    unit    sessions    validate    metadata
    Create Mock Collector    ${SESSION_ID}
    Capture Test Result
    ...    test_id=tests/unit/test_auth.py::test_login
    ...    name=test_login
    ...    category=unit
    ...    status=passed
    ...    duration_ms=150.0
    ${event}=    Get Last Event
    Should Be Equal    ${event}[metadata][test_id]    tests/unit/test_auth.py::test_login
    Should Be Equal    ${event}[metadata][status]    passed
    Should Be Equal    ${event}[metadata][category]    unit
    Should Be Equal As Numbers    ${event}[metadata][duration_ms]    150.0

# =============================================================================
# Linked Rules and Gaps Tests
# =============================================================================

Capture Test Result With Rules
    [Documentation]    GIVEN capture with rules WHEN captured THEN rules in metadata
    [Tags]    unit    sessions    rules    validate
    Create Mock Collector    ${SESSION_ID}
    @{rules}=    Create List    RULE-001    SESSION-EVID-01-v1
    @{gaps}=    Create List    GAP-TEST-001
    Capture Test Result
    ...    test_id=test_rule_compliance
    ...    name=test_rule_compliance
    ...    category=integration
    ...    status=passed
    ...    duration_ms=200.0
    ...    linked_rules=${rules}
    ...    linked_gaps=${gaps}
    ${event}=    Get Last Event
    List Should Contain Value    ${event}[metadata][linked_rules]    RULE-001
    List Should Contain Value    ${event}[metadata][linked_rules]    SESSION-EVID-01-v1
    List Should Contain Value    ${event}[metadata][linked_gaps]    GAP-TEST-001

# =============================================================================
# Failed Test Capture Tests
# =============================================================================

Capture Test Result Failed
    [Documentation]    GIVEN failed test WHEN captured THEN error message in metadata
    [Tags]    unit    sessions    validate    failed
    Create Mock Collector    ${SESSION_ID}
    Capture Test Result
    ...    test_id=test_failing
    ...    name=test_failing
    ...    category=unit
    ...    status=failed
    ...    duration_ms=50.0
    ...    error_message=AssertionError: Expected True but got False
    ${event}=    Get Last Event
    Should Be Equal    ${event}[metadata][status]    failed
    Should Contain    ${event}[metadata][error_message]    AssertionError
    ${content_ok}=    Event Content Contains    FAILED: test_failing
    Should Be True    ${content_ok}

# =============================================================================
# Skipped Test Capture Tests
# =============================================================================

Capture Test Result Skipped
    [Documentation]    GIVEN skipped test WHEN captured THEN status is skipped
    [Tags]    unit    sessions    validate    skipped
    Create Mock Collector    ${SESSION_ID}
    Capture Test Result
    ...    test_id=test_skipped
    ...    name=test_skipped
    ...    category=e2e
    ...    status=skipped
    ...    duration_ms=0.0
    ...    intent=Skipped due to missing fixture
    ${event}=    Get Last Event
    Should Be Equal    ${event}[metadata][status]    skipped
    Should Be Equal    ${event}[metadata][category]    e2e
    ${content_ok}=    Event Content Contains    SKIPPED: test_skipped
    Should Be True    ${content_ok}

# =============================================================================
# Integration Tests
# =============================================================================

Full Collector Multiple Results
    [Documentation]    GIVEN full collector WHEN multiple results THEN all captured
    [Tags]    unit    sessions    integration    create
    ${ok}=    Create Full Collector    TEST-EVIDENCE
    IF    not ${ok}
        Skip    Full collector not available
    END
    Capture Test Result
    ...    test_id=test_1
    ...    name=test_1
    ...    category=unit
    ...    status=passed
    ...    duration_ms=100.0
    ...    intent=First test
    Capture Test Result
    ...    test_id=test_2
    ...    name=test_2
    ...    category=unit
    ...    status=failed
    ...    duration_ms=50.0
    ...    error_message=Test failed
    ${count}=    Get Event Count
    Should Be True    ${count} >= 2
    ${event0}=    Get Event At    0
    ${event1}=    Get Event At    1
    Should Be Equal    ${event0}[metadata][status]    passed
    Should Be Equal    ${event1}[metadata][status]    failed

