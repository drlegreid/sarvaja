*** Settings ***
Documentation    RF-004: Unit Tests - Trace Event Query Param Parsing
...              Migrated from tests/unit/test_trace_event.py
...              Per GAP-UI-TRACE-001: Trace bar request params visibility
Library          Collections
Library          ../../libs/TraceEventLibrary.py
Force Tags        unit    trace    events    medium    TEST-EVID-01-v1    session    validate

*** Test Cases ***
# =============================================================================
# Query Parameter Parsing Tests
# =============================================================================

Parse Endpoint Simple Path Returns Path Only
    [Documentation]    GIVEN endpoint without query params WHEN parsed THEN returns path only
    [Tags]    unit    ui    validate    api    query-params
    ${event}=    Create Api Call Event    GET /rules    /rules    GET
    ${path}=    Get Path    ${event}
    ${params}=    Get Query Params    ${event}
    Should Be Equal    ${path}    /rules
    Should Be Equal    ${params}    ${None}

Parse Endpoint With Single Param
    [Documentation]    GIVEN endpoint with single query param WHEN parsed THEN param extracted
    [Tags]    unit    ui    validate    api    query-params
    ${event}=    Create Api Call Event    GET /rules?search=test    /rules?search=test    GET
    ${path}=    Get Path    ${event}
    ${search}=    Get Query Param    ${event}    search
    Should Be Equal    ${path}    /rules
    Should Be Equal    ${search}    test

Parse Endpoint With Multiple Params
    [Documentation]    GIVEN endpoint with multiple params WHEN parsed THEN all extracted
    [Tags]    unit    ui    validate    api    query-params
    ${event}=    Create Api Call Event    GET /rules?search=test&limit=10&offset=0    /rules?search=test&limit=10&offset=0    GET
    ${path}=    Get Path    ${event}
    ${search}=    Get Query Param    ${event}    search
    ${limit}=    Get Query Param    ${event}    limit
    ${offset}=    Get Query Param    ${event}    offset
    Should Be Equal    ${path}    /rules
    Should Be Equal    ${search}    test
    Should Be Equal    ${limit}    10
    Should Be Equal    ${offset}    0

Parse Endpoint With Repeated Param Returns List
    [Documentation]    GIVEN endpoint with repeated param WHEN parsed THEN returns list
    [Tags]    unit    ui    validate    api    query-params
    ${event}=    Create Api Call Event    GET /rules?tag=a&tag=b&tag=c    /rules?tag=a&tag=b&tag=c    GET
    ${path}=    Get Path    ${event}
    ${tags}=    Get Query Param    ${event}    tag
    Should Be Equal    ${path}    /rules
    ${expected}=    Create List    a    b    c
    Lists Should Be Equal    ${tags}    ${expected}

Parse Endpoint None Returns None
    [Documentation]    GIVEN None endpoint WHEN parsed THEN returns None path and params
    [Tags]    unit    ui    validate    api    query-params
    ${event}=    Create Api Call Event    API call    ${None}    GET
    ${path}=    Get Path    ${event}
    ${params}=    Get Query Params    ${event}
    Should Be Equal    ${path}    ${None}
    Should Be Equal    ${params}    ${None}

Parse Endpoint Empty Query Returns No Params
    [Documentation]    GIVEN endpoint with empty query WHEN parsed THEN no params
    [Tags]    unit    ui    validate    api    query-params
    ${event}=    Create Api Call Event    GET /rules?    /rules?    GET
    ${path}=    Get Path    ${event}
    ${params}=    Get Query Params    ${event}
    Should Be Equal    ${path}    /rules
    Should Be Equal    ${params}    ${None}

Parse Endpoint URL Encoded Value Decoded
    [Documentation]    GIVEN URL-encoded param WHEN parsed THEN decoded correctly
    [Tags]    unit    ui    validate    api    query-params
    ${event}=    Create Api Call Event    GET /rules?search=hello%20world    /rules?search=hello%20world    GET
    ${path}=    Get Path    ${event}
    ${search}=    Get Query Param    ${event}    search
    Should Be Equal    ${path}    /rules
    Should Be Equal    ${search}    hello world

# =============================================================================
# To Dict Serialization Tests
# =============================================================================

To Dict Includes All Fields
    [Documentation]    GIVEN trace event with all fields WHEN to_dict THEN all present
    [Tags]    unit    ui    validate    serialize
    &{req_body}=    Create Dictionary    filter=active
    &{resp_body}=    Create Dictionary    rules=@{EMPTY}
    &{headers}=    Create Dictionary    Authorization=Bearer xxx
    ${event}=    Create Api Call Event
    ...    message=GET /rules
    ...    endpoint=/rules?limit=10
    ...    method=GET
    ...    status_code=200
    ...    duration_ms=150
    ...    request_body=${req_body}
    ...    response_body=${resp_body}
    ...    request_headers=${headers}
    Should Be Equal    ${event}[event_type]    api_call
    Should Be Equal    ${event}[message]    GET /rules
    Should Be Equal    ${event}[path]    /rules
    Should Be Equal    ${event}[method]    GET
    Should Be Equal As Integers    ${event}[status_code]    200
    Should Be Equal As Numbers    ${event}[duration_ms]    150

UI Action Event Has No Query Params
    [Documentation]    GIVEN UI action event WHEN to_dict THEN no query params
    [Tags]    unit    ui    validate    action
    ${event}=    Create Ui Action Event    click on button    click    submit-btn    form
    ${type}=    Get Event Type    ${event}
    ${path}=    Get Path    ${event}
    ${params}=    Get Query Params    ${event}
    Should Be Equal    ${type}    ui_action
    Should Be Equal    ${path}    ${None}
    Should Be Equal    ${params}    ${None}
    Should Be Equal    ${event}[action]    click
    Should Be Equal    ${event}[component]    submit-btn

