*** Settings ***
Documentation    RF-004: Unit Tests - Routes Chat Split Module
...              Migrated from tests/test_routes_chat_split.py
...              Per DOC-SIZE-01-v1: Files under 400 lines
Library          Collections
Library          ../../libs/RoutesChatSplitLibrary.py

*** Test Cases ***
# =============================================================================
# Package Structure Tests
# =============================================================================

Chat Routes Package Or Module Exists
    [Documentation]    Either routes/chat/ package or routes/chat.py must exist
    [Tags]    unit    structure    chat    routes
    ${result}=    Chat Package Or Module Exists
    Should Be True    ${result}[either_exists]    Chat routes must exist as package or module

Commands Module Exists In Package
    [Documentation]    Commands module should exist in chat package
    [Tags]    unit    structure    chat    commands
    ${pkg}=    Chat Package Or Module Exists
    IF    ${pkg}[package_exists]
        ${exists}=    Commands Module Exists
        Should Be True    ${exists}    commands.py must exist in package
    ELSE
        Skip    Chat is a module, not package
    END

# =============================================================================
# Backward Compatibility Tests
# =============================================================================

Import Router From Chat Routes
    [Documentation]    from governance.routes.chat import router must work
    [Tags]    unit    compatibility    chat    import
    ${success}=    Import Router
    Should Be True    ${success}    Router should be importable

Router Has Registered Routes
    [Documentation]    Router should have registered routes
    [Tags]    unit    compatibility    chat    routes
    ${result}=    Router Has Routes
    Should Be True    ${result}[has_routes]    Router should have chat routes

# =============================================================================
# Commands Module Tests
# =============================================================================

Process Chat Command Importable
    [Documentation]    process_chat_command function should be importable
    [Tags]    unit    commands    chat    import
    ${success}=    Import Process Chat Command
    Should Be True    ${success}    process_chat_command should be importable

Process Chat Command Status
    [Documentation]    process_chat_command should handle /status
    [Tags]    unit    commands    chat    status
    ${result}=    Test Command Status
    Should Be True    ${result}[has_status]    /status should return status info

Process Chat Command Help
    [Documentation]    process_chat_command should handle /help
    [Tags]    unit    commands    chat    help
    ${result}=    Test Command Help
    Should Be True    ${result}[has_help]    /help should return help info

Process Chat Command Unknown
    [Documentation]    process_chat_command should handle unknown commands
    [Tags]    unit    commands    chat    unknown
    ${result}=    Test Command Unknown
    Should Be True    ${result}[has_response]    Unknown command should get response

# =============================================================================
# File Size Compliance Tests
# =============================================================================

All Modules Under 400 Lines
    [Documentation]    All modules in package should be under 400 lines
    [Tags]    unit    structure    chat    doc-size
    ${result}=    Check Modules Under 400 Lines
    Should Be True    ${result}[all_under_limit]    All files should be under 400 lines

# =============================================================================
# Integration Tests
# =============================================================================

Router Is FastAPI APIRouter
    [Documentation]    Router should be FastAPI APIRouter
    [Tags]    unit    integration    chat    fastapi
    ${is_api_router}=    Router Is Api Router
    Should Be True    ${is_api_router}    Router should be APIRouter instance

Router Has POST Send Route
    [Documentation]    Router should have POST /chat/send route
    [Tags]    unit    integration    chat    send
    ${has_route}=    Router Has Post Send
    Should Be True    ${has_route}    Should have POST /chat/send route

Router Has GET Sessions Route
    [Documentation]    Router should have GET /chat/sessions route
    [Tags]    unit    integration    chat    sessions
    ${has_route}=    Router Has Get Sessions
    Should Be True    ${has_route}    Should have GET /chat/sessions route
