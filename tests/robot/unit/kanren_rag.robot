*** Settings ***
Documentation    RF-004: Unit Tests - Kanren RAG Validation Constraints
...              Split from kanren_constraints.robot per DOC-SIZE-01-v1
...              Covers: RAG Chunk Validation, RAG Chunk Filtering, KAN-003 RAG Filter
Library          Collections
Library          ../../libs/KanrenRAGLibrary.py
Force Tags        unit    kanren    rag    low    read    TEST-BDD-01-v1

*** Test Cases ***
# =============================================================================
# RAG Chunk Validation Tests
# =============================================================================

Valid TypeDB Chunk
    [Documentation]    GIVEN typedb source WHEN valid_rag_chunk THEN valid
    [Tags]    unit    kanren    rag    typedb
    ${result}=    Valid TypeDB Chunk
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[valid]

Valid ChromaDB Chunk
    [Documentation]    GIVEN chromadb source WHEN valid_rag_chunk THEN valid
    [Tags]    unit    kanren    rag    chromadb
    ${result}=    Valid ChromaDB Chunk
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[has_result]
    Should Be True    ${result}[valid]

Invalid Source Fails
    [Documentation]    GIVEN external source WHEN valid_rag_chunk THEN no solutions
    [Tags]    unit    kanren    rag    invalid
    ${result}=    Invalid Source Fails
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[no_solutions]

Unverified Chunk Fails
    [Documentation]    GIVEN unverified chunk WHEN valid_rag_chunk THEN no solutions
    [Tags]    unit    kanren    rag    unverified
    ${result}=    Unverified Chunk Fails
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[no_solutions]

Invalid Type Fails
    [Documentation]    GIVEN unknown type WHEN valid_rag_chunk THEN no solutions
    [Tags]    unit    kanren    rag    type
    ${result}=    Invalid Type Fails
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[no_solutions]

# =============================================================================
# RAG Chunk Filtering Tests
# =============================================================================

Filter Mixed Chunks
    [Documentation]    GIVEN mixed chunks WHEN filter_rag_chunks THEN valid only
    [Tags]    unit    kanren    rag    filter
    ${result}=    Filter Mixed Chunks
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[correct_count]
    Should Be True    ${result}[all_valid_sources]

Filter Empty List
    [Documentation]    GIVEN empty list WHEN filter_rag_chunks THEN empty result
    [Tags]    unit    kanren    rag    filter    empty
    ${result}=    Filter Empty List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[empty_result]

Filter All Invalid
    [Documentation]    GIVEN all invalid chunks WHEN filter_rag_chunks THEN empty result
    [Tags]    unit    kanren    rag    filter    invalid
    ${result}=    Filter All Invalid
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[empty_result]

# =============================================================================
# KAN-003: RAG Filter Tests
# =============================================================================

Filter Import
    [Documentation]    KanrenRAGFilter can be imported
    [Tags]    unit    kanren    kan-003    import
    ${result}=    Filter Import
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[exists]

Filter Instantiation
    [Documentation]    KanrenRAGFilter can be instantiated
    [Tags]    unit    kanren    kan-003    instantiation
    ${result}=    Filter Instantiation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[created]
    Should Be True    ${result}[store_none]

Filter With Mock Store
    [Documentation]    KanrenRAGFilter works with injected mock store
    [Tags]    unit    kanren    kan-003    mock
    ${result}=    Filter With Mock Store
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[search_called]
    Should Be True    ${result}[one_result]
    Should Be True    ${result}[source_typedb]
    Should Be True    ${result}[type_rule]

Results To Chunks Conversion
    [Documentation]    _results_to_chunks correctly converts SimilarityResult format
    [Tags]    unit    kanren    kan-003    conversion
    ${result}=    Results To Chunks Conversion
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[chunk_count]
    Should Be True    ${result}[first_typedb]
    Should Be True    ${result}[second_typedb]
    Should Be True    ${result}[third_chromadb]

Search For Task Validation
    [Documentation]    search_for_task validates agent-task assignment
    [Tags]    unit    kanren    kan-003    task
    ${result}=    Search For Task Validation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[assignment_valid]
    Should Be True    ${result}[trust_level]
    Should Be True    ${result}[requires_evidence]
    Should Be True    ${result}[has_constraints]

Low Score Chunk Filtered
    [Documentation]    Chunks with low similarity score (< 0.5) are filtered
    [Tags]    unit    kanren    kan-003    score
    ${result}=    Low Score Chunk Filtered
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[filtered_out]

# =============================================================================
# Context Assembly Tests
# =============================================================================

Assemble Valid Context
    [Documentation]    assemble_context creates valid context with filtered chunks
    [Tags]    unit    kanren    context    assembly
    ${result}=    Assemble Valid Context
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    kanren not installed
    Should Be True    ${result}[assignment_valid]
    Should Be True    ${result}[trust_level]
    Should Be True    ${result}[requires_evidence]
    Should Be True    ${result}[one_chunk]
    Should Be True    ${result}[has_rule_007]
