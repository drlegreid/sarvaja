*** Settings ***
Documentation    RF-004: Unit Tests - Vector Store
...              Migrated from tests/test_vector_store.py
...              Per P7.1: VectorStore, embeddings, cosine similarity
Library          Collections
Library          ../../libs/VectorStoreLibrary.py

*** Test Cases ***
# =============================================================================
# Module Existence Tests
# =============================================================================

Module Exists
    [Documentation]    GIVEN governance WHEN check THEN vector_store.py exists
    [Tags]    unit    vector    module    exists
    ${result}=    Module Exists
    Should Be True    ${result}[exists]

Vector Document Dataclass
    [Documentation]    GIVEN VectorDocument WHEN create THEN has correct fields
    [Tags]    unit    vector    dataclass    document
    ${result}=    Vector Document Dataclass
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[source_type_correct]
    Should Be True    ${result}[embedding_len]

Similarity Result Dataclass
    [Documentation]    GIVEN SimilarityResult WHEN create THEN has correct fields
    [Tags]    unit    vector    dataclass    similarity
    ${result}=    Similarity Result Dataclass
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[score_correct]
    Should Be True    ${result}[source_correct]

Vector Store Class
    [Documentation]    GIVEN VectorStore WHEN instantiate THEN configurable
    [Tags]    unit    vector    class    store
    ${result}=    Vector Store Class
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[host_correct]
    Should Be True    ${result}[port_correct]

Vector Document Created At
    [Documentation]    GIVEN VectorDocument WHEN create THEN has timestamp
    [Tags]    unit    vector    dataclass    timestamp
    ${result}=    Vector Document Created At
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_created_at]
    Should Be True    ${result}[is_datetime]

# =============================================================================
# Embedding Generator Tests
# =============================================================================

Mock Embeddings Exists
    [Documentation]    GIVEN MockEmbeddings WHEN create THEN configurable
    [Tags]    unit    vector    embeddings    mock
    ${result}=    Mock Embeddings Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[dimension_correct]
    Should Be True    ${result}[model_name_correct]

Mock Embeddings Generate
    [Documentation]    GIVEN MockEmbeddings WHEN generate THEN deterministic
    [Tags]    unit    vector    embeddings    generate
    ${result}=    Mock Embeddings Generate
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[len_correct]
    Should Be True    ${result}[deterministic]

Mock Embeddings Different Texts
    [Documentation]    GIVEN different texts WHEN generate THEN different embeddings
    [Tags]    unit    vector    embeddings    different
    ${result}=    Mock Embeddings Different Texts
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[different]

Ollama Embeddings Class
    [Documentation]    GIVEN OllamaEmbeddings WHEN create THEN correct config
    [Tags]    unit    vector    embeddings    ollama
    ${result}=    Ollama Embeddings Class
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[host_correct]
    Should Be True    ${result}[dimension_correct]
    Should Be True    ${result}[has_ollama]

LiteLLM Embeddings Class
    [Documentation]    GIVEN LiteLLMEmbeddings WHEN create THEN correct config
    [Tags]    unit    vector    embeddings    litellm
    ${result}=    LiteLLM Embeddings Class
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[host_correct]
    Should Be True    ${result}[dimension_correct]
    Should Be True    ${result}[has_litellm]

# =============================================================================
# Cosine Similarity Tests
# =============================================================================

Cosine Similarity Identical
    [Documentation]    GIVEN identical vectors WHEN similarity THEN 1.0
    [Tags]    unit    vector    similarity    identical
    ${result}=    Cosine Similarity Identical
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_one]

Cosine Similarity Orthogonal
    [Documentation]    GIVEN orthogonal vectors WHEN similarity THEN 0.0
    [Tags]    unit    vector    similarity    orthogonal
    ${result}=    Cosine Similarity Orthogonal
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_zero]

Cosine Similarity Opposite
    [Documentation]    GIVEN opposite vectors WHEN similarity THEN -1.0
    [Tags]    unit    vector    similarity    opposite
    ${result}=    Cosine Similarity Opposite
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_neg_one]

Cosine Similarity Different Lengths
    [Documentation]    GIVEN different length vectors WHEN similarity THEN 0.0
    [Tags]    unit    vector    similarity    lengths
    ${result}=    Cosine Similarity Different Lengths
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_zero]

Cosine Similarity Zero Vector
    [Documentation]    GIVEN zero vector WHEN similarity THEN 0.0
    [Tags]    unit    vector    similarity    zero
    ${result}=    Cosine Similarity Zero Vector
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_zero]

# =============================================================================
# Vector Search Tests
# =============================================================================

Search With Cache
    [Documentation]    GIVEN cached docs WHEN search THEN returns ordered results
    [Tags]    unit    vector    search    cache
    ${result}=    Search With Cache
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_results]
    Should Be True    ${result}[ordered]

Search With Source Type Filter
    [Documentation]    GIVEN source_type filter WHEN search THEN filtered
    [Tags]    unit    vector    search    filter
    ${result}=    Search With Source Type Filter
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[all_rules]

Search By Source
    [Documentation]    GIVEN source ID WHEN search_by_source THEN finds doc
    [Tags]    unit    vector    search    source
    ${result}=    Search By Source
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[found]
    Should Be True    ${result}[not_found_none]

# =============================================================================
# Convenience Function Tests
# =============================================================================

Create Vector From Rule
    [Documentation]    GIVEN rule WHEN create_vector_from_rule THEN VectorDocument
    [Tags]    unit    vector    convenience    rule
    ${result}=    Create Vector From Rule
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[source_correct]
    Should Be True    ${result}[type_correct]
    Should Be True    ${result}[embedding_len]

Create Vector From Decision
    [Documentation]    GIVEN decision WHEN create_vector_from_decision THEN VectorDocument
    [Tags]    unit    vector    convenience    decision
    ${result}=    Create Vector From Decision
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[source_correct]
    Should Be True    ${result}[type_correct]

Create Vector From Session
    [Documentation]    GIVEN session WHEN create_vector_from_session THEN VectorDocument
    [Tags]    unit    vector    convenience    session
    ${result}=    Create Vector From Session
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[source_correct]
    Should Be True    ${result}[type_correct]

# =============================================================================
# TypeQL Generation Tests
# =============================================================================

TypeDB Insert Generation
    [Documentation]    GIVEN VectorDocument WHEN to_typedb_insert THEN valid TypeQL
    [Tags]    unit    vector    typeql    insert
    ${result}=    TypeDB Insert Generation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_insert]
    Should Be True    ${result}[has_id]
    Should Be True    ${result}[has_source]
    Should Be True    ${result}[has_type]
    Should Be True    ${result}[has_embedding]

TypeDB Insert Escaping
    [Documentation]    GIVEN special chars WHEN to_typedb_insert THEN escaped
    [Tags]    unit    vector    typeql    escaping
    ${result}=    TypeDB Insert Escaping
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[escaped_quotes]
    Should Be True    ${result}[escaped_newline]

# =============================================================================
# Schema Tests
# =============================================================================

Schema Has Vector Entities
    [Documentation]    GIVEN schema.tql WHEN check THEN has vector entities
    [Tags]    unit    vector    schema    entities
    ${result}=    Schema Has Vector Entities
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Schema not found
    Should Be True    ${result}[has_vector_document]
    Should Be True    ${result}[has_embedding]
    Should Be True    ${result}[has_similarity]
    Should Be True    ${result}[has_score]

Schema Has Vector Attributes
    [Documentation]    GIVEN schema.tql WHEN check THEN has vector attributes
    [Tags]    unit    vector    schema    attributes
    ${result}=    Schema Has Vector Attributes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Schema not found
    Should Be True    ${result}[has_id]
    Should Be True    ${result}[has_content]
    Should Be True    ${result}[has_model]
    Should Be True    ${result}[has_dimension]

Entities Can Have Embeddings
    [Documentation]    GIVEN schema WHEN check THEN entities play embedding role
    [Tags]    unit    vector    schema    role
    ${result}=    Entities Can Have Embeddings
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Schema not found
    Should Be True    ${result}[has_role]
