*** Settings ***
Documentation    RF-009: API Input Validation & Negative Tests
...              Per GAP-TEST-LENIENCY-001: Ensure API rejects invalid input
...              Per ARCH-EBMSF-01-v1: Evidence-based assertions with msg=
Library          Collections
Library          ../../libs/GovernanceCRUDE2ELibrary.py
Suite Setup       Cleanup Test Data
Suite Teardown    Cleanup Test Data
Test Tags        e2e    api    validation    negative    TEST-QUAL-01-v1

*** Test Cases ***
# =============================================================================
# Rule Validation Tests
# =============================================================================

Rule With Invalid Category Returns 422
    [Documentation]    POST rule with invalid category must return 422
    [Tags]    e2e    rules    validation    category
    ${rule}=    Create Dictionary
    ...    rule_id=TEST-INVALID-CAT
    ...    name=Invalid Category Test
    ...    category=INVALID_CATEGORY
    ...    priority=HIGH
    ...    directive=Test rule with bad category
    ${result}=    Post Rule Raw    ${rule}
    Should Be Equal As Integers    ${result}[status_code]    422
    ...    msg=Invalid category should return 422, got ${result}[status_code]

Rule With Invalid Priority Returns 422
    [Documentation]    POST rule with invalid priority must return 422
    [Tags]    e2e    rules    validation    priority
    ${rule}=    Create Dictionary
    ...    rule_id=TEST-INVALID-PRI
    ...    name=Invalid Priority Test
    ...    category=governance
    ...    priority=INVALID_PRIORITY
    ...    directive=Test rule with bad priority
    ${result}=    Post Rule Raw    ${rule}
    Should Be Equal As Integers    ${result}[status_code]    422
    ...    msg=Invalid priority should return 422, got ${result}[status_code]

Rule With Invalid Status Returns 422
    [Documentation]    POST rule with invalid status must return 422
    [Tags]    e2e    rules    validation    status
    ${rule}=    Create Dictionary
    ...    rule_id=TEST-INVALID-STAT
    ...    name=Invalid Status Test
    ...    category=governance
    ...    priority=HIGH
    ...    directive=Test rule
    ...    status=INVALID_STATUS
    ${result}=    Post Rule Raw    ${rule}
    Should Be Equal As Integers    ${result}[status_code]    422
    ...    msg=Invalid status should return 422, got ${result}[status_code]

Duplicate Rule Returns 409
    [Documentation]    POST rule with existing ID must return 409
    [Tags]    e2e    rules    validation    duplicate
    ${rule}=    Create Dictionary
    ...    rule_id=ARCH-EBMSF-01-v1
    ...    name=Duplicate Test
    ...    category=governance
    ...    priority=HIGH
    ...    directive=Should fail - already exists
    ${result}=    Post Rule Raw    ${rule}
    # ARCH-EBMSF-01-v1 already exists in TypeDB
    Should Be Equal As Integers    ${result}[status_code]    409
    ...    msg=Duplicate rule_id should return 409, got ${result}[status_code]

Rule Missing Required Fields Returns 422
    [Documentation]    POST rule missing name returns 422
    [Tags]    e2e    rules    validation    required
    ${rule}=    Create Dictionary
    ...    rule_id=TEST-MISSING
    ${result}=    Post Rule Raw    ${rule}
    Should Be Equal As Integers    ${result}[status_code]    422
    ...    msg=Missing required fields should return 422, got ${result}[status_code]

# =============================================================================
# Task Validation Tests
# =============================================================================

Task Missing Required Fields Returns 422
    [Documentation]    POST task missing description/phase returns 422
    [Tags]    e2e    tasks    validation    required
    ${task}=    Create Dictionary
    ...    task_id=TASK-INCOMPLETE
    ${result}=    Post Task Raw    ${task}
    Should Be Equal As Integers    ${result}[status_code]    422
    ...    msg=Missing required fields should return 422, got ${result}[status_code]

# =============================================================================
# Decision Validation Tests
# =============================================================================

Decision With Invalid Status Returns 422
    [Documentation]    POST decision with invalid status returns 422
    [Tags]    e2e    decisions    validation    status
    ${decision}=    Create Dictionary
    ...    decision_id=DEC-BAD-STATUS
    ...    name=Bad Status Decision
    ...    context=Test context
    ...    rationale=Test rationale
    ...    status=INVALID_STATUS
    ${result}=    Post Decision Raw    ${decision}
    Should Be Equal As Integers    ${result}[status_code]    422
    ...    msg=Invalid status should return 422, got ${result}[status_code]

# =============================================================================
# Not Found Tests (404)
# =============================================================================

Get Nonexistent Rule Returns 404
    [Documentation]    GET nonexistent rule returns 404
    [Tags]    e2e    rules    notfound
    ${result}=    Get Resource Raw    rules/RULE-DOES-NOT-EXIST-999
    Should Be Equal As Integers    ${result}[status_code]    404
    ...    msg=Nonexistent rule should return 404, got ${result}[status_code]

Get Nonexistent Task Returns 404
    [Documentation]    GET nonexistent task returns 404
    [Tags]    e2e    tasks    notfound
    ${result}=    Get Resource Raw    tasks/TASK-DOES-NOT-EXIST-999
    Should Be Equal As Integers    ${result}[status_code]    404
    ...    msg=Nonexistent task should return 404, got ${result}[status_code]

Delete Nonexistent Session Returns 404
    [Documentation]    DELETE nonexistent session returns 404
    [Tags]    e2e    sessions    notfound
    ${result}=    Delete Resource Raw    sessions/SESSION-DOES-NOT-EXIST
    Should Be Equal As Integers    ${result}[status_code]    404
    ...    msg=Nonexistent session should return 404, got ${result}[status_code]
