*** Settings ***
Documentation    RF-004: Unit Tests - Trace Capture Module
...              Migrated from tests/unit/test_trace_capture.py
...              Per RD-TESTING-STRATEGY TEST-002: Evidence collection at trace level
Library          Collections
Library          ../../libs/TraceCaptureLibrary.py

*** Test Cases ***
# =============================================================================
# TraceRecord Tests
# =============================================================================

HTTP Trace Record Creation
    [Documentation]    GIVEN TraceRecord WHEN creating HTTP trace THEN fields are set correctly
    [Tags]    unit    evidence    create    trace
    ${result}=    Create Http Trace Record
    Should Be Equal    ${result}[trace_type]    http
    Should Be Equal    ${result}[method]    GET
    Should Be Equal As Integers    ${result}[status_code]    200
    Should Be Equal As Numbers    ${result}[duration_ms]    150.5

MCP Trace Record Creation
    [Documentation]    GIVEN TraceRecord WHEN creating MCP trace THEN fields are set correctly
    [Tags]    unit    evidence    create    trace
    ${result}=    Create Mcp Trace Record
    Should Be Equal    ${result}[trace_type]    mcp
    Should Be Equal    ${result}[tool_name]    rules_query
    Dictionary Should Contain Key    ${result}[arguments]    status

Trace Record To Dict
    [Documentation]    GIVEN TraceRecord WHEN converting to dict THEN all fields present
    [Tags]    unit    evidence    validate    trace
    ${data}=    Trace Record To Dict
    Should Be Equal    ${data}[trace_id]    TR-12345678
    Should Be Equal    ${data}[correlation_id]    TEST-20260121-ABC123
    Should Be Equal    ${data}[trace_type]    http
    Should Be Equal    ${data}[method]    POST
    Should Be Equal As Integers    ${data}[status_code]    201

Trace Record Truncation
    [Documentation]    GIVEN large response body WHEN converting to dict THEN truncated
    [Tags]    unit    evidence    validate    trace
    ${result}=    Trace Record Truncation
    Should Be True    ${result}[is_truncated]
    Should Be True    ${result}[length_under_5000]

# =============================================================================
# TraceCapture Initialization Tests
# =============================================================================

Trace Capture Initialization
    [Documentation]    GIVEN TraceCapture WHEN initializing THEN test_id set and correlation_id generated
    [Tags]    unit    evidence    create    trace
    ${ok}=    Create Trace Capture    tests/test_example.py::test_func
    Should Be True    ${ok}
    ${info}=    Get Capture Info
    Should Be Equal    ${info}[test_id]    tests/test_example.py::test_func
    Should Be True    ${info}[correlation_starts_with_test]
    Should Be Equal As Integers    ${info}[traces_count]    0

Correlation ID Format Valid
    [Documentation]    GIVEN TraceCapture WHEN checking format THEN starts with TEST and has parts
    [Tags]    unit    evidence    validate    trace
    ${valid}=    Correlation Id Format Valid
    Should Be True    ${valid}

Custom Correlation ID
    [Documentation]    GIVEN custom correlation ID WHEN creating capture THEN uses custom ID
    [Tags]    unit    evidence    validate    trace
    ${matches}=    Custom Correlation Id    CUSTOM-CORR-12345
    Should Be True    ${matches}

Headers Property Has Required Headers
    [Documentation]    GIVEN TraceCapture WHEN getting headers THEN has correlation/test/trace headers
    [Tags]    unit    evidence    validate    trace
    ${result}=    Headers Property
    Should Be True    ${result}[has_correlation_id]
    Should Be True    ${result}[has_test_id]
    Should Be True    ${result}[has_trace_enabled]
    Should Be Equal    ${result}[test_id_value]    test_example

# =============================================================================
# TraceCapture Lifecycle Tests
# =============================================================================

Start End Lifecycle
    [Documentation]    GIVEN TraceCapture WHEN start/end called THEN state changes correctly
    [Tags]    unit    evidence    validate    trace
    ${result}=    Start End Lifecycle
    # Before start
    Should Be Equal    ${result}[before_start][start_time]    ${None}
    Should Not Be True    ${result}[before_start][active]
    # After start
    Should Be True    ${result}[after_start][start_time_set]
    Should Be True    ${result}[after_start][active]
    # After end
    Should Be True    ${result}[after_end][end_time_set]
    Should Not Be True    ${result}[after_end][active]

# =============================================================================
# TraceCapture Recording Tests
# =============================================================================

Record HTTP Trace
    [Documentation]    GIVEN started capture WHEN recording HTTP THEN trace added with correct fields
    [Tags]    unit    evidence    create    trace
    ${result}=    Record Http Trace
    Should Be Equal As Integers    ${result}[traces_count]    1
    Should Be Equal    ${result}[trace_type]    http
    Should Be Equal    ${result}[method]    GET
    Should Be True    ${result}[correlation_matches]

Record MCP Trace
    [Documentation]    GIVEN started capture WHEN recording MCP THEN trace added with correct fields
    [Tags]    unit    evidence    create    trace
    ${result}=    Record Mcp Trace
    Should Be Equal As Integers    ${result}[traces_count]    1
    Should Be Equal    ${result}[trace_type]    mcp
    Should Be Equal    ${result}[tool_name]    rules_query

Get Traces As Dicts
    [Documentation]    GIVEN traces recorded WHEN getting traces THEN returns list of dicts
    [Tags]    unit    evidence    validate    trace
    ${result}=    Get Traces As Dicts
    Should Be Equal As Integers    ${result}[count]    2
    Should Be True    ${result}[all_dicts]
    Should Be Equal    ${result}[first_type]    http
    Should Be Equal    ${result}[second_type]    mcp

Get Summary Has Required Fields
    [Documentation]    GIVEN multiple traces WHEN getting summary THEN has all statistics
    [Tags]    unit    evidence    validate    trace
    ${summary}=    Get Summary
    Should Be Equal    ${summary}[test_id]    test_example
    Should Be Equal As Integers    ${summary}[total_traces]    4
    Should Be Equal As Integers    ${summary}[http_traces]    3
    Should Be Equal As Integers    ${summary}[mcp_traces]    1
    Should Be Equal As Integers    ${summary}[total_duration_ms]    325
    Should Be Equal As Integers    ${summary}[status_codes][2xx]    2
    Should Be Equal As Integers    ${summary}[status_codes][4xx]    1

Capture Context Manager
    [Documentation]    GIVEN context manager WHEN entering/exiting THEN state managed correctly
    [Tags]    unit    evidence    validate    trace
    ${result}=    Capture Context Manager
    Should Be True    ${result}[active_in_context]
    Should Not Be True    ${result}[active_after_context]
    Should Be Equal As Integers    ${result}[traces_count]    1

# =============================================================================
# RequestsTraceAdapter Tests
# =============================================================================

Adapter Initialization
    [Documentation]    GIVEN RequestsTraceAdapter WHEN creating THEN trace_capture set
    [Tags]    unit    evidence    validate    trace
    ${matches}=    Adapter Initialization
    Should Be True    ${matches}

Adapter Patches Requests
    [Documentation]    GIVEN adapter WHEN patching THEN requests library is patched and restored
    [Tags]    unit    evidence    validate    trace
    ${result}=    Adapter Patches Requests
    Should Be True    ${result}[is_patched]
    Should Be True    ${result}[is_restored]

# =============================================================================
# Link Traces to Evidence Tests
# =============================================================================

Link Traces To Evidence
    [Documentation]    GIVEN traces and evidence WHEN linking THEN evidence has trace data
    [Tags]    unit    evidence    validate    trace
    ${result}=    Link Traces To Evidence
    Should Be True    ${result}[has_traces]
    Should Be True    ${result}[has_trace_summary]
    Should Be True    ${result}[has_correlation_id]
    Should Be Equal As Integers    ${result}[traces_count]    1
    Should Be True    ${result}[correlation_matches]

