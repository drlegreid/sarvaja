*** Settings ***
Documentation    RF-004: Unit Tests - BDD Evidence Collector
...              Migrated from tests/unit/test_bdd_evidence.py
...              Per GAP-TEST-EVIDENCE-001: File-based test evidence
Library          Collections
Library          ../../libs/BDDEvidenceLibrary.py

Suite Setup      Setup BDD Evidence Environment
Suite Teardown   Cleanup BDD Evidence Environment
Force Tags             unit    evidence    GAP-TEST-EVIDENCE-001    medium    GAP-TEST-EVIDENCE-003    evidence-file    validate    TEST-EVID-01-v1

*** Keywords ***
Setup BDD Evidence Environment
    [Documentation]    Create temp directory for tests
    ${tmpdir}=    Create Temp Directory
    Set Suite Variable    ${TMPDIR}    ${tmpdir}

Cleanup BDD Evidence Environment
    [Documentation]    Clean up temp directory
    Cleanup Temp Directory

*** Test Cases ***
# =============================================================================
# BDDStep Tests
# =============================================================================

BDD Step Creation With Required Fields
    [Documentation]    BDDStep creates with required fields
    [Tags]    unit    evidence    create    bdd
    ${step}=    Create Bdd Step    given    a user exists
    Should Be Equal    ${step}[type]    given
    Should Be Equal    ${step}[description]    a user exists
    Should Be True    ${step}[passed]

BDD Step With Data
    [Documentation]    BDDStep accepts optional data dictionary
    [Tags]    unit    evidence    create    bdd
    &{data}=    Create Dictionary    email=test@example.com
    ${step}=    Create Bdd Step    when    user submits form    data=${data}
    Should Be Equal    ${step}[data][email]    test@example.com

BDD Step To Dict Serializes Correctly
    [Documentation]    BDDStep serializes to dictionary
    [Tags]    unit    evidence    serialize    bdd
    ${step}=    Create Bdd Step    then    user is logged in    duration_ms=50.0
    Should Be Equal    ${step}[type]    then
    Should Be Equal    ${step}[description]    user is logged in
    Should Be Equal As Numbers    ${step}[duration_ms]    50.0

BDD Step Failed With Error
    [Documentation]    Failed step includes error message
    [Tags]    unit    evidence    validate    bdd
    ${step}=    Create Bdd Step    then    assertion fails    passed=${FALSE}    error=Expected True but got False
    Should Not Be True    ${step}[passed]
    Should Be Equal    ${step}[error]    Expected True but got False

# =============================================================================
# EvidenceRecord Tests
# =============================================================================

Evidence Record Creation With Required Fields
    [Documentation]    EvidenceRecord creates with required fields
    [Tags]    unit    evidence    create    record
    ${evidence}=    Create Evidence Record
    ...    test_id=tests/test_example.py::test_login
    ...    name=test_login
    ...    category=unit
    ...    status=passed
    ...    duration_ms=150.0
    ...    intent=User login validates credentials
    Should Be Equal    ${evidence}[test_id]    tests/test_example.py::test_login
    Should Be Equal    ${evidence}[name]    test_login
    Should Be Equal    ${evidence}[status]    passed

Evidence Record With Rule Links
    [Documentation]    EvidenceRecord includes rule and gap links
    [Tags]    unit    evidence    create    record
    @{rules}=    Create List    RULE-001    SESSION-EVID-01-v1
    @{gaps}=    Create List    GAP-TEST-001
    ${evidence}=    Create Evidence Record
    ...    test_id=test_rule_compliance
    ...    name=test_rule_compliance
    ...    category=integration
    ...    status=passed
    ...    duration_ms=200.0
    ...    intent=RULE-001 compliance test
    ...    linked_rules=${rules}
    ...    linked_gaps=${gaps}
    List Should Contain Value    ${evidence}[linked_rules]    RULE-001
    List Should Contain Value    ${evidence}[linked_rules]    SESSION-EVID-01-v1
    List Should Contain Value    ${evidence}[linked_gaps]    GAP-TEST-001

Evidence Record To Dict Contains Timestamp
    [Documentation]    Serialized evidence has timestamp field
    [Tags]    unit    evidence    serialize    record
    ${evidence}=    Create Evidence Record
    ...    test_id=test_example
    ...    name=test_example
    ...    category=unit
    ...    status=passed
    ...    intent=Example test
    Dictionary Should Contain Key    ${evidence}    timestamp

# =============================================================================
# BDDEvidenceCollector Tests
# =============================================================================

Collector Initializes With Defaults
    [Documentation]    Collector initializes with defaults
    [Tags]    unit    evidence    create    collector
    ${created}=    Create Collector    ${TMPDIR}
    Should Be True    ${created}

Collector Accepts Session ID
    [Documentation]    Collector accepts session ID for linking
    [Tags]    unit    evidence    create    collector
    Create Collector    ${TMPDIR}    SESSION-2026-01-21-TEST
    ${session_id}=    Get Collector Session Id
    Should Be Equal    ${session_id}    SESSION-2026-01-21-TEST

Start Run Creates Directory
    [Documentation]    start_run creates run directory structure
    [Tags]    unit    evidence    create    collector
    Create Collector    ${TMPDIR}
    ${run_id}=    Start Run
    Should Not Be Empty    ${run_id}
    ${exists}=    Run Directory Exists
    Should Be True    ${exists}

Record BDD Steps
    [Documentation]    Collector records BDD Given/When/Then steps
    [Tags]    unit    evidence    create    collector
    Create Collector    ${TMPDIR}
    Start Run
    Start Test    test_login    unit    User login test
    &{data}=    Create Dictionary    email=test@example.com
    Record Given    a registered user exists    ${data}
    Record When    the user submits valid credentials
    Record Then    the user is logged in
    ${evidence}=    End Test    passed    duration_ms=100.0
    ${steps}=    Get From Dictionary    ${evidence}    bdd_steps
    ${step_count}=    Get Length    ${steps}
    Should Be Equal As Integers    ${step_count}    3

End Test Saves Evidence File
    [Documentation]    end_test writes evidence JSON file
    [Tags]    unit    evidence    create    collector
    Create Collector    ${TMPDIR}
    Start Run
    Start Test    test_example    unit    Example test
    Record Given    setup complete
    End Test    passed    duration_ms=50.0
    ${file_count}=    Get Evidence File Count    unit
    Should Be True    ${file_count} >= 1    msg=Expected at least 1 evidence file

End Run Generates Summary
    [Documentation]    end_run generates summary with statistics
    [Tags]    unit    evidence    validate    collector
    Create Collector    ${TMPDIR}    SESSION-TEST
    Start Run
    # Test 1 - passed
    Start Test    test_1    unit    Test 1
    End Test    passed    duration_ms=100.0
    # Test 2 - failed
    Start Test    test_2    unit    Test 2
    End Test    failed    duration_ms=50.0    error=Assertion failed
    # Test 3 - skipped
    Start Test    test_3    integration    Test 3
    End Test    skipped
    ${summary}=    End Run
    Should Be Equal As Integers    ${summary}[total_tests]    3
    Should Be Equal As Integers    ${summary}[passed]    1
    Should Be Equal As Integers    ${summary}[failed]    1
    Should Be Equal As Integers    ${summary}[skipped]    1
    Should Be Equal    ${summary}[session_id]    SESSION-TEST

# =============================================================================
# RuleLinker Tests
# =============================================================================

Linker Extracts Legacy Rule IDs
    [Documentation]    Linker extracts RULE-XXX IDs
    [Tags]    unit    evidence    validate    linker
    Create Rule Linker
    ${rules}    ${gaps}=    Extract References    This test validates RULE-001 and RULE-012 compliance.
    List Should Contain Value    ${rules}    RULE-001
    List Should Contain Value    ${rules}    RULE-012

Linker Extracts Semantic Rule IDs
    [Documentation]    Linker extracts semantic rule IDs
    [Tags]    unit    evidence    validate    linker
    Create Rule Linker
    ${rules}    ${gaps}=    Extract References    Per SESSION-EVID-01-v1: Evidence collection test.
    List Should Contain Value    ${rules}    SESSION-EVID-01-v1

Linker Extracts Gap IDs
    [Documentation]    Linker extracts GAP-XXX IDs
    [Tags]    unit    evidence    validate    linker
    Create Rule Linker
    ${rules}    ${gaps}=    Extract References    Addresses GAP-MCP-001 and GAP-UI-AUDIT-001.
    List Should Contain Value    ${gaps}    GAP-MCP-001
    List Should Contain Value    ${gaps}    GAP-UI-AUDIT-001

Register Test Combines Sources
    [Documentation]    register_test combines docstring and explicit markers
    [Tags]    unit    evidence    validate    linker
    Create Rule Linker
    @{explicit_rules}=    Create List    RULE-002
    @{explicit_gaps}=    Create List    GAP-001
    ${rules}    ${gaps}=    Register Test
    ...    test_combined
    ...    docstring=Tests RULE-001 compliance.
    ...    rules=${explicit_rules}
    ...    gaps=${explicit_gaps}
    List Should Contain Value    ${rules}    RULE-001
    List Should Contain Value    ${rules}    RULE-002
    List Should Contain Value    ${gaps}    GAP-001

Get Tests For Rule Returns Matching Tests
    [Documentation]    get_tests_for_rule returns tests validating a rule
    [Tags]    unit    evidence    validate    linker
    Create Rule Linker
    @{rules_a}=    Create List    RULE-001    RULE-002
    @{rules_b}=    Create List    RULE-001
    @{rules_c}=    Create List    RULE-003
    Register Test    test_a    rules=${rules_a}
    Register Test    test_b    rules=${rules_b}
    Register Test    test_c    rules=${rules_c}
    ${tests}=    Get Tests For Rule    RULE-001
    List Should Contain Value    ${tests}    test_a
    List Should Contain Value    ${tests}    test_b
    List Should Not Contain Value    ${tests}    test_c

Coverage Summary Returns Statistics
    [Documentation]    get_coverage_summary returns statistics
    [Tags]    unit    evidence    validate    linker
    Create Rule Linker
    @{rules}=    Create List    RULE-001
    @{gaps}=    Create List    GAP-001
    Register Test    test_a    rules=${rules}
    Register Test    test_b    gaps=${gaps}
    Register Test    test_c
    ${summary}=    Get Coverage Summary
    Should Be Equal As Integers    ${summary}[total_tests]    3
    Should Be Equal As Integers    ${summary}[linked_tests]    2
    Should Be Equal As Integers    ${summary}[unique_rules]    1
    Should Be Equal As Integers    ${summary}[unique_gaps]    1

