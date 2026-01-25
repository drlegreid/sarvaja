*** Settings ***
Documentation    RF-004: Unit Tests - Delegation Protocol
...              Migrated from tests/test_delegation.py
...              Per ORCH-004: Agent delegation protocol
Library          Collections
Library          ../../libs/DelegationLibrary.py

*** Test Cases ***
# =============================================================================
# DelegationType Tests
# =============================================================================

Delegation Type Research
    [Documentation]    GIVEN DelegationType WHEN RESEARCH THEN value is research
    [Tags]    unit    delegation    type    enum
    ${result}=    Delegation Type Research
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[value_correct]

Delegation Type Implementation
    [Documentation]    GIVEN DelegationType WHEN IMPLEMENTATION THEN value is impl
    [Tags]    unit    delegation    type    enum
    ${result}=    Delegation Type Implementation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[value_correct]

Delegation Type Validation
    [Documentation]    GIVEN DelegationType WHEN VALIDATION THEN value is validation
    [Tags]    unit    delegation    type    enum
    ${result}=    Delegation Type Validation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[value_correct]

Delegation Type Escalation
    [Documentation]    GIVEN DelegationType WHEN ESCALATION THEN value is escalation
    [Tags]    unit    delegation    type    enum
    ${result}=    Delegation Type Escalation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[value_correct]

# =============================================================================
# DelegationPriority Tests
# =============================================================================

Priority Ordering Works
    [Documentation]    GIVEN DelegationPriority WHEN comparing THEN CRITICAL < HIGH < MEDIUM < LOW
    [Tags]    unit    delegation    priority    enum
    ${result}=    Priority Ordering Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[crit_lt_high]
    Should Be True    ${result}[high_lt_med]
    Should Be True    ${result}[med_lt_low]

Critical Priority Value
    [Documentation]    GIVEN DelegationPriority.CRITICAL THEN value is 1
    [Tags]    unit    delegation    priority    enum
    ${result}=    Critical Priority Value
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_1]

# =============================================================================
# DelegationContext Tests
# =============================================================================

Context Basic Creation
    [Documentation]    GIVEN DelegationContext WHEN creating THEN fields set correctly
    [Tags]    unit    delegation    context    create
    ${result}=    Context Basic Creation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[task_correct]
    Should Be True    ${result}[source_correct]
    Should Be True    ${result}[priority_default]

Context With Constraints
    [Documentation]    GIVEN context WHEN constraints provided THEN stored
    [Tags]    unit    delegation    context    constraints
    ${result}=    Context With Constraints
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_constraints]
    Should Be True    ${result}[constraint_present]

Context With Evidence
    [Documentation]    GIVEN context WHEN evidence provided THEN stored
    [Tags]    unit    delegation    context    evidence
    ${result}=    Context With Evidence
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_evidence]

Context To Dict
    [Documentation]    GIVEN context WHEN to_dict THEN dictionary created
    [Tags]    unit    delegation    context    serialize
    ${result}=    Context To Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[priority_correct]
    Should Be True    ${result}[has_created_at]

Context From Dict
    [Documentation]    GIVEN dictionary WHEN from_dict THEN context created
    [Tags]    unit    delegation    context    deserialize
    ${result}=    Context From Dict
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[id_correct]
    Should Be True    ${result}[priority_correct]
    Should Be True    ${result}[trust_correct]

Context Min Trust Default
    [Documentation]    GIVEN context WHEN no trust specified THEN default 0.5
    [Tags]    unit    delegation    context    default
    ${result}=    Context Min Trust Default
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[default_trust]

# =============================================================================
# DelegationRequest Tests
# =============================================================================

Request Basic Creation
    [Documentation]    GIVEN DelegationRequest WHEN creating THEN fields set
    [Tags]    unit    delegation    request    create
    ${result}=    Request Basic Creation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[task_correct]
    Should Be True    ${result}[type_correct]
    Should Be True    ${result}[target_none]

Request With Specific Agent
    [Documentation]    GIVEN request WHEN target agent specified THEN stored
    [Tags]    unit    delegation    request    target
    ${result}=    Request With Specific Agent
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_target]

Request ID Auto Generated
    [Documentation]    GIVEN request WHEN created THEN ID auto-generated
    [Tags]    unit    delegation    request    id
    ${result}=    Request ID Auto Generated
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[starts_with_del]

# =============================================================================
# DelegationResult Tests
# =============================================================================

Result Success
    [Documentation]    GIVEN success result WHEN checking THEN success true
    [Tags]    unit    delegation    result    success
    ${result}=    Result Success
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_success]
    Should Be True    ${result}[status_correct]

Result Failure
    [Documentation]    GIVEN failure result WHEN checking THEN success false
    [Tags]    unit    delegation    result    failure
    ${result}=    Result Failure
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_failure]
    Should Be True    ${result}[has_message]

Result With Followup
    [Documentation]    GIVEN result WHEN needs followup THEN followup set
    [Tags]    unit    delegation    result    followup
    ${result}=    Result With Followup
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[needs_followup]
    Should Be True    ${result}[followup_type]

# =============================================================================
# DelegationProtocol Tests
# =============================================================================

Protocol Init
    [Documentation]    GIVEN DelegationProtocol WHEN init THEN empty state
    [Tags]    unit    delegation    protocol    init
    ${result}=    Protocol Init
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[active_zero]
    Should Be True    ${result}[history_empty]

Protocol Register Handler
    [Documentation]    GIVEN protocol WHEN register handler THEN registered
    [Tags]    unit    delegation    protocol    handler
    ${result}=    Protocol Register Handler
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[handler_registered]

Protocol Delegate No Agent
    [Documentation]    GIVEN no agents WHEN delegate THEN fails
    [Tags]    unit    delegation    protocol    failure
    ${result}=    Protocol Delegate No Agent
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[is_failure]
    Should Be True    ${result}[has_message]

Protocol Get Stats
    [Documentation]    GIVEN protocol WHEN get_stats THEN returns stats
    [Tags]    unit    delegation    protocol    stats
    ${result}=    Protocol Get Stats
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[has_active]
    Should Be True    ${result}[has_total]
    Should Be True    ${result}[has_success_rate]

# =============================================================================
# Convenience Function Tests
# =============================================================================

Create Delegation Context Works
    [Documentation]    GIVEN create_delegation_context WHEN called THEN context created
    [Tags]    unit    delegation    convenience    context
    ${result}=    Create Delegation Context Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[task_correct]
    Should Be True    ${result}[id_starts_with]
    Should Be True    ${result}[context_correct]

Create Research Request Works
    [Documentation]    GIVEN create_research_request WHEN called THEN request created
    [Tags]    unit    delegation    convenience    research
    ${result}=    Create Research Request Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[type_correct]
    Should Be True    ${result}[role_correct]

Create Implementation Request Works
    [Documentation]    GIVEN create_implementation_request WHEN called THEN request created
    [Tags]    unit    delegation    convenience    implementation
    ${result}=    Create Implementation Request Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Execution not possible
    Should Be True    ${result}[type_correct]
    Should Be True    ${result}[role_correct]
    Should Be True    ${result}[context_correct]
