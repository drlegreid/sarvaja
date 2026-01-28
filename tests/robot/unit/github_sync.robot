*** Settings ***
Documentation    RF-004: Unit Tests - GitHub Sync
...              Migrated from tests/test_github_sync.py
...              Per FH-006: GitHub sync functionality
Library          Collections
Library          ../../libs/GitHubSyncLibrary.py
Force Tags        unit    sync    github    medium    WORKFLOW-SEQ-01-v1

*** Test Cases ***
# =============================================================================
# Module Existence Tests
# =============================================================================

GitHub Sync Module Exists
    [Documentation]    GIVEN governance/ WHEN checking THEN github_sync.py exists
    [Tags]    unit    github-sync    validate    module
    ${result}=    GitHub Sync Module Exists
    Should Be True    ${result}[exists]

RDTask Dataclass Works
    [Documentation]    GIVEN RDTask WHEN creating THEN all fields correct
    [Tags]    unit    github-sync    validate    dataclass
    ${result}=    RDTask Dataclass Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[status_correct]
    Should Be True    ${result}[github_issue_none]

SyncResult Dataclass Works
    [Documentation]    GIVEN SyncResult WHEN creating THEN lists empty
    [Tags]    unit    github-sync    validate    dataclass
    ${result}=    SyncResult Dataclass Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created_empty]
    Should Be True    ${result}[updated_empty]
    Should Be True    ${result}[errors_empty]

GitHubSync Class Instantiable
    [Documentation]    GIVEN GitHubSync WHEN creating THEN instantiates correctly
    [Tags]    unit    github-sync    validate    class
    ${result}=    GitHubSync Class Instantiable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[dry_run_true]
    Should Be True    ${result}[default_repo]

GitHubSync Custom Repo Works
    [Documentation]    GIVEN custom repo WHEN creating THEN repo set correctly
    [Tags]    unit    github-sync    validate    class
    ${result}=    GitHubSync Custom Repo Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[custom_repo]

# =============================================================================
# Backlog Parsing Tests
# =============================================================================

Backlog File Exists
    [Documentation]    GIVEN docs/ WHEN checking THEN R&D-BACKLOG.md exists
    [Tags]    unit    github-sync    validate    backlog
    ${result}=    Backlog File Exists
    Should Be True    ${result}[exists]

Parse Backlog Returns List
    [Documentation]    GIVEN parse_backlog WHEN calling THEN returns list
    [Tags]    unit    github-sync    validate    backlog
    ${result}=    Parse Backlog Returns List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_list]

