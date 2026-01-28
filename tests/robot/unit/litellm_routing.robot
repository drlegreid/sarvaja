*** Settings ***
Documentation    RF-004: Unit Tests - LiteLLM Model Routing
...              Migrated from tests/test_litellm_routing.py
...              Integration tests for LiteLLM routing
Library          Collections
Library          ../../libs/LiteLLMRoutingLibrary.py
Force Tags        unit    llm    routing    low    validate    ARCH-MCP-02-v1

*** Test Cases ***
# =============================================================================
# LiteLLM Model Routing Tests (Integration)
# =============================================================================

List Available Models
    [Documentation]    GIVEN LiteLLM WHEN list models THEN expected models present
    [Tags]    integration    litellm    models    slow
    ${result}=    List Available Models
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    LiteLLM not available
    Should Be True    ${result}[has_models]

Model Fallback Error
    [Documentation]    GIVEN invalid model WHEN completion THEN error returned
    [Tags]    integration    litellm    error
    ${result}=    Model Fallback Error
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    LiteLLM not available
    Should Be True    ${result}[error_code]
