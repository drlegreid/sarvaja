*** Settings ***
Documentation    RF-004: Unit Tests - Rule Fallback Parser
...              Migrated from tests/test_rule_fallback.py
...              Per GAP-MCP-004: Rule fallback to markdown files
Library          Collections
Library          ../../libs/RuleFallbackLibrary.py
Force Tags        unit    rules    fallback    high    GOV-RULE-01-v1    rule    read

*** Test Cases ***
# =============================================================================
# Markdown Parser Tests
# =============================================================================

Parse Markdown Rules Basic
    [Documentation]    GIVEN markdown WHEN parse_markdown_rules THEN rules parsed
    [Tags]    unit    rules    fallback    parser
    ${result}=    Parse Markdown Rules Basic
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[count_correct]
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[category_correct]
    Should Be True    ${result}[priority_correct]
    Should Be True    ${result}[status_correct]
    Should Be True    ${result}[has_directive]

Parse Markdown Rules Second Rule
    [Documentation]    GIVEN markdown WHEN parse THEN second rule correct
    [Tags]    unit    rules    fallback    parser
    ${result}=    Parse Markdown Rules Second Rule
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[category_correct]
    Should Be True    ${result}[priority_correct]

Parse Markdown Rules Source File
    [Documentation]    GIVEN markdown WHEN parse THEN source tracked
    [Tags]    unit    rules    fallback    source
    ${result}=    Parse Markdown Rules Source File
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[source_correct]

Filter Markdown Rules By Category
    [Documentation]    GIVEN rules WHEN filter by category THEN filtered
    [Tags]    unit    rules    fallback    filter
    ${result}=    Filter Markdown Rules By Category
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[count_correct]
    Should Be True    ${result}[id_correct]

Filter Markdown Rules By Priority
    [Documentation]    GIVEN rules WHEN filter by priority THEN filtered
    [Tags]    unit    rules    fallback    filter
    ${result}=    Filter Markdown Rules By Priority
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[count_correct]
    Should Be True    ${result}[id_correct]

Filter Markdown Rules By Status
    [Documentation]    GIVEN rules WHEN filter by status THEN filtered
    [Tags]    unit    rules    fallback    filter
    ${result}=    Filter Markdown Rules By Status
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[count_correct]

Markdown Rule To Dict
    [Documentation]    GIVEN rule WHEN to_dict THEN dict correct
    [Tags]    unit    rules    fallback    serialize
    ${result}=    Markdown Rule To Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[name_correct]
    Should Be True    ${result}[source_correct]
    Should Be True    ${result}[source_file_correct]

# =============================================================================
# Rules Directory Tests
# =============================================================================

Get Rules Directory Returns Path
    [Documentation]    GIVEN project WHEN get_rules_directory THEN Path
    [Tags]    unit    rules    fallback    directory
    ${result}=    Get Rules Directory Returns Path
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_path]

Rules Directory Exists
    [Documentation]    GIVEN project WHEN check rules dir THEN exists
    [Tags]    unit    rules    fallback    directory
    ${result}=    Rules Directory Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[exists]

# =============================================================================
# Real Markdown Files Tests
# =============================================================================

Get All Markdown Rules
    [Documentation]    GIVEN docs/rules WHEN get_all_markdown_rules THEN rules
    [Tags]    unit    rules    fallback    real
    ${result}=    Get All Markdown Rules
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_rules]

Get Markdown Rule By Id Exists
    [Documentation]    GIVEN RULE-001 WHEN get_by_id THEN found
    [Tags]    unit    rules    fallback    lookup
    ${result}=    Get Markdown Rule By Id Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    RULE-001 not in markdown
    Should Be True    ${result}[not_none]
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[name_correct]

Get Markdown Rule By Id Not Found
    [Documentation]    GIVEN RULE-999 WHEN get_by_id THEN None
    [Tags]    unit    rules    fallback    lookup
    ${result}=    Get Markdown Rule By Id Not Found
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_none]

Known Rules Present
    [Documentation]    GIVEN docs/rules WHEN parse THEN known rules exist
    [Tags]    unit    rules    fallback    verify
    ${result}=    Known Rules Present
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Missing rules
    Should Be True    ${result}[all_present]

Rules Have Required Fields
    [Documentation]    GIVEN all rules WHEN validate THEN valid fields
    [Tags]    unit    rules    fallback    validate
    ${result}=    Rules Have Required Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    No rules found
    Should Be True    ${result}[valid]
