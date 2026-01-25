*** Settings ***
Documentation    RF-004: Unit Tests - Data Integrity Validation
...              Migrated from tests/test_data_integrity.py
...              Per P10.7: Entity/Relation Schema Compliance
Library          Collections
Library          ../../libs/DataIntegrityLibrary.py

*** Test Cases ***
# =============================================================================
# Entity Validation Tests
# =============================================================================

Valid Rule Passes
    [Documentation]    GIVEN valid rule WHEN validate THEN passes all checks
    [Tags]    unit    integrity    entity    rule    valid
    ${result}=    Valid Rule Passes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_valid]
    Should Be True    ${result}[no_failures]
    Should Be True    ${result}[has_rule_id]
    Should Be True    ${result}[has_directive]

Missing Required Field Fails
    [Documentation]    GIVEN incomplete rule WHEN validate THEN fails
    [Tags]    unit    integrity    entity    rule    missing
    ${result}=    Missing Required Field Fails
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_valid]
    Should Be True    ${result}[has_category_failure]
    Should Be True    ${result}[has_priority_failure]

Valid Task Passes
    [Documentation]    GIVEN valid task WHEN validate THEN passes
    [Tags]    unit    integrity    entity    task    valid
    ${result}=    Valid Task Passes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_valid]
    Should Be True    ${result}[has_task_id]

Valid Decision Passes
    [Documentation]    GIVEN valid decision WHEN validate THEN passes
    [Tags]    unit    integrity    entity    decision    valid
    ${result}=    Valid Decision Passes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_valid]
    Should Be True    ${result}[has_context]
    Should Be True    ${result}[has_rationale]

Valid Gap Passes
    [Documentation]    GIVEN valid gap WHEN validate THEN passes
    [Tags]    unit    integrity    entity    gap    valid
    ${result}=    Valid Gap Passes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_valid]
    Should Be True    ${result}[has_severity]

Valid Agent Passes
    [Documentation]    GIVEN valid agent WHEN validate THEN passes
    [Tags]    unit    integrity    entity    agent    valid
    ${result}=    Valid Agent Passes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_valid]
    Should Be True    ${result}[has_agent_type]

Valid Session Passes
    [Documentation]    GIVEN valid session WHEN validate THEN passes
    [Tags]    unit    integrity    entity    session    valid
    ${result}=    Valid Session Passes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_valid]

Unknown Entity Type Fails
    [Documentation]    GIVEN unknown type WHEN validate THEN fails
    [Tags]    unit    integrity    entity    unknown    error
    ${result}=    Unknown Entity Type Fails
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_valid]
    Should Be True    ${result}[has_unknown_error]

Alternative Field Naming
    [Documentation]    GIVEN snake_case fields WHEN validate THEN handles
    [Tags]    unit    integrity    entity    naming    snake
    ${result}=    Alternative Field Naming
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_valid]

Invalid Enum Value Warns
    [Documentation]    GIVEN invalid enum WHEN validate THEN warns
    [Tags]    unit    integrity    entity    enum    warning
    ${result}=    Invalid Enum Value Warns
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_valid]
    Should Be True    ${result}[has_warnings]
    Should Be True    ${result}[priority_warning]

# =============================================================================
# Relation Validation Tests
# =============================================================================

Valid References Gap Passes
    [Documentation]    GIVEN valid references-gap WHEN validate THEN passes
    [Tags]    unit    integrity    relation    gap    valid
    ${result}=    Valid References Gap Passes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_valid]
    Should Be True    ${result}[has_task_role]
    Should Be True    ${result}[has_gap_role]

Valid Task Outcome Passes
    [Documentation]    GIVEN valid task-outcome WHEN validate THEN passes
    [Tags]    unit    integrity    relation    outcome    valid
    ${result}=    Valid Task Outcome Passes
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_valid]
    Should Be True    ${result}[has_authority_attr]

Missing Role Fails
    [Documentation]    GIVEN missing role WHEN validate THEN fails
    [Tags]    unit    integrity    relation    role    missing
    ${result}=    Missing Role Fails
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_valid]
    Should Be True    ${result}[has_gap_failure]

Unknown Relation Fails
    [Documentation]    GIVEN unknown relation WHEN validate THEN fails
    [Tags]    unit    integrity    relation    unknown    error
    ${result}=    Unknown Relation Fails
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[not_valid]

# =============================================================================
# Entity Set Validation Tests
# =============================================================================

Validate Entity Set
    [Documentation]    GIVEN rule set WHEN validate_entity_set THEN summary
    [Tags]    unit    integrity    set    summary    valid
    ${result}=    Validate Entity Set
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[total_correct]
    Should Be True    ${result}[valid_correct]
    Should Be True    ${result}[coverage_100]

Mixed Validity Set
    [Documentation]    GIVEN mixed validity WHEN validate_entity_set THEN counts
    [Tags]    unit    integrity    set    mixed    count
    ${result}=    Mixed Validity Set
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[total_correct]
    Should Be True    ${result}[valid_correct]
    Should Be True    ${result}[invalid_correct]
    Should Be True    ${result}[has_failures]

# =============================================================================
# Cross-Entity Consistency Tests
# =============================================================================

Valid Gap Reference
    [Documentation]    GIVEN task with valid gap ref WHEN check THEN passes
    [Tags]    unit    integrity    cross    gap    valid
    ${result}=    Valid Gap Reference
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[score_100]
    Should Be True    ${result}[no_orphans]

Orphan Gap Reference
    [Documentation]    GIVEN task with orphan gap ref WHEN check THEN flagged
    [Tags]    unit    integrity    cross    gap    orphan
    ${result}=    Orphan Gap Reference
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[score_below_100]
    Should Be True    ${result}[has_orphan]
    Should Be True    ${result}[correct_gap]

# =============================================================================
# Integrity Report Tests
# =============================================================================

Generate Report
    [Documentation]    GIVEN validations WHEN generate_report THEN comprehensive
    [Tags]    unit    integrity    report    generate
    ${result}=    Generate Report
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_summary]
    Should Be True    ${result}[total_2]
    Should Be True    ${result}[valid_2]
    Should Be True    ${result}[score_100]
    Should Be True    ${result}[has_by_type]
    Should Be True    ${result}[has_rule]

Empty Report
    [Documentation]    GIVEN no validations WHEN generate_report THEN handles
    [Tags]    unit    integrity    report    empty
    ${result}=    Empty Report
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_error]

# =============================================================================
# ValidationResult Tests
# =============================================================================

Result To Dict
    [Documentation]    GIVEN ValidationResult WHEN to_dict THEN serializes
    [Tags]    unit    integrity    result    dict
    ${result}=    Result To Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[entity_type]
    Should Be True    ${result}[entity_id]
    Should Be True    ${result}[not_valid]
    Should Be True    ${result}[has_passed]
    Should Be True    ${result}[has_failed]

Is Valid Property
    [Documentation]    GIVEN ValidationResult WHEN add_fail THEN is_valid false
    [Tags]    unit    integrity    result    valid
    ${result}=    Is Valid Property
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[initially_valid]
    Should Be True    ${result}[not_valid_after_fail]

# =============================================================================
# Validator Accumulation Tests
# =============================================================================

Validator Accumulates Results
    [Documentation]    GIVEN multiple entities WHEN validate THEN accumulates
    [Tags]    unit    integrity    accumulate    multiple
    ${result}=    Validator Accumulates Results
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[three_results]
    Should Be True    ${result}[total_3]
    Should Be True    ${result}[has_rule]
    Should Be True    ${result}[has_task]
    Should Be True    ${result}[has_decision]

# =============================================================================
# ID Pattern Validation Tests
# =============================================================================

Valid Rule ID Pattern
    [Documentation]    GIVEN RULE-XXX pattern WHEN validate THEN passes
    [Tags]    unit    integrity    pattern    rule    valid
    ${result}=    Valid Rule ID Pattern
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_id_pattern]

Invalid Rule ID Pattern
    [Documentation]    GIVEN non-conforming ID WHEN validate THEN warns
    [Tags]    unit    integrity    pattern    rule    invalid
    ${result}=    Invalid Rule ID Pattern
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_id_warning]

Valid Task ID Patterns
    [Documentation]    GIVEN various task IDs WHEN validate THEN all pass
    [Tags]    unit    integrity    pattern    task    valid
    ${result}=    Valid Task ID Patterns
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[all_valid]

# =============================================================================
# Validation Level Tests
# =============================================================================

Schema Level Validation
    [Documentation]    GIVEN SCHEMA level WHEN validate THEN correct level
    [Tags]    unit    integrity    level    schema
    ${result}=    Schema Level Validation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct_level]

API Level Validation
    [Documentation]    GIVEN API level WHEN validate THEN correct level
    [Tags]    unit    integrity    level    api
    ${result}=    API Level Validation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct_level]

UI Level Validation
    [Documentation]    GIVEN UI level WHEN validate THEN correct level
    [Tags]    unit    integrity    level    ui
    ${result}=    UI Level Validation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct_level]

Report Groups By Level
    [Documentation]    GIVEN multiple levels WHEN report THEN groups by level
    [Tags]    unit    integrity    level    report
    ${result}=    Report Groups By Level
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_by_level]
    Should Be True    ${result}[has_schema]
    Should Be True    ${result}[has_api]
