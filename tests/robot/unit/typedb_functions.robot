*** Settings ***
Documentation    TypeDB 3.x Inference Functions Integration Tests
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/integration/test_typedb_functions.py
...              Tests transitive_dependencies, priority_conflicts, etc.
Library          Collections
Library          ../../libs/TypeDBFunctionsLibrary.py
Resource         ../resources/common.resource
Force Tags             integration    typedb    typedb3    functions    medium    validate    ARCH-INFRA-01-v1

*** Test Cases ***
# =============================================================================
# Transitive Dependencies Tests
# =============================================================================

Test Transitive Dependencies Function Exists
    [Documentation]    Verify transitive_dependencies() function is defined in schema
    [Tags]    transitive    schema
    ${result}=    Transitive Dependencies Function Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB not available')}
    Should Be True    ${result['function_exists']}

Test Transitive Dependencies Returns Direct
    [Documentation]    Transitive function includes direct dependencies
    [Tags]    transitive    direct
    ${result}=    Transitive Dependencies Returns Direct
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB not available')}
    Should Be True    ${result['includes_direct']}

# =============================================================================
# Priority Conflicts Tests
# =============================================================================

Test Priority Conflicts Detection
    [Documentation]    Conflicting rules should be detected
    [Tags]    conflicts    priority
    ${result}=    Priority Conflicts Detection
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB not available')}
    Should Be True    ${result['function_executes']}

# =============================================================================
# Escalated Proposals Tests
# =============================================================================

Test Escalated Proposals Detection
    [Documentation]    Proposals with 'escalate' resolution should be found
    [Tags]    escalated    proposals
    ${result}=    Escalated Proposals Detection
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB not available')}
    Should Be True    ${result['function_executes']}

# =============================================================================
# Cascaded Decision Affects Tests
# =============================================================================

Test Cascaded Decision Affects Includes Direct
    [Documentation]    Function should include direct decision-affects relations
    [Tags]    cascaded    decision
    ${result}=    Cascaded Decision Affects Includes Direct
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB not available')}
    Should Be True    ${result['includes_direct']}

# =============================================================================
# Proposal Cascade Affects Tests
# =============================================================================

Test Proposal Cascade Affects Includes Direct
    [Documentation]    Function should include direct proposal-affects relations
    [Tags]    cascade    proposal
    ${result}=    Proposal Cascade Affects Includes Direct
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'TypeDB not available')}
    Should Be True    ${result['includes_direct']}
