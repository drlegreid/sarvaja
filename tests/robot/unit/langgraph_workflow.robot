*** Settings ***
Documentation    LangGraph Governance Workflow Tests
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/test_langgraph_workflow.py
...              Validates state management, voting, and decision logic.
Library          Collections
Library          ../../libs/LanggraphLibrary.py
Resource         ../resources/common.resource
Tags             unit    langgraph    workflow    rule-011

*** Test Cases ***
# =============================================================================
# State Schema Tests
# =============================================================================

Test Proposal State Exists
    [Documentation]    ProposalState type is defined
    [Tags]    schema    types
    ${result}=    Proposal State Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['type_defined']}

Test Vote Type Exists
    [Documentation]    Vote type is defined
    [Tags]    schema    types
    ${result}=    Vote Type Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['type_defined']}

Test Create Initial State
    [Documentation]    create_initial_state creates valid state
    [Tags]    schema    state
    ${result}=    Create Initial State
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_correct']}
    Should Be True    ${result['hypothesis_correct']}
    Should Be True    ${result['evidence_count']}
    Should Be True    ${result['status_pending']}
    Should Be True    ${result['dry_run_true']}

Test Initial State Has All Fields
    [Documentation]    Initial state includes all required fields
    [Tags]    schema    state
    ${result}=    Initial State Has All Fields
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['all_fields_present']}

# =============================================================================
# Governance Constants Tests
# =============================================================================

Test Quorum Threshold Defined
    [Documentation]    QUORUM_THRESHOLD is defined
    [Tags]    constants
    ${result}=    Quorum Threshold Defined
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['value_correct']}

Test Approval Threshold Defined
    [Documentation]    APPROVAL_THRESHOLD is defined
    [Tags]    constants
    ${result}=    Approval Threshold Defined
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['value_correct']}

Test Dispute Threshold Defined
    [Documentation]    DISPUTE_THRESHOLD is defined
    [Tags]    constants
    ${result}=    Dispute Threshold Defined
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['value_correct']}

Test Trust Weights Defined
    [Documentation]    TRUST_WEIGHTS follows RULE-011 formula
    [Tags]    constants    rule-011
    ${result}=    Trust Weights Defined
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['compliance_correct']}
    Should Be True    ${result['accuracy_correct']}
    Should Be True    ${result['consistency_correct']}
    Should Be True    ${result['tenure_correct']}
    Should Be True    ${result['sum_is_one']}

# =============================================================================
# Node Functions Tests
# =============================================================================

Test Submit Node Exists
    [Documentation]    submit_node function exists
    [Tags]    nodes
    ${result}=    Submit Node Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test Validate Node Exists
    [Documentation]    validate_node function exists
    [Tags]    nodes
    ${result}=    Validate Node Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test Assess Node Exists
    [Documentation]    assess_node function exists
    [Tags]    nodes
    ${result}=    Assess Node Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test Vote Node Exists
    [Documentation]    vote_node function exists
    [Tags]    nodes
    ${result}=    Vote Node Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test Decide Node Exists
    [Documentation]    decide_node function exists
    [Tags]    nodes
    ${result}=    Decide Node Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test Implement Node Exists
    [Documentation]    implement_node function exists
    [Tags]    nodes
    ${result}=    Implement Node Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test Complete Node Exists
    [Documentation]    complete_node function exists
    [Tags]    nodes
    ${result}=    Complete Node Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test Reject Node Exists
    [Documentation]    reject_node function exists
    [Tags]    nodes
    ${result}=    Reject Node Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

# =============================================================================
# Submit Node Logic Tests
# =============================================================================

Test Submit Generates Proposal Id
    [Documentation]    Submit generates proposal ID if not set
    [Tags]    submit
    ${result}=    Submit Generates Proposal Id
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_proposal_id']}
    Should Be True    ${result['id_prefix_correct']}

Test Submit Rejects Low Trust Submitter
    [Documentation]    Submit rejects submitters with low trust score
    [Tags]    submit    trust
    ${result}=    Submit Rejects Low Trust Submitter
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['status_failed']}
    Should Be True    ${result['has_trust_error']}

Test Submit Accepts Valid Submitter
    [Documentation]    Submit accepts submitters with sufficient trust score
    [Tags]    submit    trust
    ${result}=    Submit Accepts Valid Submitter
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['status_running']}
    Should Be True    ${result['submit_completed']}

# =============================================================================
# Validate Node Logic Tests
# =============================================================================

Test Validate Requires Hypothesis
    [Documentation]    Validation fails without hypothesis
    [Tags]    validate
    ${result}=    Validate Requires Hypothesis
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['validation_failed']}
    Should Be True    ${result['has_hypothesis_error']}

Test Validate Requires Evidence
    [Documentation]    Validation fails without evidence
    [Tags]    validate
    ${result}=    Validate Requires Evidence
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['validation_failed']}
    Should Be True    ${result['has_evidence_error']}

Test Validate Modify Requires Rule Id
    [Documentation]    Validation fails for modify without rule_id
    [Tags]    validate
    ${result}=    Validate Modify Requires Rule Id
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['validation_failed']}
    Should Be True    ${result['has_rule_id_error']}

Test Validate Create Requires Directive
    [Documentation]    Validation fails for create without directive
    [Tags]    validate
    ${result}=    Validate Create Requires Directive
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['validation_failed']}
    Should Be True    ${result['has_directive_error']}

Test Validate Passes Valid Create
    [Documentation]    Validation passes for valid create proposal
    [Tags]    validate
    ${result}=    Validate Passes Valid Create
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['validation_passed']}
    Should Be True    ${result['no_errors']}

# =============================================================================
# Assess Node Logic Tests
# =============================================================================

Test Assess Returns Impact Score
    [Documentation]    Assessment returns impact score
    [Tags]    assess    impact
    ${result}=    Assess Returns Impact Score
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_impact_score']}
    Should Be True    ${result['score_non_negative']}

Test Assess Returns Risk Level
    [Documentation]    Assessment returns risk level
    [Tags]    assess    risk
    ${result}=    Assess Returns Risk Level
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['risk_level_valid']}

Test Deprecate Has Higher Impact
    [Documentation]    Deprecate action has higher impact score
    [Tags]    assess    impact
    ${result}=    Deprecate Has Higher Impact
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['deprecate_higher']}

# =============================================================================
# Vote Node Tests
# =============================================================================

Test Vote Calculates Weighted Totals
    [Documentation]    Vote calculates weighted totals correctly
    [Tags]    vote
    ${result}=    Vote Calculates Weighted Totals
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_votes_for']}
    Should Be True    ${result['has_votes_against']}
    Should Be True    ${result['votes_non_negative']}

Test Vote Checks Quorum
    [Documentation]    Vote checks quorum requirement
    [Tags]    vote    quorum
    ${result}=    Vote Checks Quorum
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_quorum_reached']}
    Should Be True    ${result['is_boolean']}

Test Vote Checks Threshold
    [Documentation]    Vote checks approval threshold
    [Tags]    vote    threshold
    ${result}=    Vote Checks Threshold
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_threshold_met']}
    Should Be True    ${result['is_boolean']}

# =============================================================================
# Decide Node Tests
# =============================================================================

Test Decide Rejects Without Quorum
    [Documentation]    Decision rejects if quorum not reached
    [Tags]    decide    quorum
    ${result}=    Decide Rejects Without Quorum
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['decision_rejected']}
    Should Be True    ${result['mentions_quorum']}

Test Decide Approves With Quorum And Threshold
    [Documentation]    Decision approves if quorum and threshold met
    [Tags]    decide
    ${result}=    Decide Approves With Quorum And Threshold
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['decision_approved']}

Test Decide Rejects Below Threshold
    [Documentation]    Decision rejects if below threshold
    [Tags]    decide    threshold
    ${result}=    Decide Rejects Below Threshold
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['decision_rejected']}
    Should Be True    ${result['mentions_threshold']}

# =============================================================================
# Graph Building Tests
# =============================================================================

Test Build Proposal Graph Exists
    [Documentation]    build_proposal_graph function exists
    [Tags]    graph
    ${result}=    Build Proposal Graph Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test Graph Has Required Nodes
    [Documentation]    Graph has all required nodes
    [Tags]    graph    nodes
    ${result}=    Graph Has Required Nodes
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['all_nodes_present']}

# =============================================================================
# Workflow Execution Tests
# =============================================================================

Test Run Proposal Workflow Exists
    [Documentation]    run_proposal_workflow function exists
    [Tags]    execution
    ${result}=    Run Proposal Workflow Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test Dry Run Completes
    [Documentation]    Dry-run workflow completes
    [Tags]    execution    dry-run
    ${result}=    Dry Run Completes
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['result_not_none']}
    Should Be True    ${result['status_valid']}
    Should Be True    ${result['submit_completed']}

Test Workflow Returns Decision
    [Documentation]    Workflow returns decision
    [Tags]    execution
    ${result}=    Workflow Returns Decision
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['decision_valid']}

Test Invalid Proposal Fails
    [Documentation]    Invalid proposal fails validation
    [Tags]    execution    validation
    ${result}=    Invalid Proposal Fails
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['status_failed']}
    Should Be True    ${result['validation_failed']}

# =============================================================================
# MCP Wrapper Tests
# =============================================================================

Test Proposal Submit MCP Exists
    [Documentation]    proposal_submit_mcp function exists
    [Tags]    mcp
    ${result}=    Proposal Submit MCP Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test Proposal Submit MCP Returns JSON
    [Documentation]    proposal_submit_mcp returns valid JSON
    [Tags]    mcp    json
    ${result}=    Proposal Submit MCP Returns JSON
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_proposal_id']}
    Should Be True    ${result['has_decision']}
    Should Be True    ${result['has_status']}

Test Proposal Submit MCP Handles Comma Separated Evidence
    [Documentation]    MCP wrapper parses comma-separated evidence
    [Tags]    mcp    parsing
    ${result}=    Proposal Submit MCP Handles Comma Separated Evidence
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['proposal_id_present']}

# =============================================================================
# Workflow Visualization Tests
# =============================================================================

Test Print Workflow Diagram Exists
    [Documentation]    print_workflow_diagram function exists
    [Tags]    visualization
    ${result}=    Print Workflow Diagram Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}
