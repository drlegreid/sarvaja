*** Settings ***
Documentation    RF-004: Unit Tests - Task CRUD Split Module
...              Migrated from tests/test_task_crud_split.py
...              Per DOC-SIZE-01-v1: Files under 300 lines
Library          Collections
Library          ../../libs/TaskCrudSplitLibrary.py

*** Test Cases ***
# =============================================================================
# Module Structure Tests
# =============================================================================

CRUD Module Exists
    [Documentation]    Verify crud.py exists in queries/tasks directory
    [Tags]    unit    structure    tasks    crud
    ${exists}=    Crud Module Exists
    Should Be True    ${exists}    crud.py must exist

CRUD Module Under 300 Lines
    [Documentation]    Per DOC-SIZE-01-v1: crud.py should be under 300 lines
    [Tags]    unit    structure    tasks    doc-size
    ${result}=    File Under Limit    crud.py    300
    Should Be True    ${result}[under_limit]    crud.py has ${result}[lines] lines, should be <300

Status Module Exists
    [Documentation]    Verify status.py extraction exists
    [Tags]    unit    structure    tasks    status
    ${exists}=    Status Module Exists
    Should Be True    ${exists}    status.py should be extracted

Status Module Under 300 Lines
    [Documentation]    Per DOC-SIZE-01-v1: status.py should be under 300 lines
    [Tags]    unit    structure    tasks    doc-size
    ${result}=    File Under Limit    status.py    300
    Should Be True    ${result}[under_limit]    status.py has ${result}[lines] lines, should be <300

# =============================================================================
# Backward Compatibility Tests
# =============================================================================

Import TaskCRUDOperations Class
    [Documentation]    Verify TaskCRUDOperations can still be imported
    [Tags]    unit    compatibility    tasks    import
    ${success}=    Import Task Crud Operations
    Should Be True    ${success}    TaskCRUDOperations should be importable

CRUD Has Insert Task Method
    [Documentation]    Verify crud still has insert_task method
    [Tags]    unit    compatibility    tasks    method
    ${has_method}=    Crud Has Method    insert_task
    Should Be True    ${has_method}    insert_task method should exist

CRUD Has Update Task Status Method
    [Documentation]    Verify crud still has update_task_status method
    [Tags]    unit    compatibility    tasks    method
    ${has_method}=    Crud Has Method    update_task_status
    Should Be True    ${has_method}    update_task_status method should exist

CRUD Has Delete Task Method
    [Documentation]    Verify crud still has delete_task method
    [Tags]    unit    compatibility    tasks    method
    ${has_method}=    Crud Has Method    delete_task
    Should Be True    ${has_method}    delete_task method should exist

# =============================================================================
# Status Module Tests
# =============================================================================

Status Module Has Update Function
    [Documentation]    Verify status.py has update_task_status function
    [Tags]    unit    status    tasks    function
    ${success}=    Import Status Update
    Should Be True    ${success}    update_task_status function should be callable

# =============================================================================
# Full Compatibility Check
# =============================================================================

Full Backward Compatibility
    [Documentation]    Verify all backward compatibility requirements
    [Tags]    unit    compatibility    tasks    full
    ${result}=    Verify Backward Compatibility
    Should Be True    ${result}[import_ok]    TaskCRUDOperations import failed
    Should Be True    ${result}[has_insert_task]    Missing insert_task method
    Should Be True    ${result}[has_update_task_status]    Missing update_task_status method
    Should Be True    ${result}[has_delete_task]    Missing delete_task method
    Should Be True    ${result}[status_import_ok]    Status update import failed
