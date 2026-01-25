*** Settings ***
Documentation    RF-004: Unit Tests - Task Detail Sections
...              Migrated from tests/test_task_details.py
...              Per GAP-TASK-LINK-004: Task details (business, design, arch, test)
...              Per TASK-TECH-01-v1: Technology Solution Documentation
Library          Collections
Library          ../../libs/TaskDetailsLibrary.py

*** Test Cases ***
# =============================================================================
# Section Design Tests
# =============================================================================

Section Names Valid
    [Documentation]    GIVEN section names WHEN validate THEN lowercase and non-empty
    [Tags]    unit    task    details    section    names
    ${result}=    Section Names Valid
    Should Be True    ${result}[all_lowercase]
    Should Be True    ${result}[all_have_content]
    Should Be True    ${result}[count_correct]

Section Descriptions Valid
    [Documentation]    GIVEN sections WHEN check THEN has four defined
    [Tags]    unit    task    details    section    descriptions
    ${result}=    Section Descriptions Valid
    Should Be True    ${result}[has_four_sections]

# =============================================================================
# Task Entity Tests
# =============================================================================

Task Has Business Field
    [Documentation]    GIVEN Task entity WHEN check THEN has business field
    [Tags]    unit    task    details    entity    business
    ${result}=    Task Has Business Field
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_field]

Task Has Design Field
    [Documentation]    GIVEN Task entity WHEN check THEN has design field
    [Tags]    unit    task    details    entity    design
    ${result}=    Task Has Design Field
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_field]

Task Has Architecture Field
    [Documentation]    GIVEN Task entity WHEN check THEN has architecture field
    [Tags]    unit    task    details    entity    architecture
    ${result}=    Task Has Architecture Field
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_field]

Task Has Test Section Field
    [Documentation]    GIVEN Task entity WHEN check THEN has test_section field
    [Tags]    unit    task    details    entity    test
    ${result}=    Task Has Test Section Field
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_field]

# =============================================================================
# TypeDB Schema Tests
# =============================================================================

Schema Has Business Attribute
    [Documentation]    GIVEN schema.tql WHEN check THEN has task-business
    [Tags]    unit    task    details    schema    business
    ${result}=    Schema Has Business Attribute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Schema file not found
    Should Be True    ${result}[has_attribute]

Schema Has Design Attribute
    [Documentation]    GIVEN schema.tql WHEN check THEN has task-design
    [Tags]    unit    task    details    schema    design
    ${result}=    Schema Has Design Attribute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Schema file not found
    Should Be True    ${result}[has_attribute]

Schema Has Architecture Attribute
    [Documentation]    GIVEN schema.tql WHEN check THEN has task-architecture
    [Tags]    unit    task    details    schema    architecture
    ${result}=    Schema Has Architecture Attribute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Schema file not found
    Should Be True    ${result}[has_attribute]

Schema Has Test Attribute
    [Documentation]    GIVEN schema.tql WHEN check THEN has task-test
    [Tags]    unit    task    details    schema    test
    ${result}=    Schema Has Test Attribute
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Schema file not found
    Should Be True    ${result}[has_attribute]

# =============================================================================
# Content Format Tests
# =============================================================================

Markdown Content Allowed
    [Documentation]    GIVEN markdown WHEN use in field THEN allowed
    [Tags]    unit    task    details    format    markdown
    ${result}=    Markdown Content Allowed
    Should Be True    ${result}[has_headers]
    Should Be True    ${result}[has_lists]

Multiline Content Supported
    [Documentation]    GIVEN multiline text WHEN use in field THEN supported
    [Tags]    unit    task    details    format    multiline
    ${result}=    Multiline Content Supported
    Should Be True    ${result}[supported]

# =============================================================================
# BDD Scenario Tests
# =============================================================================

Scenario Create Task With Details
    [Documentation]    GIVEN new task WHEN provide sections THEN all stored
    [Tags]    unit    task    details    bdd    create
    ${result}=    Scenario Create Task With Details
    Should Be True    ${result}[has_all_fields]

Scenario Update Task Section
    [Documentation]    GIVEN existing task WHEN update section THEN only that changes
    [Tags]    unit    task    details    bdd    update
    ${result}=    Scenario Update Task Section
    Should Be True    ${result}[can_update]

# =============================================================================
# Documentation Compliance Tests
# =============================================================================

Rule TASK TECH 01 v1 Exists
    [Documentation]    GIVEN docs/rules/leaf WHEN check THEN TASK-TECH-01-v1.md exists
    [Tags]    unit    task    details    compliance    rule
    ${result}=    Rule TASK TECH 01 v1 Exists
    Should Be True    ${result}[exists]

Rule Mentions Sections
    [Documentation]    GIVEN TASK-TECH-01-v1 WHEN read THEN mentions all sections
    [Tags]    unit    task    details    compliance    content
    ${result}=    Rule Mentions Sections
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Rule file not found
    Should Be True    ${result}[has_business]
    Should Be True    ${result}[has_design]
    Should Be True    ${result}[has_architecture]
    Should Be True    ${result}[has_test]
