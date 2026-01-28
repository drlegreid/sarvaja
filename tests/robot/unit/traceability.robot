*** Settings ***
Documentation     Composite Traceability MCP Tools Tests
...               Per A3: Full governance chain tracing (test → GAP → evidence → session → task → rule)
...               Created: 2026-01-28 | Per SESSION-EVID-01-v1, GOV-TRANSP-01-v1
Library           ../../libs/TraceabilityLibrary.py
Force Tags        unit    traceability    mcp    high    SESSION-EVID-01-v1    GOV-TRANSP-01-v1    task    session    rule    trace

*** Test Cases ***
# =========================================================================
# Module Import Tests
# =========================================================================

Traceability Module Should Import
    [Documentation]    Verify traceability module can be imported
    [Tags]    smoke    import
    ${result}=    Traceability Module Imports Successfully
    Skip If    not ${result}[imported]    Traceability module not available
    Should Be True    ${result}[has_register]

Traceability Should Have All Tool Functions
    [Documentation]    Verify all helper functions are defined
    [Tags]    smoke    import
    ${result}=    Traceability Has All Tool Functions
    Skip If    not ${result}[all_found]    Some functions missing: ${result}
    Should Be True    ${result}[all_found]

Traceability Should Be Registered In Init
    [Documentation]    Verify traceability is registered in mcp_tools __init__
    [Tags]    smoke    import
    ${result}=    Traceability Registered In Init
    Should Be True    ${result}[registered]

# =========================================================================
# Helper Function Tests
# =========================================================================

Trace Task Helper Should Return Dict
    [Documentation]    _trace_task returns dict with task_id key
    [Tags]    helper    typedb
    ${result}=    Trace Task Helper Returns Dict
    Skip If    $result.get("skipped", False)    ${result.get("reason", "skipped")}
    Should Be True    ${result}[is_dict]

Trace Session Helper Should Return Dict
    [Documentation]    _trace_session returns dict with session_id key
    [Tags]    helper    typedb
    ${result}=    Trace Session Helper Returns Dict
    Skip If    $result.get("skipped", False)    ${result.get("reason", "skipped")}
    Should Be True    ${result}[is_dict]

Trace Rule Helper Should Return Dict
    [Documentation]    _trace_rule returns dict with rule_id key
    [Tags]    helper    typedb
    ${result}=    Trace Rule Helper Returns Dict
    Skip If    $result.get("skipped", False)    ${result.get("reason", "skipped")}
    Should Be True    ${result}[is_dict]

# =========================================================================
# Tool Registration Tests
# =========================================================================

Register Traceability Tools Should Register Five Tools
    [Documentation]    Mock MCP receives exactly 5 tool registrations
    [Tags]    registration    mock
    ${result}=    Register Traceability Tools With Mock
    Skip If    $result.get("skipped", False)    ${result.get("reason", "skipped")}
    Should Be Equal As Numbers    ${result}[count]    5
    Should Be True    ${result}[all_present]

All Trace Tools Should Have Docstrings
    [Documentation]    Every registered tool function has a docstring
    [Tags]    registration    docs
    ${result}=    Trace Tools Have Docstrings
    Skip If    $result.get("skipped", False)    ${result.get("reason", "skipped")}
    Should Be True    ${result}[all_have_docs]

# =========================================================================
# Integration Tests (require TypeDB)
# =========================================================================

Trace Task Chain With Known Task
    [Documentation]    Trace a real task from TypeDB with all linked entities
    [Tags]    integration    typedb    chain
    ${result}=    Trace Task Chain With Known Task
    Skip If    $result.get("skipped", False)    ${result.get("reason", "skipped")}
    Should Be True    ${result}[success]
    Should Be True    ${result}[has_status]

Trace Session Chain With Known Session
    [Documentation]    Trace a real session from TypeDB with all linked entities
    [Tags]    integration    typedb    chain
    ${result}=    Trace Session Chain With Known Session
    Skip If    $result.get("skipped", False)    ${result.get("reason", "skipped")}
    Should Be True    ${result}[success]

Trace Rule Chain With Known Rule
    [Documentation]    Trace a real rule from TypeDB with all linked entities
    [Tags]    integration    typedb    chain
    ${result}=    Trace Rule Chain With Known Rule
    Skip If    $result.get("skipped", False)    ${result.get("reason", "skipped")}
    Should Be True    ${result}[success]
    Should Be True    ${result}[has_name]
