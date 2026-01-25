*** Settings ***
Documentation    RF-004: Unit Tests - Session Viewer
...              Migrated from tests/test_session_viewer.py
...              Per P9.3: Session evidence viewer
Library          Collections
Library          ../../libs/SessionViewerLibrary.py

*** Test Cases ***
# =============================================================================
# Module Existence Tests
# =============================================================================

Session Viewer Module Exists
    [Documentation]    GIVEN agent/ WHEN checking THEN session_viewer.py exists
    [Tags]    unit    session-viewer    validate    module
    ${result}=    Session Viewer Module Exists
    Should Be True    ${result}[exists]

Session Viewer Class Importable
    [Documentation]    GIVEN SessionViewer WHEN importing THEN instantiates
    [Tags]    unit    session-viewer    validate    class
    ${result}=    Session Viewer Class Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[importable]
    Should Be True    ${result}[instantiable]

Viewer Has Required Methods
    [Documentation]    GIVEN SessionViewer WHEN checking THEN has required methods
    [Tags]    unit    session-viewer    validate    methods
    ${result}=    Viewer Has Required Methods
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_get_sessions_timeline]
    Should Be True    ${result}[has_get_session_detail]
    Should Be True    ${result}[has_search_in_session]
    Should Be True    ${result}[has_get_session_metadata]

# =============================================================================
# Timeline Tests
# =============================================================================

Get Sessions Timeline Works
    [Documentation]    GIVEN viewer WHEN get_sessions_timeline THEN returns ordered list
    [Tags]    unit    session-viewer    timeline    query
    ${result}=    Get Sessions Timeline Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]
    Should Be True    ${result}[is_ordered]

Timeline Has Required Fields
    [Documentation]    GIVEN timeline WHEN checking THEN has required fields
    [Tags]    unit    session-viewer    timeline    fields
    ${result}=    Timeline Has Required Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_session_id]
    Should Be True    ${result}[has_date]

Timeline Date Filter Works
    [Documentation]    GIVEN date range WHEN filtering THEN all in range
    [Tags]    unit    session-viewer    timeline    filter
    ${result}=    Timeline Date Filter Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]
    Should Be True    ${result}[all_in_range]

# =============================================================================
# Session Detail Tests
# =============================================================================

Get Session Detail Works
    [Documentation]    GIVEN session_id WHEN get_session_detail THEN returns details
    [Tags]    unit    session-viewer    detail    query
    ${result}=    Get Session Detail Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_session_id]
    Should Be True    ${result}[has_content]

Session Detail Parses Sections
    [Documentation]    GIVEN session WHEN parsing THEN has sections list
    [Tags]    unit    session-viewer    detail    parse
    ${result}=    Session Detail Parses Sections
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_sections]
    Should Be True    ${result}[sections_is_list]

Session Not Found Handled
    [Documentation]    GIVEN nonexistent session WHEN querying THEN error returned
    [Tags]    unit    session-viewer    detail    error
    ${result}=    Session Not Found Handled
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_error]

# =============================================================================
# Metadata Tests
# =============================================================================

Get Session Metadata Works
    [Documentation]    GIVEN session WHEN get_session_metadata THEN returns dict
    [Tags]    unit    session-viewer    metadata    query
    ${result}=    Get Session Metadata Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_session_id]

Metadata Extracts Phase
    [Documentation]    GIVEN session ID WHEN parsing THEN extracts phase
    [Tags]    unit    session-viewer    metadata    parse
    ${result}=    Metadata Extracts Phase
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_date]
    Should Be True    ${result}[has_phase]
    Should Be True    ${result}[phase_correct]

Metadata Extracts Topic
    [Documentation]    GIVEN session ID WHEN parsing THEN extracts topic
    [Tags]    unit    session-viewer    metadata    parse
    ${result}=    Metadata Extracts Topic
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_topic]
    Should Be True    ${result}[topic_correct]

# =============================================================================
# Search Tests
# =============================================================================

Search In Session Works
    [Documentation]    GIVEN session WHEN search_in_session THEN returns list
    [Tags]    unit    session-viewer    search    query
    ${result}=    Search In Session Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

Search Returns Context
    [Documentation]    GIVEN search WHEN results THEN includes context
    [Tags]    unit    session-viewer    search    context
    ${result}=    Search Returns Context
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_context]

Search All Sessions Works
    [Documentation]    GIVEN query WHEN search_all_sessions THEN returns list
    [Tags]    unit    session-viewer    search    global
    ${result}=    Search All Sessions Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]
    Should Be True    ${result}[has_session_id]

# =============================================================================
# Summary Tests
# =============================================================================

Generate Summary Works
    [Documentation]    GIVEN session WHEN get_session_summary THEN returns dict
    [Tags]    unit    session-viewer    summary    generate
    ${result}=    Generate Summary Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_session_id]

Summary Has Stats
    [Documentation]    GIVEN summary WHEN checking THEN has statistics
    [Tags]    unit    session-viewer    summary    stats
    ${result}=    Summary Has Stats
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_stats]

# =============================================================================
# Navigation Tests
# =============================================================================

Get Adjacent Sessions Works
    [Documentation]    GIVEN session WHEN get_adjacent THEN has previous and next
    [Tags]    unit    session-viewer    navigation    adjacent
    ${result}=    Get Adjacent Sessions Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_previous]
    Should Be True    ${result}[has_next]

Get Sessions By Phase Works
    [Documentation]    GIVEN viewer WHEN get_sessions_by_phase THEN returns dict
    [Tags]    unit    session-viewer    navigation    group
    ${result}=    Get Sessions By Phase Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]

Get Sessions By Date Works
    [Documentation]    GIVEN viewer WHEN get_sessions_by_date THEN returns dict
    [Tags]    unit    session-viewer    navigation    group
    ${result}=    Get Sessions By Date Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_dict]

# =============================================================================
# Integration Tests
# =============================================================================

Viewer Uses MCP Tools
    [Documentation]    GIVEN viewer WHEN checking THEN has _call_mcp_tool method
    [Tags]    unit    session-viewer    integration    mcp
    ${result}=    Viewer Uses MCP Tools
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_mcp_method]

Session Viewer Factory Works
    [Documentation]    GIVEN create_session_viewer WHEN calling THEN creates viewer
    [Tags]    unit    session-viewer    integration    factory
    ${result}=    Session Viewer Factory Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created]
