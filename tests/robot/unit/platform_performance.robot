*** Settings ***
Documentation    Platform Performance Heuristic Tests
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/heuristics/test_platform_performance.py
...              Tests Platform/Time (SFDIPOT) and Charisma/Scalability (CRUCSS).
Library          Collections
Library          ../../libs/PlatformPerformanceLibrary.py
Resource         ../resources/common.resource
Tags             unit    heuristics    performance    platform

*** Test Cases ***
# =============================================================================
# SFDIPOT: Platform Tests
# =============================================================================

Test Health Endpoint Responds
    [Documentation]    Health endpoint should respond
    [Tags]    sfdipot    platform    health
    ${result}=    Health Endpoint Responds
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['responds']}

Test Environment Vars Documented
    [Documentation]    Required environment variables should be documented
    [Tags]    sfdipot    platform    environment
    ${result}=    Environment Vars Documented
    Should Be True    ${result['count_correct']}

Test Content Type JSON Accepted
    [Documentation]    API should accept application/json
    [Tags]    sfdipot    platform    content-type
    ${result}=    Content Type JSON Accepted
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['accepted']}

# =============================================================================
# SFDIPOT: Time Tests
# =============================================================================

Test API Latency Acceptable
    [Documentation]    API should respond within 2 seconds
    [Tags]    sfdipot    time    latency
    ${result}=    API Latency Acceptable
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['within_threshold']}

Test No Performance Degradation
    [Documentation]    Multiple requests should maintain performance
    [Tags]    sfdipot    time    degradation
    ${result}=    No Performance Degradation
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['no_degradation']}

Test Timeout Handling Works
    [Documentation]    API should handle timeouts gracefully
    [Tags]    sfdipot    time    timeout
    ${result}=    Timeout Handling Works
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['timeout_handled']}

# =============================================================================
# CRUCSS: Charisma Tests
# =============================================================================

Test Response Structure Valid
    [Documentation]    Responses should be well-formatted JSON
    [Tags]    crucss    charisma    response
    ${result}=    Response Structure Valid
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['valid_structure']}

Test Error Messages User Friendly
    [Documentation]    Error messages should be helpful
    [Tags]    crucss    charisma    errors
    ${result}=    Error Messages User Friendly
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['has_error_message']}

Test Dashboard Overview Available
    [Documentation]    Dashboard should provide useful summary
    [Tags]    crucss    charisma    dashboard
    ${result}=    Dashboard Overview Available
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['endpoint_exists']}

# =============================================================================
# CRUCSS: Scalability Tests
# =============================================================================

Test Pagination Support
    [Documentation]    API should support pagination
    [Tags]    crucss    scalability    pagination
    ${result}=    Pagination Support
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['pagination_works']}

Test Large Results Handled
    [Documentation]    API should handle large result requests
    [Tags]    crucss    scalability    limits
    ${result}=    Large Results Handled
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['handles_large_requests']}

Test Concurrent Requests Supported
    [Documentation]    API should handle concurrent requests
    [Tags]    crucss    scalability    concurrency
    ${result}=    Concurrent Requests Supported
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['concurrency_works']}
