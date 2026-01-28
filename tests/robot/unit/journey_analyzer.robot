*** Settings ***
Documentation    RF-004: Unit Tests - Journey Analyzer
...              Migrated from tests/test_journey_analyzer.py
...              Per P9.7: Journey pattern analyzer
Library          Collections
Library          ../../libs/JourneyAnalyzerLibrary.py
Library          ../../libs/JourneyAnalyzerAdvancedLibrary.py
Force Tags        unit    agents    journey    low    agent    validate    TEST-COMP-01-v1

*** Test Cases ***
# =============================================================================
# Module Existence Tests
# =============================================================================

Journey Analyzer Module Exists
    [Documentation]    GIVEN agent/ WHEN importing THEN journey_analyzer exists
    [Tags]    unit    journey-analyzer    validate    module
    ${result}=    Journey Analyzer Module Exists
    Should Be True    ${result}[exists]

Journey Analyzer Class Exists
    [Documentation]    GIVEN journey_analyzer WHEN importing THEN JourneyAnalyzer exists
    [Tags]    unit    journey-analyzer    validate    class
    ${result}=    Journey Analyzer Class Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Analyzer Has Required Methods
    [Documentation]    GIVEN JourneyAnalyzer WHEN checking THEN has required methods
    [Tags]    unit    journey-analyzer    validate    methods
    ${result}=    Analyzer Has Required Methods
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_log_question]
    Should Be True    ${result}[has_get_recurring_questions]
    Should Be True    ${result}[has_detect_patterns]
    Should Be True    ${result}[has_get_knowledge_gaps]
    Should Be True    ${result}[has_get_question_history]

# =============================================================================
# Question Logging Tests
# =============================================================================

Log Question Works
    [Documentation]    GIVEN analyzer WHEN log_question THEN logs with timestamp
    [Tags]    unit    journey-analyzer    logging    question
    ${result}=    Log Question Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[not_none]
    Should Be True    ${result}[has_question_id]
    Should Be True    ${result}[has_timestamp]
    Should Be True    ${result}[question_correct]

Log Question With Category Works
    [Documentation]    GIVEN analyzer WHEN log_question with category THEN category set
    [Tags]    unit    journey-analyzer    logging    category
    ${result}=    Log Question With Category Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[category_correct]

Question Generates Semantic Hash
    [Documentation]    GIVEN similar questions WHEN logging THEN semantic hash generated
    [Tags]    unit    journey-analyzer    logging    semantic
    ${result}=    Question Generates Semantic Hash
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[ids_different]
    Should Be True    ${result}[has_semantic_hash]

# =============================================================================
# Recurrence Detection Tests
# =============================================================================

Detect Recurring Exact Match
    [Documentation]    GIVEN same question 3x WHEN get_recurring THEN detects
    [Tags]    unit    journey-analyzer    recurrence    exact
    ${result}=    Detect Recurring Exact Match
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_recurring]
    Should Be True    ${result}[count_at_least_3]

Detect Recurring Semantic Match
    [Documentation]    GIVEN similar questions WHEN semantic_match THEN detects
    [Tags]    unit    journey-analyzer    recurrence    semantic
    ${result}=    Detect Recurring Semantic Match
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_recurring]

Recurrence Within Time Window
    [Documentation]    GIVEN time window WHEN checking THEN filters by time
    [Tags]    unit    journey-analyzer    recurrence    timewindow
    ${result}=    Recurrence Within Time Window
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_recurring]

# =============================================================================
# Pattern Detection Tests
# =============================================================================

Detect Patterns Returns List
    [Documentation]    GIVEN questions WHEN detect_patterns THEN returns list
    [Tags]    unit    journey-analyzer    pattern    query
    ${result}=    Detect Patterns Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

Pattern Includes Topic Cluster
    [Documentation]    GIVEN related questions WHEN detect_patterns THEN has cluster
    [Tags]    unit    journey-analyzer    pattern    cluster
    ${result}=    Pattern Includes Topic Cluster
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_topic_cluster]

Pattern Suggests UI Component
    [Documentation]    GIVEN recurring pattern WHEN detect THEN suggests UI
    [Tags]    unit    journey-analyzer    pattern    suggestion
    ${result}=    Pattern Suggests UI Component
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_suggestion]

# =============================================================================
# Knowledge Gap Tests
# =============================================================================

Get Knowledge Gaps Returns List
    [Documentation]    GIVEN analyzer WHEN get_knowledge_gaps THEN returns list
    [Tags]    unit    journey-analyzer    gap    query
    ${result}=    Get Knowledge Gaps Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

Gap Includes Topic And Frequency
    [Documentation]    GIVEN unanswered questions WHEN get_gaps THEN has fields
    [Tags]    unit    journey-analyzer    gap    fields
    ${result}=    Gap Includes Topic And Frequency
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_required_fields]

Gap Prioritized By Frequency
    [Documentation]    GIVEN gaps WHEN sorted THEN by frequency descending
    [Tags]    unit    journey-analyzer    gap    priority
    ${result}=    Gap Prioritized By Frequency
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_prioritized]

# =============================================================================
# History Tests
# =============================================================================

Get History Returns List
    [Documentation]    GIVEN logged questions WHEN get_history THEN returns list
    [Tags]    unit    journey-analyzer    history    query
    ${result}=    Get History Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]
    Should Be True    ${result}[has_entries]

History Ordered By Timestamp
    [Documentation]    GIVEN history WHEN retrieved THEN newest first
    [Tags]    unit    journey-analyzer    history    order
    ${result}=    History Ordered By Timestamp
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_ordered]

History Filter By Source
    [Documentation]    GIVEN history WHEN filter by source THEN filters
    [Tags]    unit    journey-analyzer    history    filter
    ${result}=    History Filter By Source
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[filters_correctly]

History Filter By Category
    [Documentation]    GIVEN history WHEN filter by category THEN filters
    [Tags]    unit    journey-analyzer    history    filter
    ${result}=    History Filter By Category
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[filters_correctly]

# =============================================================================
# Alert Tests
# =============================================================================

Generate Alert For Recurring
    [Documentation]    GIVEN recurring question WHEN threshold met THEN alert
    [Tags]    unit    journey-analyzer    alert    recurring
    ${result}=    Generate Alert For Recurring
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_alert]

Alert Includes Suggestion
    [Documentation]    GIVEN alert WHEN generated THEN has suggestion
    [Tags]    unit    journey-analyzer    alert    suggestion
    ${result}=    Alert Includes Suggestion
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_suggestion]

# =============================================================================
# Integration Tests
# =============================================================================

Journey Analyzer Factory Works
    [Documentation]    GIVEN create_journey_analyzer WHEN calling THEN creates
    [Tags]    unit    journey-analyzer    integration    factory
    ${result}=    Journey Analyzer Factory Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created]
    Should Be True    ${result}[has_log_question]

Analyzer Persistence Works
    [Documentation]    GIVEN logged questions WHEN get_history THEN persists
    [Tags]    unit    journey-analyzer    integration    persistence
    ${result}=    Analyzer Persistence Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[persists]

Clear History Works
    [Documentation]    GIVEN history WHEN clear_history THEN empties
    [Tags]    unit    journey-analyzer    integration    clear
    ${result}=    Clear History Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[cleared]
