*** Settings ***
Documentation    DSM Tracker Integration Tests
...              Per: RULE-012 (DSP)
...              Migrated from tests/test_dsm_tracker_integration.py
Library          Collections
Library          ../../libs/DSMTrackerIntegrationLibrary.py
Resource         ../resources/common.resource
Force Tags             unit    dsm    integration    rule-012    high    GAP-DSP-NOTIFY-001    session    validate    SESSION-DSM-01-v1

*** Test Cases ***
# =============================================================================
# State Persistence Tests
# =============================================================================

Test State Saved On Start Cycle
    [Documentation]    State file created on start_cycle
    [Tags]    state    persistence
    ${result}=    State Saved On Start Cycle
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['state_created']}
    Should Be True    ${result['batch_id_correct']}

Test State Saved On Advance Phase
    [Documentation]    State updated on advance_phase
    [Tags]    state    persistence
    ${result}=    State Saved On Advance Phase
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['phase_updated']}

Test State Saved On Checkpoint
    [Documentation]    State updated on checkpoint
    [Tags]    state    persistence
    ${result}=    State Saved On Checkpoint
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['checkpoint_saved']}

Test State Loaded On Init
    [Documentation]    State loaded from file on init
    [Tags]    state    persistence
    ${result}=    State Loaded On Init
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['cycle_loaded']}
    Should Be True    ${result['cycle_id_matches']}
    Should Be True    ${result['batch_id_matches']}

Test State Cleared On Complete
    [Documentation]    State cleared on complete_cycle
    [Tags]    state    persistence
    ${result}=    State Cleared On Complete
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['state_cleared']}

# =============================================================================
# Evidence Generation Tests
# =============================================================================

Test Evidence File Created
    [Documentation]    Evidence markdown file created on complete
    [Tags]    evidence    generation
    ${result}=    Evidence File Created
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['file_created']}

Test Evidence Contains Summary
    [Documentation]    Evidence file contains summary section
    [Tags]    evidence    generation
    ${result}=    Evidence Contains Summary
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_summary_section']}
    Should Be True    ${result['has_batch_id']}

Test Evidence Contains Findings
    [Documentation]    Evidence file contains findings
    [Tags]    evidence    generation
    ${result}=    Evidence Contains Findings
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_findings_section']}
    Should Be True    ${result['has_finding_text']}

Test Evidence Contains Checkpoints
    [Documentation]    Evidence file contains checkpoints
    [Tags]    evidence    generation
    ${result}=    Evidence Contains Checkpoints
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_checkpoints_section']}
    Should Be True    ${result['has_checkpoint_text']}

Test Evidence Contains Metrics
    [Documentation]    Evidence file contains metrics
    [Tags]    evidence    generation
    ${result}=    Evidence Contains Metrics
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_metrics_section']}
    Should Be True    ${result['has_metric_key']}
    Should Be True    ${result['has_metric_value']}

# =============================================================================
# Full Cycle Workflow Tests
# =============================================================================

Test Full Cycle Workflow
    [Documentation]    Full DSP cycle from start to complete
    [Tags]    workflow    full-cycle
    ${result}=    Full Cycle Workflow
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['start_idle']}
    Should Be True    ${result['advance_audit']}
    Should Be True    ${result['advance_hypothesize']}
    Should Be True    ${result['advance_measure']}
    Should Be True    ${result['advance_optimize']}
    Should Be True    ${result['advance_validate']}
    Should Be True    ${result['advance_dream']}
    Should Be True    ${result['advance_report']}
    Should Be True    ${result['evidence_exists']}
    Should Be True    ${result['completed_count']}
    Should Be True    ${result['cycle_cleared']}

Test Resume Interrupted Cycle
    [Documentation]    Resume cycle after interruption
    [Tags]    workflow    resume
    ${result}=    Resume Interrupted Cycle
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['cycle_resumed']}
    Should Be True    ${result['phase_correct']}
    Should Be True    ${result['checkpoints_preserved']}
    Should Be True    ${result['can_continue']}

# =============================================================================
# Metrics Update Tests
# =============================================================================

Test Update Metrics Adds To Cycle
    [Documentation]    update_metrics adds metrics to cycle
    [Tags]    metrics
    ${result}=    Update Metrics Adds To Cycle
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['tests_added']}
    Should Be True    ${result['coverage_added']}

Test Update Metrics Merges With Existing
    [Documentation]    update_metrics merges with existing metrics
    [Tags]    metrics
    ${result}=    Update Metrics Merges With Existing
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['tests_preserved']}
    Should Be True    ${result['coverage_merged']}

Test Update Metrics No Cycle Raises
    [Documentation]    update_metrics without cycle raises ValueError
    [Tags]    metrics    error-handling
    ${result}=    Update Metrics No Cycle Raises
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['raises_error']}
    Should Be True    ${result['error_message_correct']}

# =============================================================================
# MCP Tool Existence Tests
# =============================================================================

Test DSM Start Tool Exists
    [Documentation]    dsm_start MCP tool exists
    [Tags]    mcp    existence
    ${result}=    DSM Start Tool Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test DSM Advance Tool Exists
    [Documentation]    dsm_advance MCP tool exists
    [Tags]    mcp    existence
    ${result}=    DSM Advance Tool Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test DSM Checkpoint Tool Exists
    [Documentation]    dsm_checkpoint MCP tool exists
    [Tags]    mcp    existence
    ${result}=    DSM Checkpoint Tool Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test DSM Status Tool Exists
    [Documentation]    dsm_status MCP tool exists
    [Tags]    mcp    existence
    ${result}=    DSM Status Tool Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test DSM Complete Tool Exists
    [Documentation]    dsm_complete MCP tool exists
    [Tags]    mcp    existence
    ${result}=    DSM Complete Tool Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test DSM Finding Tool Exists
    [Documentation]    dsm_finding MCP tool exists
    [Tags]    mcp    existence
    ${result}=    DSM Finding Tool Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test DSM Metrics Tool Exists
    [Documentation]    dsm_metrics MCP tool exists
    [Tags]    mcp    existence
    ${result}=    DSM Metrics Tool Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

# =============================================================================
# MCP Tool Functionality Tests
# =============================================================================

Test DSM Start Returns JSON
    [Documentation]    dsm_start returns valid JSON
    [Tags]    mcp    functionality
    ${result}=    DSM Start Returns JSON
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['valid_json']}
    Should Be True    ${result['has_cycle_id']}
    Should Be True    ${result['batch_id_correct']}

Test DSM Advance Returns JSON
    [Documentation]    dsm_advance returns valid JSON
    [Tags]    mcp    functionality
    ${result}=    DSM Advance Returns JSON
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['valid_json']}
    Should Be True    ${result['new_phase_audit']}
    Should Be True    ${result['has_required_mcps']}

Test DSM Status Returns JSON
    [Documentation]    dsm_status returns valid JSON
    [Tags]    mcp    functionality
    ${result}=    DSM Status Returns JSON
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['valid_json']}
    Should Be True    ${result['has_active']}
    Should Be True    ${result['active_is_true']}

Test DSM Checkpoint Returns JSON
    [Documentation]    dsm_checkpoint returns valid JSON
    [Tags]    mcp    functionality
    ${result}=    DSM Checkpoint Returns JSON
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['valid_json']}
    Should Be True    ${result['description_correct']}
    Should Be True    ${result['has_timestamp']}

Test DSM Finding Returns JSON
    [Documentation]    dsm_finding returns valid JSON
    [Tags]    mcp    functionality
    ${result}=    DSM Finding Returns JSON
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['valid_json']}
    Should Be True    ${result['has_finding_id']}
    Should Be True    ${result['finding_type_correct']}
    Should Be True    ${result['has_rule_reference']}

# =============================================================================
# RULE-012 Compliance Tests
# =============================================================================

Test Phases Match Rule 012
    [Documentation]    DSP phases match RULE-012 specification
    [Tags]    compliance    rule-012
    ${result}=    Phases Match Rule 012
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['phase_0_audit']}
    Should Be True    ${result['phase_1_hypothesize']}
    Should Be True    ${result['phase_2_measure']}
    Should Be True    ${result['phase_3_optimize']}
    Should Be True    ${result['phase_4_validate']}
    Should Be True    ${result['phase_5_dream']}
    Should Be True    ${result['phase_6_report']}

Test Evidence References Rule 012
    [Documentation]    Evidence file references RULE-012
    [Tags]    compliance    rule-012
    ${result}=    Evidence References Rule 012
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['references_rule_012']}

Test MCPs Per Phase Per Rule 012
    [Documentation]    MCP requirements match RULE-012 specification
    [Tags]    compliance    rule-012
    ${result}=    MCPs Per Phase Per Rule 012
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['audit_mcps_correct']}
    Should Be True    ${result['hypothesize_mcps_correct']}
    Should Be True    ${result['measure_mcps_correct']}
    Should Be True    ${result['validate_mcps_correct']}
