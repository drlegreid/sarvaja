*** Settings ***
Documentation    RF-004: Unit Tests - Workspace Scanner Split Module
...              Migrated from tests/test_workspace_scanner_split.py
...              Per DOC-SIZE-01-v1: Files under 400 lines
Library          Collections
Library          ../../libs/WorkspaceScannerSplitLibrary.py

*** Test Cases ***
# =============================================================================
# Module Structure Tests
# =============================================================================

Scanner Module Exists
    [Documentation]    Verify workspace_scanner.py exists
    [Tags]    unit    structure    workspace    scanner
    ${exists}=    Scanner Module Exists
    Should Be True    ${exists}    workspace_scanner.py must exist

Parsers Module Exists
    [Documentation]    Verify task_parsers.py extraction exists
    [Tags]    unit    structure    workspace    parsers
    ${exists}=    Parsers Module Exists
    Should Be True    ${exists}    task_parsers.py should be extracted

Scanner Module Under 400 Lines
    [Documentation]    Per DOC-SIZE-01-v1: workspace_scanner.py should be under 400 lines
    [Tags]    unit    structure    workspace    doc-size
    ${result}=    File Under Limit    workspace_scanner.py    400
    Should Be True    ${result}[under_limit]    workspace_scanner.py has ${result}[lines] lines, should be <400

# =============================================================================
# Backward Compatibility Tests
# =============================================================================

Import ParsedTask From Scanner
    [Documentation]    Verify ParsedTask can still be imported from workspace_scanner
    [Tags]    unit    compatibility    workspace    import
    ${success}=    Import Parsed Task
    Should Be True    ${success}    ParsedTask should be importable

Import Scan Workspace
    [Documentation]    Verify scan_workspace can still be imported
    [Tags]    unit    compatibility    workspace    import
    ${success}=    Import Scan Workspace
    Should Be True    ${success}    scan_workspace should be importable

Import Capture Workspace Tasks
    [Documentation]    Verify capture_workspace_tasks can still be imported
    [Tags]    unit    compatibility    workspace    import
    ${success}=    Import Capture Workspace Tasks
    Should Be True    ${success}    capture_workspace_tasks should be importable

# =============================================================================
# Parsers Module Tests
# =============================================================================

Import Normalize Status
    [Documentation]    Verify normalize_status is exported
    [Tags]    unit    parsers    workspace    import
    ${success}=    Import Normalize Status
    Should Be True    ${success}    normalize_status should be callable

Normalize Status Done Values
    [Documentation]    Test done status normalization
    [Tags]    unit    parsers    workspace    status
    ${result}=    Test Normalize Status Done
    Should Be True    ${result}[DONE_works]    DONE should normalize to DONE
    Should Be True    ${result}[checkmark_works]    Checkmark should normalize to DONE
    Should Be True    ${result}[checkmark_done_works]    Checkmark DONE should normalize to DONE

Normalize Status In Progress Values
    [Documentation]    Test in progress status normalization
    [Tags]    unit    parsers    workspace    status
    ${result}=    Test Normalize Status In Progress
    Should Be True    ${result}[IN_PROGRESS_works]    IN_PROGRESS should normalize to IN_PROGRESS
    Should Be True    ${result}[construction_works]    Construction emoji should normalize to IN_PROGRESS

Import Parse Markdown Table
    [Documentation]    Verify parse_markdown_table is exported
    [Tags]    unit    parsers    workspace    import
    ${success}=    Import Parse Markdown Table
    Should Be True    ${success}    parse_markdown_table should be callable

Parse Markdown Table Basic
    [Documentation]    Test basic table parsing
    [Tags]    unit    parsers    workspace    table
    ${result}=    Test Parse Markdown Table Basic
    Should Be True    ${result}[has_two_rows]    Should parse two rows
    Should Be True    ${result}[first_id_correct]    First row ID should be T1
    Should Be True    ${result}[first_name_correct]    First row name should be Test
    Should Be True    ${result}[second_id_correct]    Second row ID should be T2

Import Extract Functions
    [Documentation]    Verify extract functions are exported
    [Tags]    unit    parsers    workspace    extract
    ${result}=    Import Extract Functions
    Should Be True    ${result}[extract_task_id]    extract_task_id should be callable
    Should Be True    ${result}[extract_gap_id]    extract_gap_id should be callable
    Should Be True    ${result}[extract_linked_rules]    extract_linked_rules should be callable

# =============================================================================
# Integration Tests
# =============================================================================

Scanner Uses Parsers Module
    [Documentation]    Verify scanner uses the extracted parsers
    [Tags]    unit    integration    workspace    full
    ${result}=    Verify Integration
    Should Be True    ${result}[parse_todo_md]    parse_todo_md should be callable
    Should Be True    ${result}[normalize_status]    normalize_status should be callable
