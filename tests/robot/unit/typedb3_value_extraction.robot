*** Settings ***
Documentation    TypeDB 3.x Value Extraction Integration Tests
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/integration/test_typedb3_value_extraction.py
...              Tests API returns clean values without Attribute wrappers.
Library          Collections
Library          ../../libs/TypeDB3ValueExtractionLibrary.py
Resource         ../resources/common.resource
Tags             integration    typedb3    api    value-extraction

*** Test Cases ***
# =============================================================================
# Value Extraction Tests
# =============================================================================

Test Tasks API Returns Clean Values
    [Documentation]    Verify tasks API returns clean string values, not Attribute wrappers
    [Tags]    tasks    clean-values
    ${result}=    Tasks API Returns Clean Values
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['all_values_clean']}

Test Rules API Returns Clean Values
    [Documentation]    Verify rules API returns clean string values, not Attribute wrappers
    [Tags]    rules    clean-values
    ${result}=    Rules API Returns Clean Values
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['all_values_clean']}

Test Task Values Are Proper Strings
    [Documentation]    Verify task values are proper strings (no type wrappers)
    [Tags]    tasks    strings
    ${result}=    Task Values Are Proper Strings
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['is_string']}
    Should Be True    ${result['no_wrapper']}
    Should Be True    ${result['reasonable_length']}

Test Rule Semantic ID Extraction
    [Documentation]    Verify semantic_id is properly extracted for rules
    [Tags]    rules    semantic-id
    ${result}=    Rule Semantic ID Extraction
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['is_string']}
    Should Be True    ${result['no_wrapper']}
    Should Be True    ${result['has_dashes']}

# =============================================================================
# API Response Format Tests
# =============================================================================

Test Tasks Pagination Metadata
    [Documentation]    Verify tasks API includes proper pagination metadata
    [Tags]    tasks    pagination
    ${result}=    Tasks Pagination Metadata
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['has_pagination']}
    Should Be True    ${result['has_total']}
    Should Be True    ${result['has_offset']}
    Should Be True    ${result['has_limit']}
    Should Be True    ${result['total_is_int']}
    Should Be True    ${result['offset_is_int']}

Test Rules Response Is List
    [Documentation]    Verify rules API returns a list (not wrapped object)
    [Tags]    rules    response-format
    ${result}=    Rules Response Is List
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'API not available')}
    Should Be True    ${result['is_list']}
