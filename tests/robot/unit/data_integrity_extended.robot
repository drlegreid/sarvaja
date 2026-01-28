*** Settings ***
Documentation    RF-004: Data Integrity Extended Tests (Entity, Relation, Report)
...              Migrated from test_data_integrity_e2e.py
...              Per RF-007 Robot Framework Migration
Library          ../../libs/DataIntegrityEntityLibrary.py
Library          ../../libs/DataIntegrityRelationLibrary.py
Library          ../../libs/DataIntegrityReportLibrary.py
Library          Collections
Resource         ../resources/common.resource
Force Tags             unit    data-integrity    extended    tasks    low    task    validate    TASK-VALID-01-v1

*** Test Cases ***
# =============================================================================
# Entity Validation Tests
# =============================================================================

Valid Rule Passes
    [Documentation]    Test: Valid Rule Passes
    ${result}=    Valid Rule Passes
    Skip If Import Failed    ${result}

Missing Required Field Fails
    [Documentation]    Test: Missing Required Field Fails
    ${result}=    Missing Required Field Fails
    Skip If Import Failed    ${result}

Valid Task Passes
    [Documentation]    Test: Valid Task Passes
    ${result}=    Valid Task Passes
    Skip If Import Failed    ${result}

Valid Decision Passes
    [Documentation]    Test: Valid Decision Passes
    ${result}=    Valid Decision Passes
    Skip If Import Failed    ${result}

Valid Gap Passes
    [Documentation]    Test: Valid Gap Passes
    ${result}=    Valid Gap Passes
    Skip If Import Failed    ${result}

Valid Agent Passes
    [Documentation]    Test: Valid Agent Passes
    ${result}=    Valid Agent Passes
    Skip If Import Failed    ${result}

Valid Session Passes
    [Documentation]    Test: Valid Session Passes
    ${result}=    Valid Session Passes
    Skip If Import Failed    ${result}

Unknown Entity Type Fails
    [Documentation]    Test: Unknown Entity Type Fails
    ${result}=    Unknown Entity Type Fails
    Skip If Import Failed    ${result}

Alternative Field Naming
    [Documentation]    Test: Alternative Field Naming
    ${result}=    Alternative Field Naming
    Skip If Import Failed    ${result}

Invalid Enum Value Warns
    [Documentation]    Test: Invalid Enum Value Warns
    ${result}=    Invalid Enum Value Warns
    Skip If Import Failed    ${result}

# =============================================================================
# Relation Validation Tests
# =============================================================================

Valid References Gap Passes
    [Documentation]    Test: Valid References Gap Passes
    ${result}=    Valid References Gap Passes
    Skip If Import Failed    ${result}

Valid Task Outcome Passes
    [Documentation]    Test: Valid Task Outcome Passes
    ${result}=    Valid Task Outcome Passes
    Skip If Import Failed    ${result}

Missing Role Fails
    [Documentation]    Test: Missing Role Fails
    ${result}=    Missing Role Fails
    Skip If Import Failed    ${result}

Unknown Relation Fails
    [Documentation]    Test: Unknown Relation Fails
    ${result}=    Unknown Relation Fails
    Skip If Import Failed    ${result}

Validate Entity Set
    [Documentation]    Test: Validate Entity Set
    ${result}=    Validate Entity Set
    Skip If Import Failed    ${result}

Mixed Validity Set
    [Documentation]    Test: Mixed Validity Set
    ${result}=    Mixed Validity Set
    Skip If Import Failed    ${result}

Valid Gap Reference
    [Documentation]    Test: Valid Gap Reference
    ${result}=    Valid Gap Reference
    Skip If Import Failed    ${result}

Orphan Gap Reference
    [Documentation]    Test: Orphan Gap Reference
    ${result}=    Orphan Gap Reference
    Skip If Import Failed    ${result}

# =============================================================================
# Report Generation Tests
# =============================================================================

Generate Report
    [Documentation]    Test: Generate Report
    ${result}=    Generate Report
    Skip If Import Failed    ${result}

Empty Report
    [Documentation]    Test: Empty Report
    ${result}=    Empty Report
    Skip If Import Failed    ${result}

Result To Dict
    [Documentation]    Test: Result To Dict
    ${result}=    Result To Dict
    Skip If Import Failed    ${result}

Is Valid Property
    [Documentation]    Test: Is Valid Property
    ${result}=    Is Valid Property
    Skip If Import Failed    ${result}

Validator Accumulates Results
    [Documentation]    Test: Validator Accumulates Results
    ${result}=    Validator Accumulates Results
    Skip If Import Failed    ${result}

Valid Rule ID Pattern
    [Documentation]    Test: Valid Rule ID Pattern
    ${result}=    Valid Rule ID Pattern
    Skip If Import Failed    ${result}

Invalid Rule ID Pattern
    [Documentation]    Test: Invalid Rule ID Pattern
    ${result}=    Invalid Rule ID Pattern
    Skip If Import Failed    ${result}

Valid Task ID Patterns
    [Documentation]    Test: Valid Task ID Patterns
    ${result}=    Valid Task ID Patterns
    Skip If Import Failed    ${result}

Schema Level Validation
    [Documentation]    Test: Schema Level Validation
    ${result}=    Schema Level Validation
    Skip If Import Failed    ${result}

API Level Validation
    [Documentation]    Test: API Level Validation
    ${result}=    API Level Validation
    Skip If Import Failed    ${result}

UI Level Validation
    [Documentation]    Test: UI Level Validation
    ${result}=    UI Level Validation
    Skip If Import Failed    ${result}

Report Groups By Level
    [Documentation]    Test: Report Groups By Level
    ${result}=    Report Groups By Level
    Skip If Import Failed    ${result}
