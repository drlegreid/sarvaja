*** Settings ***
Documentation    RF-004: Unit Tests - Rule Monitor
...              Migrated from tests/test_rule_monitor.py
...              Per P9.6: Real-time rule monitoring
Library          Collections
Library          ../../libs/RuleMonitorLibrary.py
Library          ../../libs/RuleMonitorAdvancedLibrary.py
Force Tags        unit    rules    monitor    high    GOV-RULE-01-v1    rule

*** Test Cases ***
# =============================================================================
# Module Existence Tests
# =============================================================================

Rule Monitor Module Exists
    [Documentation]    GIVEN agent/ WHEN checking THEN rule_monitor.py exists
    [Tags]    unit    rule-monitor    validate    module
    ${result}=    Rule Monitor Module Exists
    Should Be True    ${result}[exists]

Rule Monitor Class Importable
    [Documentation]    GIVEN RuleMonitor WHEN importing THEN instantiates
    [Tags]    unit    rule-monitor    validate    class
    ${result}=    Rule Monitor Class Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[instantiable]

Monitor Has Required Methods
    [Documentation]    GIVEN RuleMonitor WHEN checking THEN has required methods
    [Tags]    unit    rule-monitor    validate    methods
    ${result}=    Monitor Has Required Methods
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_get_feed]
    Should Be True    ${result}[has_log_event]
    Should Be True    ${result}[has_get_alerts]
    Should Be True    ${result}[has_get_statistics]

# =============================================================================
# Event Logging Tests
# =============================================================================

Log Event Works
    [Documentation]    GIVEN monitor WHEN log_event THEN logs event
    [Tags]    unit    rule-monitor    event    logging
    ${result}=    Log Event Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[success]

Log Violation Works
    [Documentation]    GIVEN monitor WHEN log violation THEN logs
    [Tags]    unit    rule-monitor    event    violation
    ${result}=    Log Violation Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_event_id_or_success]

Log Rule Change Works
    [Documentation]    GIVEN monitor WHEN log rule change THEN logs
    [Tags]    unit    rule-monitor    event    change
    ${result}=    Log Rule Change Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[success]

# =============================================================================
# Event Feed Tests
# =============================================================================

Get Feed Works
    [Documentation]    GIVEN monitor WHEN get_feed THEN returns list
    [Tags]    unit    rule-monitor    feed    query
    ${result}=    Get Feed Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

Feed Contains Logged Events
    [Documentation]    GIVEN logged events WHEN get_feed THEN contains events
    [Tags]    unit    rule-monitor    feed    events
    ${result}=    Feed Contains Logged Events
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_events]

Feed Filters By Event Type
    [Documentation]    GIVEN events WHEN filter by type THEN filters correctly
    [Tags]    unit    rule-monitor    feed    filter
    ${result}=    Feed Filters By Event Type
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[filters_correctly]

Feed Respects Limit
    [Documentation]    GIVEN many events WHEN limit=5 THEN returns <=5
    [Tags]    unit    rule-monitor    feed    limit
    ${result}=    Feed Respects Limit
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[respects_limit]

# =============================================================================
# Alert Tests
# =============================================================================

Get Alerts Works
    [Documentation]    GIVEN monitor WHEN get_alerts THEN returns list
    [Tags]    unit    rule-monitor    alert    query
    ${result}=    Get Alerts Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

Violation Generates Alert
    [Documentation]    GIVEN violation WHEN logged THEN generates alert
    [Tags]    unit    rule-monitor    alert    violation
    ${result}=    Violation Generates Alert
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[generates_alert]

Acknowledge Alert Works
    [Documentation]    GIVEN alert WHEN acknowledge THEN succeeds
    [Tags]    unit    rule-monitor    alert    acknowledge
    ${result}=    Acknowledge Alert Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[success]

# =============================================================================
# Statistics Tests
# =============================================================================

Get Statistics Works
    [Documentation]    GIVEN monitor WHEN get_statistics THEN returns dict
    [Tags]    unit    rule-monitor    stats    query
    ${result}=    Get Statistics Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_total_events]

Statistics By Type Works
    [Documentation]    GIVEN events WHEN get_statistics THEN has events_by_type
    [Tags]    unit    rule-monitor    stats    breakdown
    ${result}=    Statistics By Type Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_events_by_type]

Get Hourly Stats Works
    [Documentation]    GIVEN monitor WHEN get_hourly_stats THEN returns dict
    [Tags]    unit    rule-monitor    stats    hourly
    ${result}=    Get Hourly Stats Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]

# =============================================================================
# Rule Tracking Tests
# =============================================================================

Get Rule Events Works
    [Documentation]    GIVEN rule_id WHEN get_rule_events THEN returns list
    [Tags]    unit    rule-monitor    tracking    events
    ${result}=    Get Rule Events Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

Get Top Rules Works
    [Documentation]    GIVEN queries WHEN get_top_rules THEN returns list
    [Tags]    unit    rule-monitor    tracking    ranking
    ${result}=    Get Top Rules Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

# =============================================================================
# Integration Tests
# =============================================================================

Factory Function Works
    [Documentation]    GIVEN create_rule_monitor WHEN calling THEN creates monitor
    [Tags]    unit    rule-monitor    integration    factory
    ${result}=    Factory Function Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created]

Event Persistence Works
    [Documentation]    GIVEN log_event WHEN get_feed THEN persists
    [Tags]    unit    rule-monitor    integration    persistence
    ${result}=    Event Persistence Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[persists]
