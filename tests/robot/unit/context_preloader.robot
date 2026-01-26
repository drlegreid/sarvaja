*** Settings ***
Documentation    Context Preloader Tests
...              Per GAP-CTX-002: Context Auto-Loading
...              Migrated from tests/test_context_preloader.py
Library          Collections
Library          ../../libs/ContextPreloaderLibrary.py
Resource         ../resources/common.resource
Tags             unit    context    preloader

*** Test Cases ***
# =============================================================================
# Decision Tests
# =============================================================================

Test Decision Creation
    [Documentation]    Test creating a Decision dataclass
    [Tags]    decision
    ${result}=    Decision Creation
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['id_correct']}
    Should Be True    ${result['status_correct']}

Test Decision Default Values
    [Documentation]    Test Decision default values
    [Tags]    decision
    ${result}=    Decision Default Values
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['rationale_empty']}
    Should Be True    ${result['source_file_empty']}

# =============================================================================
# TechnologyChoice Tests
# =============================================================================

Test Technology Choice Creation
    [Documentation]    Test creating a TechnologyChoice dataclass
    [Tags]    technology
    ${result}=    Technology Choice Creation
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['area_correct']}
    Should Be True    ${result['choice_correct']}

# =============================================================================
# ContextSummary Tests
# =============================================================================

Test Context Summary Creation
    [Documentation]    Test creating an empty ContextSummary
    [Tags]    summary
    ${result}=    Context Summary Creation
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['decisions_empty']}
    Should Be True    ${result['tech_choices_empty']}
    Should Be True    ${result['phase_none']}
    Should Be True    ${result['gaps_zero']}
    Should Be True    ${result['has_loaded_at']}

Test Context Summary To Dict
    [Documentation]    Test converting ContextSummary to dict
    [Tags]    summary
    ${result}=    Context Summary To Dict
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_decisions']}
    Should Be True    ${result['decisions_count']}
    Should Be True    ${result['decision_id']}
    Should Be True    ${result['phase_correct']}

Test Context Summary To Agent Prompt
    [Documentation]    Test generating agent prompt from context
    [Tags]    summary    prompt
    ${result}=    Context Summary To Agent Prompt
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_strategic']}
    Should Be True    ${result['has_decision']}
    Should Be True    ${result['has_typedb']}
    Should Be True    ${result['has_trame']}
    Should Be True    ${result['has_phase']}

Test Agent Prompt Filters Inactive Decisions
    [Documentation]    Test that agent prompt only shows active decisions
    [Tags]    summary    prompt
    ${result}=    Agent Prompt Filters Inactive
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['active_included']}
    Should Be True    ${result['inactive_excluded']}

# =============================================================================
# ContextPreloader Tests
# =============================================================================

Test Preloader Initialization
    [Documentation]    Test ContextPreloader initialization
    [Tags]    preloader
    ${result}=    Preloader Initialization
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_root']}
    Should Be True    ${result['cache_none']}

Test Preloader Load Context
    [Documentation]    Test loading context from project
    [Tags]    preloader
    ${result}=    Preloader Load Context
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_summary']}
    Should Be True    ${result['has_loaded_at']}

Test Preloader Caching
    [Documentation]    Test that preloader caches results
    [Tags]    preloader    cache
    ${result}=    Preloader Caching
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['same_instance']}

Test Preloader Force Refresh
    [Documentation]    Test force refresh bypasses cache
    [Tags]    preloader    cache
    ${result}=    Preloader Force Refresh
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['different_instance']}

Test Preloader Invalidate Cache
    [Documentation]    Test cache invalidation
    [Tags]    preloader    cache
    ${result}=    Preloader Invalidate Cache
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['cached_before']}
    Should Be True    ${result['cleared_after']}

Test Load Decisions From Evidence
    [Documentation]    Test loading decisions from evidence directory
    [Tags]    preloader    decisions
    ${result}=    Load Decisions From Evidence
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_list']}

Test Load Technology Choices
    [Documentation]    Test loading technology choices from CLAUDE.md
    [Tags]    preloader    technology
    ${result}=    Load Technology Choices
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_list']}
    Should Be True    ${result['valid_items']}

Test Detect Active Phase
    [Documentation]    Test detecting active phase from backlog
    [Tags]    preloader
    ${result}=    Detect Active Phase
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['valid_type']}

Test Count Open Gaps
    [Documentation]    Test counting open gaps from GAP-INDEX.md
    [Tags]    preloader    gaps
    ${result}=    Count Open Gaps
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_int']}
    Should Be True    ${result['non_negative']}

# =============================================================================
# Convenience Function Tests
# =============================================================================

Test Preload Session Context Function
    [Documentation]    Test preload_session_context function
    [Tags]    convenience
    ${result}=    Preload Session Context Function
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_summary']}

Test Get Agent Context Prompt Function
    [Documentation]    Test get_agent_context_prompt function
    [Tags]    convenience
    ${result}=    Get Agent Context Prompt Function
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_string']}
    Should Be True    ${result['has_context']}

# =============================================================================
# Decision File Parsing Tests
# =============================================================================

Test Parse Decision File With Temp File
    [Documentation]    Test parsing a decision file
    [Tags]    parsing
    ${result}=    Parse Decision File With Temp File
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['not_none']}
    Should Be True    ${result['id_correct']}
    Should Be True    ${result['status_correct']}
    Should Be True    ${result['has_summary']}

Test Parse Session Decisions File
    [Documentation]    Test parsing decisions from session file
    [Tags]    parsing
    ${result}=    Parse Session Decisions File
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['count_correct']}
    Should Be True    ${result['first_id']}
    Should Be True    ${result['first_status']}
    Should Be True    ${result['second_id']}
    Should Be True    ${result['second_status']}

# =============================================================================
# Integration Tests
# =============================================================================

Test Context Imported In Chat
    [Documentation]    Test that context preloader is importable from its module
    [Tags]    integration
    ${result}=    Context Imported In Chat
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['callable']}

Test Context Command Available
    [Documentation]    Test that /context command is available in chat
    [Tags]    integration    chat
    ${result}=    Context Command Available
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_context']}

Test Context Command Returns Prompt
    [Documentation]    Test that /context command returns context prompt
    [Tags]    integration    chat
    ${result}=    Context Command Returns Prompt
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_string']}
    Should Be True    ${result['has_content']}
