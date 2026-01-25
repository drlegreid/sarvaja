*** Settings ***
Documentation    RF-004: Unit Tests - Certification Report Generator
...              Migrated from tests/unit/test_certification_report.py
...              Per RD-TESTING-STRATEGY TEST-005: GitHub milestone certification
Library          Collections
Library          ../../libs/CertificationReportLibrary.py

*** Test Cases ***
# =============================================================================
# TestResult Tests
# =============================================================================

Test Result Creation
    [Documentation]    GIVEN TestResult WHEN creating THEN fields are set correctly
    [Tags]    unit    evidence    create    certification
    ${result}=    Create Test Result
    Should Be Equal    ${result}[category]    unit
    Should Be Equal    ${result}[status]    passed
    Should Be True    ${result}[has_rule]

Test Result Defaults
    [Documentation]    GIVEN TestResult WHEN using defaults THEN empty lists and None
    [Tags]    unit    evidence    validate    certification
    ${result}=    Test Result Defaults
    ${rules_len}=    Get Length    ${result}[linked_rules]
    ${gaps_len}=    Get Length    ${result}[linked_gaps]
    Should Be Equal As Integers    ${rules_len}    0
    Should Be Equal As Integers    ${gaps_len}    0
    Should Be Equal    ${result}[error_message]    ${None}

# =============================================================================
# CertificationReport Tests
# =============================================================================

Certification Report Creation
    [Documentation]    GIVEN CertificationReport WHEN creating THEN fields are set
    [Tags]    unit    evidence    create    certification
    ${result}=    Create Certification Report
    Should Be Equal    ${result}[report_id]    CERT-2026-01-21
    Should Be Equal    ${result}[milestone]    v1.0
    Should Be Equal As Integers    ${result}[passed]    95

Report To Dict
    [Documentation]    GIVEN CertificationReport WHEN converting to dict THEN structure correct
    [Tags]    unit    evidence    validate    certification
    ${result}=    Report To Dict
    Should Be Equal    ${result}[report_id]    CERT-TEST
    Should Be Equal As Integers    ${result}[passed]    8
    List Should Contain Value    ${result}[rules_covered]    RULE-001
    List Should Contain Value    ${result}[rules_covered]    RULE-002

Report Defaults
    [Documentation]    GIVEN CertificationReport WHEN using defaults THEN defaults correct
    [Tags]    unit    evidence    validate    certification
    ${result}=    Report Defaults
    Should Be Equal As Integers    ${result}[total_tests]    0
    Should Be Equal    ${result}[success_rate]    0%
    ${len}=    Get Length    ${result}[rules_covered]
    Should Be Equal As Integers    ${len}    0

# =============================================================================
# CertificationReportGenerator Tests
# =============================================================================

Generator Initialization
    [Documentation]    GIVEN generator WHEN initializing THEN milestone and commit_sha set
    [Tags]    unit    evidence    create    certification
    ${result}=    Generator Initialization
    Should Be Equal    ${result}[milestone]    v1.0
    Should Be Equal    ${result}[commit_sha]    abc123

Format Duration
    [Documentation]    GIVEN various durations WHEN formatting THEN correct strings
    [Tags]    unit    evidence    validate    certification
    ${result}=    Format Duration
    Should Be Equal    ${result}[500ms]    0.5s
    Should Be Equal    ${result}[5000ms]    5.0s
    Should Contain    ${result}[90000ms]    m

Generate Empty Report
    [Documentation]    GIVEN no evidence WHEN generating THEN empty report
    [Tags]    unit    evidence    validate    certification
    ${result}=    Generate Empty Report
    Should Be Equal As Integers    ${result}[total_tests]    0
    Should Be Equal    ${result}[success_rate]    0%

Generate Report From Evidence
    [Documentation]    GIVEN evidence files WHEN generating THEN report has correct stats
    [Tags]    unit    evidence    validate    certification
    ${result}=    Generate Report From Evidence
    Should Be Equal As Integers    ${result}[total_tests]    2
    Should Be Equal As Integers    ${result}[passed]    1
    Should Be Equal As Integers    ${result}[failed]    1
    Should Be Equal As Integers    ${result}[unit_tests]    1
    Should Be Equal As Integers    ${result}[integration_tests]    1
    Should Be True    ${result}[has_rule_001]
    Should Be True    ${result}[has_rule_002]
    Should Be Equal As Integers    ${result}[failed_tests_count]    1

Write Markdown Report
    [Documentation]    GIVEN report WHEN writing markdown THEN file created with content
    [Tags]    unit    evidence    create    certification
    ${result}=    Write Markdown Report
    Should Be True    ${result}[file_exists]
    Should Be True    ${result}[has_header]
    Should Be True    ${result}[has_report_id]
    Should Be True    ${result}[has_milestone]
    Should Be True    ${result}[has_rate]
    Should Be True    ${result}[has_rule]

Write JSON Report
    [Documentation]    GIVEN report WHEN writing JSON THEN file created with valid JSON
    [Tags]    unit    evidence    create    certification
    ${result}=    Write Json Report
    Should Be True    ${result}[file_exists]
    Should Be Equal    ${result}[report_id]    CERT-TEST
    Should Be Equal As Integers    ${result}[passed]    8

Find Latest Run Dir
    [Documentation]    GIVEN multiple run directories WHEN finding latest THEN returns most recent
    [Tags]    unit    evidence    validate    certification
    ${result}=    Find Latest Run Dir
    Should Be True    ${result}

Generate Certification Function
    [Documentation]    GIVEN CLI function WHEN generating THEN creates reports
    [Tags]    unit    evidence    create    certification
    ${result}=    Generate Certification Function
    Should Be Equal As Integers    ${result}[total_tests]    1
    Should Be Equal As Integers    ${result}[passed]    1
    Should Be Equal As Integers    ${result}[rules_covered]    1
    Should Be True    ${result}[markdown_exists]
    Should Be True    ${result}[json_exists]

