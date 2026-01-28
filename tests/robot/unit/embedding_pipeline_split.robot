*** Settings ***
Documentation    RF-004: Unit Tests - Embedding Pipeline Split Module
...              Migrated from tests/test_embedding_pipeline_split.py
...              Per DOC-SIZE-01-v1: Files under 400 lines
Library          Collections
Library          ../../libs/EmbeddingPipelineSplitLibrary.py
Force Tags        unit    embedding    split    low    validate    DOC-SIZE-01-v1

*** Test Cases ***
# =============================================================================
# Package Structure Tests
# =============================================================================

Embedding Pipeline Package Or File Exists
    [Documentation]    Either embedding_pipeline/ package or embedding_pipeline.py must exist
    [Tags]    unit    structure    embedding    pipeline
    ${result}=    Package Or File Exists
    Should Be True    ${result}[either_exists]    Embedding pipeline must exist

Chunking Module Exists In Package
    [Documentation]    Chunking module should exist in package
    [Tags]    unit    structure    embedding    chunking
    ${pkg}=    Package Or File Exists
    IF    ${pkg}[package_exists]
        ${exists}=    Chunking Module Exists
        Should Be True    ${exists}    chunking.py must exist in package
    ELSE
        Skip    Embedding pipeline is a file, not package
    END

Pipeline Module Exists In Package
    [Documentation]    Pipeline core module should exist in package
    [Tags]    unit    structure    embedding    pipeline
    ${pkg}=    Package Or File Exists
    IF    ${pkg}[package_exists]
        ${exists}=    Pipeline Module Exists
        Should Be True    ${exists}    pipeline.py must exist in package
    ELSE
        Skip    Embedding pipeline is a file, not package
    END

# =============================================================================
# Backward Compatibility Tests
# =============================================================================

Import EmbeddingPipeline Class
    [Documentation]    from governance.embedding_pipeline import EmbeddingPipeline must work
    [Tags]    unit    compatibility    embedding    import
    ${success}=    Import Embedding Pipeline Class
    Should Be True    ${success}    EmbeddingPipeline should be importable

Import Create Embedding Pipeline Function
    [Documentation]    from governance.embedding_pipeline import create_embedding_pipeline must work
    [Tags]    unit    compatibility    embedding    import
    ${success}=    Import Create Embedding Pipeline
    Should Be True    ${success}    create_embedding_pipeline should be importable

Create Pipeline Instance
    [Documentation]    Creating EmbeddingPipeline instance must work
    [Tags]    unit    compatibility    embedding    instance
    ${success}=    Create Pipeline Instance
    Should Be True    ${success}    Pipeline instance should be creatable

Pipeline Has Required Methods
    [Documentation]    Pipeline must have embed_rules, embed_sessions, embed_session_chunked
    [Tags]    unit    compatibility    embedding    methods
    ${result}=    Pipeline Has Methods
    Should Be True    ${result}[embed_rules]    Missing embed_rules method
    Should Be True    ${result}[embed_sessions]    Missing embed_sessions method
    Should Be True    ${result}[embed_session_chunked]    Missing embed_session_chunked method

# =============================================================================
# Chunking Module Tests
# =============================================================================

Import Chunk Content Function
    [Documentation]    chunk_content function should be importable
    [Tags]    unit    chunking    embedding    import
    ${result}=    Import Chunk Content
    Skip If    not ${result}[imported]    ${result.get("error", "chunking module not available")}
    Should Be True    ${result}[exists]    chunk_content should exist

Chunk Content Splits Long Text
    [Documentation]    chunk_content should split text exceeding chunk_size
    [Tags]    unit    chunking    embedding    split
    ${result}=    Test Chunk Content Splits Long
    Skip If    '${result.get("skip", False)}' == 'True'    ${result.get("reason", "skipped")}
    Should Be True    ${result}[multiple_chunks]    Should produce multiple chunks
    Should Be True    ${result}[all_under_limit]    All chunks should be under limit

Chunk Content Preserves Short Text
    [Documentation]    chunk_content should not split short text
    [Tags]    unit    chunking    embedding    preserve
    ${result}=    Test Chunk Content Preserves Short
    Skip If    '${result.get("skip", False)}' == 'True'    ${result.get("reason", "skipped")}
    Should Be True    ${result}[single_chunk]    Should produce single chunk
    Should Be True    ${result}[preserved]    Short text should be preserved

# =============================================================================
# File Size Compliance Tests
# =============================================================================

All Modules Under 400 Lines
    [Documentation]    All modules in package should be under 400 lines
    [Tags]    unit    structure    embedding    doc-size
    ${result}=    All Modules Under 400 Lines
    IF    '${result.get("is_package", True)}' == 'False'
        Skip If    ${result}[needs_refactoring]    Single file has ${result}[single_file_lines] lines - refactoring needed
    ELSE
        Should Be True    ${result}[all_under_limit]    Some files exceed 400 lines: ${result}[files]
    END

# =============================================================================
# Integration Tests
# =============================================================================

Embed Session Chunked Works
    [Documentation]    embed_session_chunked should work after refactoring
    [Tags]    unit    integration    embedding    chunked
    ${result}=    Test Embed Session Chunked
    Should Be True    ${result}[has_docs]    Should produce documents
    Should Be True    ${result}[correct_source]    Source should be TEST-SESSION
    Should Be True    ${result}[correct_type]    Type should be session

Run Full Pipeline Works
    [Documentation]    run_full_pipeline should work after refactoring
    [Tags]    unit    integration    embedding    full
    ${result}=    Test Run Full Pipeline
    Should Be True    ${result}[has_rules]    Result should have rules
    Should Be True    ${result}[has_decisions]    Result should have decisions
    Should Be True    ${result}[has_sessions]    Result should have sessions
    Should Be True    ${result}[has_total]    Result should have total
