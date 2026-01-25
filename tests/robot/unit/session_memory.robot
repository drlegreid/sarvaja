*** Settings ***
Documentation    RF-004: Unit Tests - Session Memory
...              Migrated from tests/test_session_memory.py
...              Per P11.4: Session memory integration
Library          Collections
Library          ../../libs/SessionMemoryLibrary.py

*** Test Cases ***
# =============================================================================
# SessionContext Tests
# =============================================================================

Session Context Creates With Defaults
    [Documentation]    GIVEN SessionContext WHEN init THEN defaults set
    [Tags]    unit    session-memory    context    defaults
    ${result}=    Session Context Creates With Defaults
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[session_id_correct]
    Should Be True    ${result}[project_correct]
    Should Be True    ${result}[date_correct]
    Should Be True    ${result}[tasks_empty]
    Should Be True    ${result}[gaps_empty]

Session Context To Document Basic
    [Documentation]    GIVEN context WHEN to_document THEN readable string
    [Tags]    unit    session-memory    context    document
    ${result}=    Session Context To Document Basic
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_session_id]
    Should Be True    ${result}[has_phase]
    Should Be True    ${result}[has_summary]

Session Context To Document With Tasks
    [Documentation]    GIVEN context with tasks WHEN to_document THEN includes tasks
    [Tags]    unit    session-memory    context    tasks
    ${result}=    Session Context To Document With Tasks
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_tasks]
    Should Be True    ${result}[has_gaps]

Session Context To Metadata
    [Documentation]    GIVEN context WHEN to_metadata THEN proper dict
    [Tags]    unit    session-memory    context    metadata
    ${result}=    Session Context To Metadata
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[project_correct]
    Should Be True    ${result}[session_id_correct]
    Should Be True    ${result}[phase_correct]
    Should Be True    ${result}[type_correct]
    Should Be True    ${result}[tasks_count_correct]
    Should Be True    ${result}[gaps_count_correct]

# =============================================================================
# SessionMemoryManager Tests
# =============================================================================

Manager Init Creates Context
    [Documentation]    GIVEN SessionMemoryManager WHEN init THEN has context
    [Tags]    unit    session-memory    manager    init
    ${result}=    Manager Init Creates Context
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_context]
    Should Be True    ${result}[project_correct]
    Should Be True    ${result}[session_id_starts_with]

Manager Set Phase
    [Documentation]    GIVEN manager WHEN set_phase THEN phase updated
    [Tags]    unit    session-memory    manager    phase
    ${result}=    Manager Set Phase
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[phase_set]

Manager Track Task Completed
    [Documentation]    GIVEN manager WHEN track_task THEN added to list
    [Tags]    unit    session-memory    manager    task
    ${result}=    Manager Track Task Completed
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_task_1]
    Should Be True    ${result}[has_task_2]

Manager Track Task No Duplicates
    [Documentation]    GIVEN duplicate tasks WHEN track THEN no duplicates
    [Tags]    unit    session-memory    manager    dedupe
    ${result}=    Manager Track Task No Duplicates
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[no_duplicates]

Manager Track Gap Resolved
    [Documentation]    GIVEN manager WHEN track_gap_resolved THEN added
    [Tags]    unit    session-memory    manager    gap
    ${result}=    Manager Track Gap Resolved
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[gap_tracked]

Manager Track Gap Discovered
    [Documentation]    GIVEN manager WHEN track_gap_discovered THEN added
    [Tags]    unit    session-memory    manager    gap
    ${result}=    Manager Track Gap Discovered
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[gap_tracked]

Manager Track Decision
    [Documentation]    GIVEN manager WHEN track_decision THEN added
    [Tags]    unit    session-memory    manager    decision
    ${result}=    Manager Track Decision
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[decision_tracked]

Manager Track File Modified
    [Documentation]    GIVEN manager WHEN track_file THEN added
    [Tags]    unit    session-memory    manager    file
    ${result}=    Manager Track File Modified
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[file_tracked]

Manager Set Test Results
    [Documentation]    GIVEN manager WHEN set_test_results THEN results set
    [Tags]    unit    session-memory    manager    tests
    ${result}=    Manager Set Test Results
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[passed_correct]
    Should Be True    ${result}[failed_correct]
    Should Be True    ${result}[skipped_correct]

Manager Set Summary
    [Documentation]    GIVEN manager WHEN set_summary THEN summary set
    [Tags]    unit    session-memory    manager    summary
    ${result}=    Manager Set Summary
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[summary_set]

Manager Add Next Step
    [Documentation]    GIVEN manager WHEN add_next_step THEN step added
    [Tags]    unit    session-memory    manager    steps
    ${result}=    Manager Add Next Step
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[step_added]

Manager Get Save Payload
    [Documentation]    GIVEN manager WHEN get_save_payload THEN valid payload
    [Tags]    unit    session-memory    manager    mcp
    ${result}=    Manager Get Save Payload
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_collection]
    Should Be True    ${result}[has_documents]
    Should Be True    ${result}[has_ids]
    Should Be True    ${result}[has_metadatas]
    Should Be True    ${result}[id_has_project]
    Should Be True    ${result}[doc_has_phase]

Manager Get Recovery Query
    [Documentation]    GIVEN manager WHEN get_recovery_query THEN valid query
    [Tags]    unit    session-memory    manager    mcp
    ${result}=    Manager Get Recovery Query
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_collection]
    Should Be True    ${result}[has_query_texts]
    Should Be True    ${result}[query_has_project]
    Should Be True    ${result}[n_results_correct]

Manager Parse Recovery Results Empty
    [Documentation]    GIVEN empty results WHEN parse THEN found false
    [Tags]    unit    session-memory    manager    recovery
    ${result}=    Manager Parse Recovery Results Empty
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[found_false]
    Should Be True    ${result}[sessions_empty]

Manager Parse Recovery Results With Data
    [Documentation]    GIVEN results WHEN parse THEN extracts context
    [Tags]    unit    session-memory    manager    recovery
    ${result}=    Manager Parse Recovery Results With Data
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[found_true]
    Should Be True    ${result}[has_sessions]
    Should Be True    ${result}[last_phase_correct]

Manager Generate Amnesia Report No Context
    [Documentation]    GIVEN no context WHEN generate_report THEN handles
    [Tags]    unit    session-memory    manager    amnesia
    ${result}=    Manager Generate Amnesia Report No Context
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_title]
    Should Be True    ${result}[has_no_context]
    Should Be True    ${result}[has_recovery]

Manager Generate Amnesia Report With Context
    [Documentation]    GIVEN context WHEN generate_report THEN shows recovered
    [Tags]    unit    session-memory    manager    amnesia
    ${result}=    Manager Generate Amnesia Report With Context
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_title]
    Should Be True    ${result}[has_found_sessions]
    Should Be True    ${result}[has_last_phase]

# =============================================================================
# DSP Integration Tests
# =============================================================================

Create DSP Session Context Basic
    [Documentation]    GIVEN DSP data WHEN create_dsp_context THEN creates
    [Tags]    unit    session-memory    dsp    create
    ${result}=    Create DSP Session Context Basic
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[session_id_correct]
    Should Be True    ${result}[phase_correct]
    Should Be True    ${result}[project_correct]

Create DSP Session Context With Findings
    [Documentation]    GIVEN findings WHEN create_dsp_context THEN extracts
    [Tags]    unit    session-memory    dsp    findings
    ${result}=    Create DSP Session Context With Findings
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_gap]
    Should Be True    ${result}[has_task]

Create DSP Session Context With Metrics
    [Documentation]    GIVEN metrics WHEN create_dsp_context THEN extracts
    [Tags]    unit    session-memory    dsp    metrics
    ${result}=    Create DSP Session Context With Metrics
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[gaps_correct]
    Should Be True    ${result}[passed_correct]
    Should Be True    ${result}[failed_correct]

Create DSP Session Context With Checkpoints
    [Documentation]    GIVEN checkpoints WHEN create_dsp_context THEN summary
    [Tags]    unit    session-memory    dsp    checkpoints
    ${result}=    Create DSP Session Context With Checkpoints
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_audit]
    Should Be True    ${result}[has_resolved]

# =============================================================================
# Global Manager Tests
# =============================================================================

Get Session Memory Singleton
    [Documentation]    GIVEN get_session_memory WHEN called THEN same instance
    [Tags]    unit    session-memory    global    singleton
    ${result}=    Get Session Memory Singleton
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_same]

Reset Session Memory Works
    [Documentation]    GIVEN reset_session_memory WHEN called THEN clears
    [Tags]    unit    session-memory    global    reset
    ${result}=    Reset Session Memory Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_different]

Manager To Dict Works
    [Documentation]    GIVEN manager WHEN to_dict THEN serializes
    [Tags]    unit    session-memory    global    serialize
    ${result}=    Manager To Dict Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[project_correct]
    Should Be True    ${result}[collection_correct]
    Should Be True    ${result}[phase_correct]
