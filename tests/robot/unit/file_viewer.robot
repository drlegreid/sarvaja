*** Settings ***
Documentation    RF-004: Unit Tests - File Viewer
...              Migrated from tests/test_file_viewer.py
...              Per GAP-DATA-003: File viewer functionality
Library          Collections
Library          ../../libs/FileViewerLibrary.py
Force Tags        unit    ui    files    low    read    UI-DESIGN-02-v1

*** Test Cases ***
# =============================================================================
# State Transform Tests
# =============================================================================

Initial State Has File Viewer Fields
    [Documentation]    GIVEN initial state WHEN checking THEN has file viewer fields
    [Tags]    unit    file-viewer    state    initial
    ${result}=    Initial State Has File Viewer Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_show]
    Should Be True    ${result}[has_path]
    Should Be True    ${result}[has_content]
    Should Be True    ${result}[has_loading]
    Should Be True    ${result}[has_error]
    Should Be True    ${result}[show_false]
    Should Be True    ${result}[path_empty]
    Should Be True    ${result}[content_empty]
    Should Be True    ${result}[loading_false]
    Should Be True    ${result}[error_empty]

With File Viewer Sets State
    [Documentation]    GIVEN with_file_viewer WHEN called THEN sets state
    [Tags]    unit    file-viewer    state    transform
    ${result}=    With File Viewer Sets State
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[show_true]
    Should Be True    ${result}[path_correct]
    Should Be True    ${result}[content_correct]
    Should Be True    ${result}[original_unchanged]

With File Viewer Loading Sets State
    [Documentation]    GIVEN with_file_viewer_loading WHEN called THEN loading state
    [Tags]    unit    file-viewer    state    loading
    ${result}=    With File Viewer Loading Sets State
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[show_true]
    Should Be True    ${result}[path_correct]
    Should Be True    ${result}[loading_true]
    Should Be True    ${result}[content_empty]
    Should Be True    ${result}[error_empty]

With File Viewer Content Sets Content
    [Documentation]    GIVEN with_file_viewer_content WHEN called THEN content set
    [Tags]    unit    file-viewer    state    content
    ${result}=    With File Viewer Content Sets Content
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[loading_false]
    Should Be True    ${result}[content_correct]
    Should Be True    ${result}[error_empty]

With File Viewer Error Sets Error
    [Documentation]    GIVEN with_file_viewer_error WHEN called THEN error set
    [Tags]    unit    file-viewer    state    error
    ${result}=    With File Viewer Error Sets Error
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[loading_false]
    Should Be True    ${result}[content_empty]
    Should Be True    ${result}[error_correct]

Close File Viewer Resets State
    [Documentation]    GIVEN close_file_viewer WHEN called THEN all state reset
    [Tags]    unit    file-viewer    state    close
    ${result}=    Close File Viewer Resets State
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[show_false]
    Should Be True    ${result}[path_empty]
    Should Be True    ${result}[content_empty]
    Should Be True    ${result}[loading_false]
    Should Be True    ${result}[error_empty]

# =============================================================================
# Response Model Tests
# =============================================================================

File Content Response Model Has Fields
    [Documentation]    GIVEN FileContentResponse WHEN checking THEN has fields
    [Tags]    unit    file-viewer    api    model
    ${result}=    File Content Response Model Has Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_path]
    Should Be True    ${result}[has_content]
    Should Be True    ${result}[has_size]
    Should Be True    ${result}[has_modified_at]
    Should Be True    ${result}[has_exists]
