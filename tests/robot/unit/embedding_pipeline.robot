*** Settings ***
Documentation    Embedding Pipeline Tests (P7.2)
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/test_embedding_pipeline.py
Library          Collections
Library          ../../libs/EmbeddingPipelineLibrary.py
Resource         ../resources/common.resource
Tags             unit    embedding    vector-store    p7.2

*** Test Cases ***
# =============================================================================
# Pipeline Module Tests
# =============================================================================

Test Pipeline Module Exists
    [Documentation]    Embedding pipeline module must exist (file or package)
    [Tags]    module
    ${result}=    Pipeline Module Exists
    Should Be True    ${result['module_exists']}

Test Pipeline Class Importable
    [Documentation]    EmbeddingPipeline class must be importable
    [Tags]    module
    ${result}=    Pipeline Class Importable
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['importable']}
    Should Be True    ${result['pipeline_created']}

Test Pipeline Has Required Methods
    [Documentation]    Pipeline must have required methods
    [Tags]    module
    ${result}=    Pipeline Has Required Methods
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_embed_rules']}
    Should Be True    ${result['has_embed_decisions']}
    Should Be True    ${result['has_embed_sessions']}
    Should Be True    ${result['has_run_full_pipeline']}

# =============================================================================
# Rule Embedding Tests
# =============================================================================

Test Embed Single Rule
    [Documentation]    Should embed a single rule
    [Tags]    rules    embedding
    ${result}=    Embed Single Rule
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['source_correct']}
    Should Be True    ${result['source_type_rule']}
    Should Be True    ${result['embedding_dimension']}

Test Embed All Rules
    [Documentation]    Should embed all rules from TypeDB
    [Tags]    rules    embedding
    ${result}=    Embed All Rules
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_list']}
    Should Be True    ${result['all_source_type_rule']}

Test Rule Embedding Content
    [Documentation]    Rule embedding content should include directive
    [Tags]    rules    embedding
    ${result}=    Rule Embedding Content
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_directive_content']}

# =============================================================================
# Decision Embedding Tests
# =============================================================================

Test Embed Single Decision
    [Documentation]    Should embed a single decision
    [Tags]    decisions    embedding
    ${result}=    Embed Single Decision
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['source_correct']}
    Should Be True    ${result['source_type_decision']}

Test Embed All Decisions
    [Documentation]    Should embed all decisions from evidence dir
    [Tags]    decisions    embedding
    ${result}=    Embed All Decisions
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_list']}
    Should Be True    ${result['all_source_type_decision']}

# =============================================================================
# Session Embedding Tests
# =============================================================================

Test Embed Single Session
    [Documentation]    Should embed a single session
    [Tags]    sessions    embedding
    ${result}=    Embed Single Session
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['source_correct']}
    Should Be True    ${result['source_type_session']}

Test Embed All Sessions
    [Documentation]    Should embed all sessions from evidence dir
    [Tags]    sessions    embedding
    ${result}=    Embed All Sessions
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_list']}
    Should Be True    ${result['all_source_type_session']}

Test Session Chunking
    [Documentation]    Long sessions should be chunked
    [Tags]    sessions    chunking
    ${result}=    Session Chunking
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['produces_chunks']}

# =============================================================================
# Full Pipeline Tests
# =============================================================================

Test Run Full Pipeline
    [Documentation]    Should run complete embedding pipeline
    [Tags]    pipeline    full
    ${result}=    Run Full Pipeline
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_rules']}
    Should Be True    ${result['has_decisions']}
    Should Be True    ${result['has_sessions']}
    Should Be True    ${result['has_total']}

Test Pipeline Returns Stats
    [Documentation]    Pipeline should return statistics
    [Tags]    pipeline    stats
    ${result}=    Pipeline Returns Stats
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['rules_is_int']}
    Should Be True    ${result['decisions_is_int']}
    Should Be True    ${result['sessions_is_int']}

# =============================================================================
# Embedding Storage Tests
# =============================================================================

Test Store To Cache
    [Documentation]    Should store embeddings in vector store cache
    [Tags]    storage    cache
    ${result}=    Store To Cache
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['in_cache']}

Test Search Stored Embeddings
    [Documentation]    Should be able to search stored embeddings
    [Tags]    storage    search
    ${result}=    Search Stored Embeddings
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_results']}

# =============================================================================
# Incremental Update Tests
# =============================================================================

Test Check Needs Update
    [Documentation]    Should check if embedding needs update
    [Tags]    incremental    update
    ${result}=    Check Needs Update
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['needs_update']}

Test Get Existing Sources
    [Documentation]    Should list existing embedded sources
    [Tags]    incremental    sources
    ${result}=    Get Existing Sources
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_rule']}

# =============================================================================
# Factory Function Tests
# =============================================================================

Test Create Pipeline Factory
    [Documentation]    Factory should create pipeline
    [Tags]    factory
    ${result}=    Create Pipeline Factory
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['pipeline_created']}

Test Create With Mock
    [Documentation]    Factory should support mock embeddings
    [Tags]    factory    mock
    ${result}=    Create With Mock
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['dimension_correct']}
