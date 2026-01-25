*** Settings ***
Documentation    RF-004: Unit Tests - SessionCollector
...              Migrated from tests/test_session_collector.py
...              Per P4.2: Session Collector
Library          Collections
Library          ../../libs/SessionCollectorLibrary.py

*** Test Cases ***
# =============================================================================
# SessionCollector Unit Tests
# =============================================================================

Session Collector Class Exists
    [Documentation]    GIVEN module WHEN import THEN SessionCollector exists
    [Tags]    unit    session    collector    class
    ${result}=    Session Collector Class Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

Session Collector Creates Session ID
    [Documentation]    GIVEN SessionCollector WHEN creating THEN has correct ID format
    [Tags]    unit    session    collector    id
    ${result}=    Session Collector Creates Session ID
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_session_prefix]
    Should Be True    ${result}[has_topic]

Session Collector Stores Topic
    [Documentation]    GIVEN SessionCollector WHEN creating THEN stores topic
    [Tags]    unit    session    collector    topic
    ${result}=    Session Collector Stores Topic
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[topic_correct]
    Should Be True    ${result}[type_correct]

Session Collector Has Empty Collections
    [Documentation]    GIVEN SessionCollector WHEN creating THEN collections empty
    [Tags]    unit    session    collector    init
    ${result}=    Session Collector Has Empty Collections
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[events_empty]
    Should Be True    ${result}[decisions_empty]
    Should Be True    ${result}[tasks_empty]

# =============================================================================
# Event Capture Tests
# =============================================================================

Capture Prompt Adds Event
    [Documentation]    GIVEN SessionCollector WHEN capture_prompt THEN event added
    [Tags]    unit    session    capture    prompt
    ${result}=    Capture Prompt Adds Event
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[event_added]
    Should Be True    ${result}[type_correct]
    Should Be True    ${result}[content_correct]

Capture Response Adds Event
    [Documentation]    GIVEN SessionCollector WHEN capture_response THEN event added
    [Tags]    unit    session    capture    response
    ${result}=    Capture Response Adds Event
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[event_added]
    Should Be True    ${result}[type_correct]

Capture Error Adds Event
    [Documentation]    GIVEN SessionCollector WHEN capture_error THEN event added
    [Tags]    unit    session    capture    error
    ${result}=    Capture Error Adds Event
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[event_added]
    Should Be True    ${result}[type_correct]
    Should Be True    ${result}[content_correct]

# =============================================================================
# Decision Capture Tests
# =============================================================================

Capture Decision Creates Decision
    [Documentation]    GIVEN SessionCollector WHEN capture_decision THEN Decision created
    [Tags]    unit    session    capture    decision
    ${result}=    Capture Decision Creates Decision
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[decision_added]

Capture Decision Adds Event
    [Documentation]    GIVEN SessionCollector WHEN capture_decision THEN event added
    [Tags]    unit    session    capture    decision    event
    ${result}=    Capture Decision Adds Event
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[event_added]
    Should Be True    ${result}[type_correct]
    Should Be True    ${result}[content_has_id]

# =============================================================================
# Task Capture Tests
# =============================================================================

Capture Task Creates Task
    [Documentation]    GIVEN SessionCollector WHEN capture_task THEN Task created
    [Tags]    unit    session    capture    task
    ${result}=    Capture Task Creates Task
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[status_correct]
    Should Be True    ${result}[priority_correct]
    Should Be True    ${result}[task_added]

Capture Task Adds Event
    [Documentation]    GIVEN SessionCollector WHEN capture_task THEN event added
    [Tags]    unit    session    capture    task    event
    ${result}=    Capture Task Adds Event
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[event_added]
    Should Be True    ${result}[type_correct]

# =============================================================================
# Session Log Generation Tests
# =============================================================================

Generate Session Log Creates File
    [Documentation]    GIVEN SessionCollector WHEN generate_session_log THEN file created
    [Tags]    unit    session    log    file
    ${result}=    Generate Session Log Creates File
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[file_exists]
    Should Be True    ${result}[is_markdown]

Generate Session Log Contains Header
    [Documentation]    GIVEN SessionCollector WHEN generate_session_log THEN has header
    [Tags]    unit    session    log    header
    ${result}=    Generate Session Log Contains Header
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_topic]
    Should Be True    ${result}[has_session_id]

Generate Session Log Contains Decisions
    [Documentation]    GIVEN SessionCollector WHEN generate_session_log THEN has decisions
    [Tags]    unit    session    log    decisions
    ${result}=    Generate Session Log Contains Decisions
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_decisions_section]
    Should Be True    ${result}[has_decision_id]
    Should Be True    ${result}[has_decision_name]

Generate Session Log Contains Thoughts
    [Documentation]    GIVEN SessionCollector WHEN generate_session_log THEN has thoughts
    [Tags]    unit    session    log    thoughts
    ${result}=    Generate Session Log Contains Thoughts
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_thoughts_section]
    Should Be True    ${result}[has_hypothesis]
    Should Be True    ${result}[has_reasoning]
    Should Be True    ${result}[has_confidence]

Generate Session Log Contains Tool Calls
    [Documentation]    GIVEN SessionCollector WHEN generate_session_log THEN has tool calls
    [Tags]    unit    session    log    tools
    ${result}=    Generate Session Log Contains Tool Calls
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_tool_calls_section]
    Should Be True    ${result}[has_tool_name]
    Should Be True    ${result}[has_duration]

Generate Session Log Contains Initial Prompt
    [Documentation]    GIVEN SessionCollector WHEN generate_session_log THEN has intent
    [Tags]    unit    session    log    intent
    ${result}=    Generate Session Log Contains Initial Prompt
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_intent_section]
    Should Be True    ${result}[has_initial_prompt]
    Should Be True    ${result}[has_prompt_content]

# =============================================================================
# Serialization Tests
# =============================================================================

To Dict Returns Dict
    [Documentation]    GIVEN SessionCollector WHEN to_dict THEN returns dict
    [Tags]    unit    session    serialize    dict
    ${result}=    To Dict Returns Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_session_id]
    Should Be True    ${result}[has_topic]
    Should Be True    ${result}[has_events_count]

To JSON Returns Valid JSON
    [Documentation]    GIVEN SessionCollector WHEN to_json THEN valid JSON
    [Tags]    unit    session    serialize    json
    ${result}=    To JSON Returns Valid JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[valid_json]
    Should Be True    ${result}[topic_correct]

# =============================================================================
# Session Registry Tests
# =============================================================================

Get Or Create Session Creates New
    [Documentation]    GIVEN get_or_create_session WHEN new topic THEN creates session
    [Tags]    unit    session    registry    create
    ${result}=    Get Or Create Session Creates New
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created]
    Should Be True    ${result}[has_topic]

Get Or Create Session Returns Existing
    [Documentation]    GIVEN get_or_create_session WHEN same topic THEN returns same
    [Tags]    unit    session    registry    singleton
    ${result}=    Get Or Create Session Returns Existing
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[same_instance]

List Active Sessions Returns IDs
    [Documentation]    GIVEN list_active_sessions WHEN called THEN returns IDs
    [Tags]    unit    session    registry    list
    ${result}=    List Active Sessions Returns IDs
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct_count]

End Session Removes And Generates Log
    [Documentation]    GIVEN end_session WHEN called THEN removes and generates log
    [Tags]    unit    session    registry    end
    ${result}=    End Session Removes And Generates Log
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[log_generated]
    Should Be True    ${result}[session_removed]

# =============================================================================
# MCP Session Tools Tests
# =============================================================================

Session Start Tool Exists
    [Documentation]    GIVEN MCP tools WHEN import THEN session_start exists
    [Tags]    unit    session    mcp    start
    ${result}=    Session Start Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[callable]

Session Start Returns JSON
    [Documentation]    GIVEN session_start WHEN called THEN returns valid JSON
    [Tags]    unit    session    mcp    start    json
    ${result}=    Session Start Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_session_id]
    Should Be True    ${result}[topic_correct]

Session Decision Tool Exists
    [Documentation]    GIVEN MCP tools WHEN import THEN session_decision exists
    [Tags]    unit    session    mcp    decision
    ${result}=    Session Decision Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[callable]

Session Task Tool Exists
    [Documentation]    GIVEN MCP tools WHEN import THEN session_task exists
    [Tags]    unit    session    mcp    task
    ${result}=    Session Task Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[callable]

Session End Tool Exists
    [Documentation]    GIVEN MCP tools WHEN import THEN session_end exists
    [Tags]    unit    session    mcp    end
    ${result}=    Session End Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[callable]

Session List Tool Exists
    [Documentation]    GIVEN MCP tools WHEN import THEN session_list exists
    [Tags]    unit    session    mcp    list
    ${result}=    Session List Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]
    Should Be True    ${result}[callable]

# =============================================================================
# Session Dataclasses Tests
# =============================================================================

Session Event Dataclass Works
    [Documentation]    GIVEN SessionEvent WHEN creating THEN fields correct
    [Tags]    unit    session    dataclass    event
    ${result}=    Session Event Dataclass Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[timestamp_correct]
    Should Be True    ${result}[type_correct]
    Should Be True    ${result}[metadata_correct]

Task Dataclass Works
    [Documentation]    GIVEN Task WHEN creating THEN fields correct
    [Tags]    unit    session    dataclass    task
    ${result}=    Task Dataclass Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[status_correct]
    Should Be True    ${result}[priority_correct]
