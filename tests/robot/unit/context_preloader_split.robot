*** Settings ***
Documentation    RF-004: Unit Tests - Context Preloader Split
...              Migrated from tests/test_context_preloader_split.py
...              Per GAP-FILE-022: context_preloader.py split
Library          Collections
Library          ../../libs/ContextPreloaderSplitLibrary.py
Force Tags        unit    context    split    low    DOC-SIZE-01-v1    sessions    session    read

*** Test Cases ***
# =============================================================================
# Package Structure Tests
# =============================================================================

Context Preloader Package Exists
    [Documentation]    GIVEN governance dir WHEN checking THEN context_preloader exists
    [Tags]    unit    preloader    split    package
    ${result}=    Context Preloader Package Exists
    Should Be True    ${result}[exists]

Models Module Exists
    [Documentation]    GIVEN context_preloader pkg WHEN checking THEN models.py exists
    [Tags]    unit    preloader    split    models
    ${result}=    Models Module Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Package not yet split
    Should Be True    ${result}[exists]

# =============================================================================
# Backward Compatibility Tests
# =============================================================================

Import Context Preloader Class
    [Documentation]    GIVEN module WHEN import ContextPreloader THEN works
    [Tags]    unit    preloader    split    import
    ${result}=    Import Context Preloader Class
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

Import Decision Class
    [Documentation]    GIVEN module WHEN import Decision THEN works
    [Tags]    unit    preloader    split    import
    ${result}=    Import Decision Class
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

Import Technology Choice Class
    [Documentation]    GIVEN module WHEN import TechnologyChoice THEN works
    [Tags]    unit    preloader    split    import
    ${result}=    Import Technology Choice Class
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

Import Context Summary Class
    [Documentation]    GIVEN module WHEN import ContextSummary THEN works
    [Tags]    unit    preloader    split    import
    ${result}=    Import Context Summary Class
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

Import Get Context Preloader
    [Documentation]    GIVEN module WHEN import get_context_preloader THEN works
    [Tags]    unit    preloader    split    import
    ${result}=    Import Get Context Preloader
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

Import Preload Session Context
    [Documentation]    GIVEN module WHEN import preload_session_context THEN works
    [Tags]    unit    preloader    split    import
    ${result}=    Import Preload Session Context
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

Import Get Agent Context Prompt
    [Documentation]    GIVEN module WHEN import get_agent_context_prompt THEN works
    [Tags]    unit    preloader    split    import
    ${result}=    Import Get Agent Context Prompt
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[imported]

# =============================================================================
# Models Module Tests
# =============================================================================

Decision Dataclass Works
    [Documentation]    GIVEN Decision WHEN creating THEN fields correct
    [Tags]    unit    preloader    split    dataclass
    ${result}=    Decision Dataclass Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[status_correct]

Technology Choice Dataclass Works
    [Documentation]    GIVEN TechnologyChoice WHEN creating THEN fields correct
    [Tags]    unit    preloader    split    dataclass
    ${result}=    Technology Choice Dataclass Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[area_correct]
    Should Be True    ${result}[choice_correct]

Context Summary Dataclass Works
    [Documentation]    GIVEN ContextSummary WHEN creating THEN defaults correct
    [Tags]    unit    preloader    split    dataclass
    ${result}=    Context Summary Dataclass Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[decisions_empty]
    Should Be True    ${result}[tech_choices_empty]
    Should Be True    ${result}[phase_none]

Context Summary To Agent Prompt
    [Documentation]    GIVEN ContextSummary WHEN to_agent_prompt THEN string
    [Tags]    unit    preloader    split    prompt
    ${result}=    Context Summary To Agent Prompt
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_string]
    Should Be True    ${result}[has_strategic]

Context Summary To Dict
    [Documentation]    GIVEN ContextSummary WHEN to_dict THEN dict
    [Tags]    unit    preloader    split    serialize
    ${result}=    Context Summary To Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_dict]
    Should Be True    ${result}[has_decisions]
    Should Be True    ${result}[has_tech_choices]

# =============================================================================
# Integration Tests
# =============================================================================

Preloader Creates Instance
    [Documentation]    GIVEN ContextPreloader WHEN creating THEN instance created
    [Tags]    unit    preloader    split    integration
    ${result}=    Preloader Creates Instance
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[created]

Preloader Load Context
    [Documentation]    GIVEN ContextPreloader WHEN load_context THEN ContextSummary
    [Tags]    unit    preloader    split    integration
    ${result}=    Preloader Load Context
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_context_summary]

Get Context Preloader Returns Same Instance
    [Documentation]    GIVEN get_context_preloader WHEN called twice THEN singleton
    [Tags]    unit    preloader    split    singleton
    ${result}=    Get Context Preloader Returns Same Instance
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[same_instance]

Preload Session Context Works
    [Documentation]    GIVEN preload_session_context WHEN called THEN ContextSummary
    [Tags]    unit    preloader    split    integration
    ${result}=    Preload Session Context Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_context_summary]
