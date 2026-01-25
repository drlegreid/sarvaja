*** Settings ***
Documentation    RF-004: Integration Tests - Service Health Checks
...              Migrated from tests/test_health.py
...              Tests service availability and basic functionality
Library          Collections
Library          ../../libs/HealthLibrary.py

*** Test Cases ***
# =============================================================================
# LiteLLM Health Tests
# =============================================================================

LiteLLM Health Check
    [Documentation]    Test LiteLLM proxy is healthy
    [Tags]    integration    health    litellm
    ${result}=    Check Litellm Health
    Skip If    '${result}[status]' == 'skip'    ${result}[reason]
    Should Be Equal    ${result}[status]    ok    LiteLLM health check failed

LiteLLM Models Available
    [Documentation]    Test LiteLLM has models configured
    [Tags]    integration    health    litellm    models
    ${result}=    Check Litellm Models
    Skip If    '${result}[status]' == 'skip'    ${result}[reason]
    Should Be Equal    ${result}[status]    ok    LiteLLM models check failed

# =============================================================================
# ChromaDB Health Tests
# =============================================================================

ChromaDB Health Check
    [Documentation]    Test ChromaDB is healthy
    [Tags]    integration    health    chromadb
    ${result}=    Check Chromadb Health
    Skip If    '${result}[status]' == 'skip'    ${result}[reason]
    Should Be Equal    ${result}[status]    ok    ChromaDB health check failed

ChromaDB Collections Endpoint
    [Documentation]    Test ChromaDB collections endpoint
    [Tags]    integration    health    chromadb    collections
    ${result}=    Check Chromadb Collections
    Skip If    '${result}[status]' == 'skip'    ${result}[reason]
    Should Be Equal    ${result}[status]    ok    ChromaDB collections check failed

# =============================================================================
# Ollama Health Tests
# =============================================================================

Ollama Health Check
    [Documentation]    Test Ollama is healthy
    [Tags]    integration    health    ollama
    ${result}=    Check Ollama Health
    Skip If    '${result}[status]' == 'skip'    ${result}[reason]
    Should Be Equal    ${result}[status]    ok    Ollama health check failed

# =============================================================================
# Agents API Health Tests
# =============================================================================

Agents API Health Check
    [Documentation]    Test Agents API is healthy
    [Tags]    integration    health    agents
    ${result}=    Check Agents Health
    Skip If    '${result}[status]' == 'skip'    ${result}[reason]
    Should Be Equal    ${result}[status]    ok    Agents API health check failed

# =============================================================================
# TypeDB Health Tests
# =============================================================================

TypeDB Health Check
    [Documentation]    Test TypeDB is healthy (DECISION-003)
    [Tags]    integration    health    typedb
    ${result}=    Check Typedb Health
    Skip If    '${result}[status]' == 'skip'    ${result}[reason]
    Should Be Equal    ${result}[status]    ok    TypeDB health check failed

# =============================================================================
# All Services Summary
# =============================================================================

All Services Summary
    [Documentation]    Summary of all service health checks
    [Tags]    integration    health    summary
    ${result}=    Check All Services
    Log    LiteLLM: ${result}[litellm]
    Log    ChromaDB: ${result}[chromadb]
    Log    Ollama: ${result}[ollama]
    Log    Agents: ${result}[agents]
    Log    TypeDB: ${result}[typedb]
