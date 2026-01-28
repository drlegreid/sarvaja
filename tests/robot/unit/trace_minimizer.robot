*** Settings ***
Documentation    RF-004: Unit Tests - Trace Minimizer Module
...              Migrated from tests/unit/test_trace_minimizer.py
...              Per RD-TESTING-STRATEGY TEST-003: Trace minimization
Library          Collections
Library          ../../libs/TraceMinimzerLibrary.py
Force Tags        unit    trace    minimizer    low    TEST-EVID-01-v1    session    validate

Suite Setup      Create Trace Minimizer

*** Test Cases ***
# =============================================================================
# Error Classification Tests
# =============================================================================

Classify Assertion Error
    [Documentation]    Test classifying AssertionError
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Assertion Error
    ${result}=    Classify Error    ${tb}
    Should Be Equal    ${result}[error_type]    AssertionError
    Should Be Equal    ${result}[category]    assertion

Classify Attribute Error
    [Documentation]    Test classifying AttributeError
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Attribute Error
    ${result}=    Classify Error    ${tb}
    Should Be Equal    ${result}[error_type]    AttributeError
    Should Be Equal    ${result}[category]    attribute

Classify Timeout Error
    [Documentation]    Test classifying TimeoutError
    [Tags]    unit    evidence    validate    trace
    ${result}=    Classify Error    TimeoutError: Connection timed out
    Should Contain    ${result}[error_type]    Timeout
    Should Be Equal    ${result}[category]    timeout

Classify Import Error
    [Documentation]    Test classifying ImportError
    [Tags]    unit    evidence    validate    trace
    ${result}=    Classify Error    ImportError: No module named 'missing'
    Should Be Equal    ${result}[error_type]    ImportError
    Should Be Equal    ${result}[category]    import

Classify Value Error
    [Documentation]    Test classifying ValueError
    [Tags]    unit    evidence    validate    trace
    ${result}=    Classify Error    ValueError: Invalid value
    Should Be Equal    ${result}[error_type]    ValueError
    Should Be Equal    ${result}[category]    value

Classify Unknown Error
    [Documentation]    Test classifying unknown error
    [Tags]    unit    evidence    validate    trace
    ${result}=    Classify Error    SomeCustomError: Something happened
    Should Contain    ${result}[error_type]    CustomError
    Should Be Equal    ${result}[category]    unknown

# =============================================================================
# Message Extraction Tests
# =============================================================================

Extract Assertion Message
    [Documentation]    Test extracting assertion error message
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Assertion Error
    ${message}=    Extract Error Message    ${tb}
    Should Contain    ${message}    INACTIVE
    Should Contain    ${message}    ACTIVE

Extract Attribute Message
    [Documentation]    Test extracting attribute error message
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Attribute Error
    ${message}=    Extract Error Message    ${tb}
    Should Contain    ${message}    NoneType
    Should Contain    ${message}    calculate

# =============================================================================
# Frame Filtering Tests
# =============================================================================

Parse And Filter Frames From Long Traceback
    [Documentation]    Test parsing and filtering frames from long traceback
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Long Traceback
    ${result}=    Parse And Filter Frames    ${tb}
    Should Be True    ${result}[count] >= 1

Filtered Frames Exclude Pytest Internals
    [Documentation]    Filtered frames exclude _pytest and pluggy
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Long Traceback
    ${excludes}=    Frames Exclude Pytest Internals    ${tb}
    Should Be True    ${excludes}

Filtered Frames Include Project Code
    [Documentation]    Filtered frames include project code
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Long Traceback
    ${includes}=    Frames Include Project Code    ${tb}
    Should Be True    ${includes}

# =============================================================================
# Token Estimation Tests
# =============================================================================

Estimate Tokens Returns Positive
    [Documentation]    Token estimation returns positive number
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Assertion Error
    ${tokens}=    Estimate Tokens    ${tb}
    Should Be True    ${tokens} > 0

# =============================================================================
# Trace Minimization Tests
# =============================================================================

Minimize Traceback Returns Required Fields
    [Documentation]    Minimized trace has all required fields
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Assertion Error
    ${result}=    Minimize Traceback    ${tb}    test_id=test_example
    Dictionary Should Contain Key    ${result}    error_type
    Dictionary Should Contain Key    ${result}    category
    Dictionary Should Contain Key    ${result}    message
    Dictionary Should Contain Key    ${result}    frame_count
    Dictionary Should Contain Key    ${result}    original_tokens
    Dictionary Should Contain Key    ${result}    minimized_tokens

Minimize Traceback Reduces Tokens
    [Documentation]    Minimization reduces token count
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Long Traceback
    ${result}=    Minimize Traceback    ${tb}    test_id=test_long
    Should Be True    ${result}[minimized_tokens] <= ${result}[original_tokens]

Minimize For LLM Returns String
    [Documentation]    minimize_for_llm returns formatted string
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Assertion Error
    ${output}=    Minimize For Llm    ${tb}    test_id=test_llm
    ${length}=    Get Length    ${output}
    Should Be True    ${length} > 0

Estimate Compression Returns Dict
    [Documentation]    estimate_compression returns statistics
    [Tags]    unit    evidence    validate    trace
    ${tb}=    Get Sample Long Traceback
    ${minimized}=    Minimize For Llm    ${tb}    test_id=test_compression
    ${result}=    Estimate Compression    ${tb}    ${minimized}
    Dictionary Should Contain Key    ${result}    original_tokens
    Dictionary Should Contain Key    ${result}    minimized_tokens
    Dictionary Should Contain Key    ${result}    ratio

