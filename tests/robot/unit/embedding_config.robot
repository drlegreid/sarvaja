*** Settings ***
Documentation    RF-004: Unit Tests - Embedding Configuration
...              Migrated from tests/test_embedding_config.py
...              Per GAP-EMBED-001: Embedding Configuration
Library          Collections
Library          ../../libs/EmbeddingConfigLibrary.py
Force Tags        unit    embedding    config    low    validate    ARCH-INFRA-01-v1

*** Test Cases ***
# =============================================================================
# Environment Variable Defaults Tests
# =============================================================================

Get Use Mock Defaults To False
    [Documentation]    GIVEN no env var WHEN get_use_mock THEN False
    [Tags]    unit    embedding    config    default
    ${result}=    Get Use Mock Defaults To False
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[default_false]

Get Use Mock True When Set
    [Documentation]    GIVEN USE_MOCK_EMBEDDINGS=true WHEN get_use_mock THEN True
    [Tags]    unit    embedding    config    mock
    ${result}=    Get Use Mock True When Set
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_true]

Get Use Mock False When False
    [Documentation]    GIVEN USE_MOCK_EMBEDDINGS=false WHEN get_use_mock THEN False
    [Tags]    unit    embedding    config    mock
    ${result}=    Get Use Mock False When False
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_false]

Get Embedding Provider Defaults To Ollama
    [Documentation]    GIVEN no env var WHEN get_embedding_provider THEN ollama
    [Tags]    unit    embedding    config    provider
    ${result}=    Get Embedding Provider Defaults To Ollama
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_ollama]

Get Embedding Provider Litellm
    [Documentation]    GIVEN EMBEDDING_PROVIDER=litellm WHEN get_embedding_provider THEN litellm
    [Tags]    unit    embedding    config    litellm
    ${result}=    Get Embedding Provider Litellm
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_litellm]

Get Embedding Provider Mock
    [Documentation]    GIVEN EMBEDDING_PROVIDER=mock WHEN get_embedding_provider THEN mock
    [Tags]    unit    embedding    config    mock
    ${result}=    Get Embedding Provider Mock
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_mock]

Invalid Provider Defaults To Ollama
    [Documentation]    GIVEN invalid provider WHEN get_embedding_provider THEN ollama
    [Tags]    unit    embedding    config    fallback
    ${result}=    Invalid Provider Defaults To Ollama
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_ollama]

# =============================================================================
# Embedding Generator Factory Tests
# =============================================================================

Create Mock When Use Mock True
    [Documentation]    GIVEN use_mock=True WHEN create_embedding_generator THEN MockEmbeddings
    [Tags]    unit    embedding    factory    mock
    ${result}=    Create Mock When Use Mock True
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_mock]

Create Ollama When Provider Ollama
    [Documentation]    GIVEN ollama provider WHEN create_embedding_generator THEN OllamaEmbeddings
    [Tags]    unit    embedding    factory    ollama
    ${result}=    Create Ollama When Provider Ollama
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_ollama]

Create Litellm When Provider Litellm
    [Documentation]    GIVEN litellm provider WHEN create_embedding_generator THEN LiteLLMEmbeddings
    [Tags]    unit    embedding    factory    litellm
    ${result}=    Create Litellm When Provider Litellm
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_litellm]

Use Mock Overrides Provider
    [Documentation]    GIVEN use_mock=True WHEN provider=ollama THEN MockEmbeddings
    [Tags]    unit    embedding    factory    override
    ${result}=    Use Mock Overrides Provider
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_mock]

Mock Uses Dimension Parameter
    [Documentation]    GIVEN dimension=768 WHEN create mock THEN dimension is 768
    [Tags]    unit    embedding    factory    dimension
    ${result}=    Mock Uses Dimension Parameter
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[dimension_768]

Default Dimension Is 384
    [Documentation]    GIVEN no dimension WHEN create mock THEN dimension is 384
    [Tags]    unit    embedding    factory    default
    ${result}=    Default Dimension Is 384
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[dimension_384]

# =============================================================================
# Host/Port Configuration Tests
# =============================================================================

Get Ollama Config Defaults
    [Documentation]    GIVEN no env vars WHEN get_ollama_config THEN localhost:11434
    [Tags]    unit    embedding    config    ollama
    ${result}=    Get Ollama Config Defaults
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[host_localhost]
    Should Be True    ${result}[port_11434]

Get Ollama Config From Env
    [Documentation]    GIVEN env vars WHEN get_ollama_config THEN custom config
    [Tags]    unit    embedding    config    ollama    env
    ${result}=    Get Ollama Config From Env
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[host_correct]
    Should Be True    ${result}[port_correct]

Get Litellm Config Defaults
    [Documentation]    GIVEN no env vars WHEN get_litellm_config THEN localhost:4000
    [Tags]    unit    embedding    config    litellm
    ${result}=    Get Litellm Config Defaults
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[host_localhost]
    Should Be True    ${result}[port_4000]

Get Litellm Config From Env
    [Documentation]    GIVEN env vars WHEN get_litellm_config THEN custom config
    [Tags]    unit    embedding    config    litellm    env
    ${result}=    Get Litellm Config From Env
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[host_correct]
    Should Be True    ${result}[port_correct]

# =============================================================================
# Config Summary Tests
# =============================================================================

Get Embedding Config Summary Returns Dict
    [Documentation]    GIVEN summary function WHEN called THEN returns dict
    [Tags]    unit    embedding    summary    dict
    ${result}=    Get Embedding Config Summary Returns Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]

Config Summary Has Required Keys
    [Documentation]    GIVEN summary WHEN check THEN has all required keys
    [Tags]    unit    embedding    summary    keys
    ${result}=    Config Summary Has Required Keys
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_use_mock]
    Should Be True    ${result}[has_provider]
    Should Be True    ${result}[has_ollama_config]
    Should Be True    ${result}[has_litellm_config]
    Should Be True    ${result}[has_env_vars]

# =============================================================================
# Pipeline Integration Tests
# =============================================================================

Pipeline Uses Env Config By Default
    [Documentation]    GIVEN EmbeddingPipeline WHEN mock env THEN uses mock
    [Tags]    unit    embedding    pipeline    env
    ${result}=    Pipeline Uses Env Config By Default
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_mock]

Create Embedding Pipeline Uses Env Config
    [Documentation]    GIVEN create_embedding_pipeline WHEN mock env THEN uses mock
    [Tags]    unit    embedding    pipeline    create
    ${result}=    Create Embedding Pipeline Uses Env Config
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_mock]

Create Embedding Pipeline Override Works
    [Documentation]    GIVEN use_mock=True WHEN false env THEN override works
    [Tags]    unit    embedding    pipeline    override
    ${result}=    Create Embedding Pipeline Override Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_mock]

# =============================================================================
# Production Safety Tests
# =============================================================================

No Env Vars Means Real Embeddings
    [Documentation]    GIVEN no env vars WHEN create THEN OllamaEmbeddings
    [Tags]    unit    embedding    production    safety
    ${result}=    No Env Vars Means Real Embeddings
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_ollama]

Pipeline Default Not Mock
    [Documentation]    GIVEN production env WHEN create pipeline THEN not mock
    [Tags]    unit    embedding    production    pipeline
    ${result}=    Pipeline Default Not Mock
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_ollama]
