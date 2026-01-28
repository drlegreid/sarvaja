*** Settings ***
Documentation    RF-004: Session Memory Extended Tests (Context, Integration, Manager)
...              Migrated from governance/session_memory.py
...              Per RF-007 Robot Framework Migration
Library          ../../libs/SessionMemoryContextLibrary.py
Library          ../../libs/SessionMemoryIntegrationLibrary.py
Library          ../../libs/SessionMemoryManagerLibrary.py
Library          Collections
Resource         ../resources/common.resource
Force Tags             unit    sessions    memory    extended    low    session    read    CONTEXT-SAVE-01-v1

*** Test Cases ***
# =============================================================================
# Context Tests
# =============================================================================

Session Context Creates With Defaults
    [Documentation]    Test: Session Context Creates With Defaults
    ${result}=    Session Context Creates With Defaults
    Skip If Import Failed    ${result}

Session Context To Document Basic
    [Documentation]    Test: Session Context To Document Basic
    ${result}=    Session Context To Document Basic
    Skip If Import Failed    ${result}

Session Context To Document With Tasks
    [Documentation]    Test: Session Context To Document With Tasks
    ${result}=    Session Context To Document With Tasks
    Skip If Import Failed    ${result}

Session Context To Metadata
    [Documentation]    Test: Session Context To Metadata
    ${result}=    Session Context To Metadata
    Skip If Import Failed    ${result}

# =============================================================================
# Integration Tests
# =============================================================================

Create DSP Session Context Basic
    [Documentation]    Test: Create DSP Session Context Basic
    ${result}=    Create DSP Session Context Basic
    Skip If Import Failed    ${result}

Create DSP Session Context With Findings
    [Documentation]    Test: Create DSP Session Context With Findings
    ${result}=    Create DSP Session Context With Findings
    Skip If Import Failed    ${result}

Create DSP Session Context With Metrics
    [Documentation]    Test: Create DSP Session Context With Metrics
    ${result}=    Create DSP Session Context With Metrics
    Skip If Import Failed    ${result}

Create DSP Session Context With Checkpoints
    [Documentation]    Test: Create DSP Session Context With Checkpoints
    ${result}=    Create DSP Session Context With Checkpoints
    Skip If Import Failed    ${result}

Get Session Memory Singleton
    [Documentation]    Test: Get Session Memory Singleton
    ${result}=    Get Session Memory Singleton
    Skip If Import Failed    ${result}

Reset Session Memory Works
    [Documentation]    Test: Reset Session Memory Works
    ${result}=    Reset Session Memory Works
    Skip If Import Failed    ${result}

Manager To Dict Works
    [Documentation]    Test: Manager To Dict Works
    ${result}=    Manager To Dict Works
    Skip If Import Failed    ${result}

# =============================================================================
# Manager Tests
# =============================================================================

Manager Init Creates Context
    [Documentation]    Test: Manager Init Creates Context
    ${result}=    Manager Init Creates Context
    Skip If Import Failed    ${result}

Manager Set Phase
    [Documentation]    Test: Manager Set Phase
    ${result}=    Manager Set Phase
    Skip If Import Failed    ${result}

Manager Track Task Completed
    [Documentation]    Test: Manager Track Task Completed
    ${result}=    Manager Track Task Completed
    Skip If Import Failed    ${result}

Manager Track Task No Duplicates
    [Documentation]    Test: Manager Track Task No Duplicates
    ${result}=    Manager Track Task No Duplicates
    Skip If Import Failed    ${result}

Manager Track Gap Resolved
    [Documentation]    Test: Manager Track Gap Resolved
    ${result}=    Manager Track Gap Resolved
    Skip If Import Failed    ${result}

Manager Track Gap Discovered
    [Documentation]    Test: Manager Track Gap Discovered
    ${result}=    Manager Track Gap Discovered
    Skip If Import Failed    ${result}

Manager Track Decision
    [Documentation]    Test: Manager Track Decision
    ${result}=    Manager Track Decision
    Skip If Import Failed    ${result}

Manager Track File Modified
    [Documentation]    Test: Manager Track File Modified
    ${result}=    Manager Track File Modified
    Skip If Import Failed    ${result}

Manager Set Test Results
    [Documentation]    Test: Manager Set Test Results
    ${result}=    Manager Set Test Results
    Skip If Import Failed    ${result}

Manager Set Summary
    [Documentation]    Test: Manager Set Summary
    ${result}=    Manager Set Summary
    Skip If Import Failed    ${result}

Manager Add Next Step
    [Documentation]    Test: Manager Add Next Step
    ${result}=    Manager Add Next Step
    Skip If Import Failed    ${result}

Manager Get Save Payload
    [Documentation]    Test: Manager Get Save Payload
    ${result}=    Manager Get Save Payload
    Skip If Import Failed    ${result}

Manager Get Recovery Query
    [Documentation]    Test: Manager Get Recovery Query
    ${result}=    Manager Get Recovery Query
    Skip If Import Failed    ${result}

Manager Parse Recovery Results Empty
    [Documentation]    Test: Manager Parse Recovery Results Empty
    ${result}=    Manager Parse Recovery Results Empty
    Skip If Import Failed    ${result}

Manager Parse Recovery Results With Data
    [Documentation]    Test: Manager Parse Recovery Results With Data
    ${result}=    Manager Parse Recovery Results With Data
    Skip If Import Failed    ${result}

Manager Generate Amnesia Report No Context
    [Documentation]    Test: Manager Generate Amnesia Report No Context
    ${result}=    Manager Generate Amnesia Report No Context
    Skip If Import Failed    ${result}

Manager Generate Amnesia Report With Context
    [Documentation]    Test: Manager Generate Amnesia Report With Context
    ${result}=    Manager Generate Amnesia Report With Context
    Skip If Import Failed    ${result}
