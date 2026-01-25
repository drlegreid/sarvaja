*** Settings ***
Documentation    RF-004: Unit Tests - Task-Commit Linking
...              Migrated from tests/test_task_commit_link.py
...              Per GAP-TASK-LINK-002: Tasks linked to github commits
Library          Collections
Library          ../../libs/TaskCommitLinkLibrary.py

*** Test Cases ***
# =============================================================================
# Commit SHA Format Tests
# =============================================================================

Commit SHA Format Short
    [Documentation]    GIVEN short SHA WHEN validate THEN 7 chars hex
    [Tags]    unit    task    commit    format    short
    ${result}=    Commit SHA Format Short
    Should Be True    ${result}[length_correct]
    Should Be True    ${result}[format_valid]

Commit SHA Format Full
    [Documentation]    GIVEN full SHA WHEN validate THEN 40 chars hex
    [Tags]    unit    task    commit    format    full
    ${result}=    Commit SHA Format Full
    Should Be True    ${result}[length_correct]
    Should Be True    ${result}[format_valid]

Commit Reference Patterns
    [Documentation]    GIVEN various refs WHEN validate THEN all valid
    [Tags]    unit    task    commit    format    pattern
    ${result}=    Commit Reference Patterns
    Should Be True    ${result}[all_valid]

# =============================================================================
# Task Entity Tests
# =============================================================================

Task Has Linked Commits Field
    [Documentation]    GIVEN Task entity WHEN check THEN has linked_commits
    [Tags]    unit    task    commit    entity    field
    ${result}=    Task Has Linked Commits Field
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_field]

Task Linked Commits Is List
    [Documentation]    GIVEN Task.linked_commits WHEN check THEN is list type
    [Tags]    unit    task    commit    entity    type
    ${result}=    Task Linked Commits Is List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_list]

# =============================================================================
# TypeDB Schema Tests
# =============================================================================

Schema Has Commit SHA Attribute
    [Documentation]    GIVEN schema.tql WHEN check THEN has commit-sha
    [Tags]    unit    task    commit    schema    attribute
    ${result}=    Schema Has Commit SHA Attribute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Schema file not found
    Should Be True    ${result}[has_attribute]

Schema Has Commit Relation
    [Documentation]    GIVEN schema.tql WHEN check THEN has task-commit relation
    [Tags]    unit    task    commit    schema    relation
    ${result}=    Schema Has Commit Relation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Schema file not found
    Should Be True    ${result}[has_relation]

# =============================================================================
# Infrastructure Tests
# =============================================================================

Linking Module Has Commit Method
    [Documentation]    GIVEN TaskLinkingOperations WHEN check THEN has link_task_to_commit
    [Tags]    unit    task    commit    link    method
    ${result}=    Linking Module Has Commit Method
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_method]

Linking Module Has Get Commits Method
    [Documentation]    GIVEN TaskLinkingOperations WHEN check THEN has get_task_commits
    [Tags]    unit    task    commit    link    query
    ${result}=    Linking Module Has Get Commits Method
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_method]

# =============================================================================
# MCP Tool Tests
# =============================================================================

MCP Registration Includes Commit Tool
    [Documentation]    GIVEN tasks_linking WHEN register THEN has commit tool
    [Tags]    unit    task    commit    mcp    register
    ${result}=    MCP Registration Includes Commit Tool
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_commit_tool]

# =============================================================================
# Data Integrity Tests
# =============================================================================

Multiple Commits Per Task
    [Documentation]    GIVEN task WHEN linking THEN multiple commits allowed
    [Tags]    unit    task    commit    integrity    multiple
    ${result}=    Multiple Commits Per Task
    Should Be True    ${result}[allowed]

Commit To Multiple Tasks
    [Documentation]    GIVEN commit WHEN linking THEN multiple tasks allowed
    [Tags]    unit    task    commit    integrity    reverse
    ${result}=    Commit To Multiple Tasks
    Should Be True    ${result}[commit_valid]
    Should Be True    ${result}[multiple_tasks]

# =============================================================================
# BDD Scenario Tests
# =============================================================================

Scenario Developer Links Commit To Task
    [Documentation]    GIVEN completed task WHEN commit THEN linked
    [Tags]    unit    task    commit    bdd    link
    ${result}=    Scenario Developer Links Commit To Task
    Should Be True    ${result}[task_defined]
    Should Be True    ${result}[commit_defined]

Scenario Query Commits For Task
    [Documentation]    GIVEN task with commits WHEN query THEN returns all
    [Tags]    unit    task    commit    bdd    query
    ${result}=    Scenario Query Commits For Task
    Should Be True    ${result}[has_multiple]
