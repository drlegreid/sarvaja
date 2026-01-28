*** Settings ***
Documentation    RF-004: Session Collector Tests (Core, Log, Registry)
...              Migrated from governance/session_collector/
...              Per RF-007 Robot Framework Migration
Library          ../../libs/SessionCollectorCoreLibrary.py
Library          ../../libs/SessionCollectorLogLibrary.py
Library          ../../libs/SessionCollectorRegistryLibrary.py
Library          Collections
Resource         ../resources/common.resource
Force Tags             unit    sessions    collector    medium    SESSION-EVID-01-v1    session    evidence-file    validate

*** Test Cases ***
# =============================================================================
# Core Tests
# =============================================================================

Session Collector Class Exists
    [Documentation]    Test: Session Collector Class Exists
    ${result}=    Session Collector Class Exists
    Skip If Import Failed    ${result}

Session Collector Creates Session ID
    [Documentation]    Test: Session Collector Creates Session ID
    ${result}=    Session Collector Creates Session ID
    Skip If Import Failed    ${result}

Session Collector Stores Topic
    [Documentation]    Test: Session Collector Stores Topic
    ${result}=    Session Collector Stores Topic
    Skip If Import Failed    ${result}

Session Collector Has Empty Collections
    [Documentation]    Test: Session Collector Has Empty Collections
    ${result}=    Session Collector Has Empty Collections
    Skip If Import Failed    ${result}

Capture Prompt Adds Event
    [Documentation]    Test: Capture Prompt Adds Event
    ${result}=    Capture Prompt Adds Event
    Skip If Import Failed    ${result}

Capture Response Adds Event
    [Documentation]    Test: Capture Response Adds Event
    ${result}=    Capture Response Adds Event
    Skip If Import Failed    ${result}

Capture Error Adds Event
    [Documentation]    Test: Capture Error Adds Event
    ${result}=    Capture Error Adds Event
    Skip If Import Failed    ${result}

Capture Decision Creates Decision
    [Documentation]    Test: Capture Decision Creates Decision
    ${result}=    Capture Decision Creates Decision
    Skip If Import Failed    ${result}

Capture Decision Adds Event
    [Documentation]    Test: Capture Decision Adds Event
    ${result}=    Capture Decision Adds Event
    Skip If Import Failed    ${result}

Capture Task Creates Task
    [Documentation]    Test: Capture Task Creates Task
    ${result}=    Capture Task Creates Task
    Skip If Import Failed    ${result}

Capture Task Adds Event
    [Documentation]    Test: Capture Task Adds Event
    ${result}=    Capture Task Adds Event
    Skip If Import Failed    ${result}

To Dict Returns Dict
    [Documentation]    Test: To Dict Returns Dict
    ${result}=    To Dict Returns Dict
    Skip If Import Failed    ${result}

To JSON Returns Valid JSON
    [Documentation]    Test: To JSON Returns Valid JSON
    ${result}=    To JSON Returns Valid JSON
    Skip If Import Failed    ${result}

Session Event Dataclass Works
    [Documentation]    Test: Session Event Dataclass Works
    ${result}=    Session Event Dataclass Works
    Skip If Import Failed    ${result}

Task Dataclass Works
    [Documentation]    Test: Task Dataclass Works
    ${result}=    Task Dataclass Works
    Skip If Import Failed    ${result}

# =============================================================================
# Log Generation Tests
# =============================================================================

Generate Session Log Creates File
    [Documentation]    Test: Generate Session Log Creates File
    ${result}=    Generate Session Log Creates File
    Skip If Import Failed    ${result}

Generate Session Log Contains Header
    [Documentation]    Test: Generate Session Log Contains Header
    ${result}=    Generate Session Log Contains Header
    Skip If Import Failed    ${result}

Generate Session Log Contains Decisions
    [Documentation]    Test: Generate Session Log Contains Decisions
    ${result}=    Generate Session Log Contains Decisions
    Skip If Import Failed    ${result}

Generate Session Log Contains Thoughts
    [Documentation]    Test: Generate Session Log Contains Thoughts
    ${result}=    Generate Session Log Contains Thoughts
    Skip If Import Failed    ${result}

Generate Session Log Contains Tool Calls
    [Documentation]    Test: Generate Session Log Contains Tool Calls
    ${result}=    Generate Session Log Contains Tool Calls
    Skip If Import Failed    ${result}

Generate Session Log Contains Initial Prompt
    [Documentation]    Test: Generate Session Log Contains Initial Prompt
    ${result}=    Generate Session Log Contains Initial Prompt
    Skip If Import Failed    ${result}

# =============================================================================
# Registry Tests
# =============================================================================

Get Or Create Session Creates New
    [Documentation]    Test: Get Or Create Session Creates New
    ${result}=    Get Or Create Session Creates New
    Skip If Import Failed    ${result}

Get Or Create Session Returns Existing
    [Documentation]    Test: Get Or Create Session Returns Existing
    ${result}=    Get Or Create Session Returns Existing
    Skip If Import Failed    ${result}

List Active Sessions Returns IDs
    [Documentation]    Test: List Active Sessions Returns IDs
    ${result}=    List Active Sessions Returns IDs
    Skip If Import Failed    ${result}

End Session Removes And Generates Log
    [Documentation]    Test: End Session Removes And Generates Log
    ${result}=    End Session Removes And Generates Log
    Skip If Import Failed    ${result}

Session Start Tool Exists
    [Documentation]    Test: Session Start Tool Exists
    ${result}=    Session Start Tool Exists
    Skip If Import Failed    ${result}

Session Start Returns JSON
    [Documentation]    Test: Session Start Returns JSON
    ${result}=    Session Start Returns JSON
    Skip If Import Failed    ${result}

Session Decision Tool Exists
    [Documentation]    Test: Session Decision Tool Exists
    ${result}=    Session Decision Tool Exists
    Skip If Import Failed    ${result}

Session Task Tool Exists
    [Documentation]    Test: Session Task Tool Exists
    ${result}=    Session Task Tool Exists
    Skip If Import Failed    ${result}

Session End Tool Exists
    [Documentation]    Test: Session End Tool Exists
    ${result}=    Session End Tool Exists
    Skip If Import Failed    ${result}

Session List Tool Exists
    [Documentation]    Test: Session List Tool Exists
    ${result}=    Session List Tool Exists
    Skip If Import Failed    ${result}
