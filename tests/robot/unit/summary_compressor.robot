*** Settings ***
Documentation    RF-004: Unit Tests - Summary Compressor
...              Migrated from tests/unit/test_summary_compressor.py
...              Per EPIC-TEST-COMPRESS-001: Test results compression
Library          Collections
Library          ../../libs/SummaryCompressorLibrary.py

*** Test Cases ***
# =============================================================================
# CompressedTestSummary Tests
# =============================================================================

Format Oneline All Passed
    [Documentation]    GIVEN all passed WHEN format oneline THEN shows 100%
    [Tags]    unit    evidence    validate    compress
    ${result}=    Format Oneline All Passed
    Should Be True    ${result}[has_count]
    Should Be True    ${result}[has_percent]
    Should Be True    ${result}[has_duration]
    Should Be True    ${result}[no_failed]

Format Oneline With Failures
    [Documentation]    GIVEN failures WHEN format oneline THEN highlights failures
    [Tags]    unit    evidence    validate    compress
    ${result}=    Format Oneline With Failures
    Should Be True    ${result}[has_count]
    Should Be True    ${result}[has_failed]

Format Compact Shows Failures
    [Documentation]    GIVEN failures WHEN format compact THEN shows details
    [Tags]    unit    evidence    validate    compress
    ${result}=    Format Compact Shows Failures
    Should Be True    ${result}[has_fail_marker]
    Should Be True    ${result}[has_test_one]
    Should Be True    ${result}[has_test_two]
    Should Be True    ${result}[has_assertion_error]

Format Compact Truncates Failures
    [Documentation]    GIVEN many failures WHEN format compact THEN truncates
    [Tags]    unit    evidence    validate    compress
    ${result}=    Format Compact Truncates Failures
    Should Be True    ${result}[has_test_0]
    Should Be True    ${result}[has_test_4]
    Should Be True    ${result}[has_more]

Format TOON Is Machine Readable
    [Documentation]    GIVEN summary WHEN format toon THEN machine readable
    [Tags]    unit    evidence    validate    compress    toon
    ${result}=    Format Toon
    Should Be True    ${result}[has_tests]
    Should Be True    ${result}[has_stats]
    Should Be True    ${result}[has_duration]
    Should Be True    ${result}[has_compression]

To Dict Includes All Fields
    [Documentation]    GIVEN summary WHEN to_dict THEN all fields present
    [Tags]    unit    evidence    validate    compress
    ${result}=    To Dict
    Should Be Equal As Integers    ${result}[total]    10
    Should Be Equal As Integers    ${result}[passed]    9
    Should Be Equal    ${result}[success_rate]    90%

# =============================================================================
# SummaryCompressor Tests
# =============================================================================

Estimate Tokens Approximates
    [Documentation]    GIVEN text WHEN estimating tokens THEN ~4 chars/token
    [Tags]    unit    evidence    validate    compress
    ${result}=    Estimate Tokens
    Should Be Equal As Integers    ${result}[100_chars]    25
    Should Be Equal As Integers    ${result}[empty]    0

Format Duration Milliseconds
    [Documentation]    GIVEN ms WHEN formatting THEN ms string
    [Tags]    unit    evidence    validate    compress
    ${result}=    Format Duration Milliseconds
    Should Be Equal    ${result}[500ms]    500ms
    Should Be Equal    ${result}[50ms]    50ms

Format Duration Seconds
    [Documentation]    GIVEN seconds WHEN formatting THEN s string
    [Tags]    unit    evidence    validate    compress
    ${result}=    Format Duration Seconds
    Should Be Equal    ${result}[5000ms]    5.0s
    Should Be Equal    ${result}[30500ms]    30.5s

Format Duration Minutes
    [Documentation]    GIVEN minutes WHEN formatting THEN m:s string
    [Tags]    unit    evidence    validate    compress
    ${result}=    Format Duration Minutes
    Should Be Equal    ${result}[90000ms]    1m30s
    Should Be Equal    ${result}[150000ms]    2m30s

Compress Test List Basic
    [Documentation]    GIVEN tests WHEN compressing THEN stats correct
    [Tags]    unit    evidence    validate    compress
    ${result}=    Compress Test List Basic
    Should Be Equal As Integers    ${result}[total]    3
    Should Be Equal As Integers    ${result}[passed]    2
    Should Be Equal As Integers    ${result}[failed]    1
    Should Be Equal As Integers    ${result}[failure_count]    1
    Should Be Equal    ${result}[failure_error]    AssertionError

Compress Test List Categories
    [Documentation]    GIVEN tests WHEN compressing THEN grouped by category
    [Tags]    unit    evidence    validate    compress
    ${result}=    Compress Test List Categories
    Should Be True    ${result}[has_unit]
    Should Be True    ${result}[has_e2e]
    Should Be Equal As Integers    ${result}[unit_passed]    2
    Should Be Equal As Integers    ${result}[e2e_failed]    1

Compress Test List Truncates Errors
    [Documentation]    GIVEN long error WHEN compressing THEN truncated
    [Tags]    unit    evidence    validate    compress
    ${result}=    Compress Test List Truncates Errors
    Should Be True    ${result}[error_truncated]

Compress Test List Limits Failures
    [Documentation]    GIVEN many failures WHEN compressing THEN limited
    [Tags]    unit    evidence    validate    compress
    ${result}=    Compress Test List Limits Failures
    Should Be Equal As Integers    ${result}[failure_count]    3

Compress Calculates Compression Ratio
    [Documentation]    GIVEN tests WHEN compressing THEN ratio calculated
    [Tags]    unit    evidence    validate    compress
    ${result}=    Compress Calculates Compression Ratio
    Should Be True    ${result}[has_original_tokens]
    Should Be True    ${result}[has_compressed_tokens]
    Should Be True    ${result}[has_percent]

# =============================================================================
# Convenience Functions Tests
# =============================================================================

Compress Tests Function Returns Compact
    [Documentation]    GIVEN tests WHEN compress_tests THEN compact format
    [Tags]    unit    evidence    validate    compress
    ${result}=    Compress Tests Function
    Should Be True    ${result}[has_fail]
    Should Be True    ${result}[has_count]

Oneline Summary Function Returns Single Line
    [Documentation]    GIVEN tests WHEN oneline_summary THEN single line
    [Tags]    unit    evidence    validate    compress
    ${result}=    Oneline Summary Function
    Should Be True    ${result}[no_newline]
    Should Be True    ${result}[has_count]

