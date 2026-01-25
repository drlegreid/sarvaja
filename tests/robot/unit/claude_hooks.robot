*** Settings ***
Documentation    RF-004: Unit Tests - Claude Code Hooks
...              Migrated from tests/test_claude_hooks.py
...              Per GAP-MCP-003: SessionStart hook context injection
...              Per EPIC-006: Entropy Monitor for SLEEP Mode Automation
Library          Collections
Library          ../../libs/ClaudeHooksLibrary.py

*** Test Cases ***
# =============================================================================
# Healthcheck Output Tests
# =============================================================================

Healthcheck Returns Valid JSON
    [Documentation]    GIVEN healthcheck WHEN run THEN returns valid JSON
    [Tags]    unit    hooks    healthcheck    output    json
    ${result}=    Healthcheck Returns Valid JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[valid_json]

Healthcheck Has Hook Specific Output
    [Documentation]    GIVEN healthcheck WHEN run THEN has hookSpecificOutput
    [Tags]    unit    hooks    healthcheck    output    structure
    ${result}=    Healthcheck Has Hook Specific Output
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[has_hook_output]
    Should Be True    ${result}[has_context]

Healthcheck Completes Within Timeout
    [Documentation]    GIVEN healthcheck WHEN run THEN completes in 5s
    [Tags]    unit    hooks    healthcheck    timeout    performance
    ${result}=    Healthcheck Completes Within Timeout
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[within_5s]
    Should Be True    ${result}[exit_zero]

Healthcheck Exits Zero Always
    [Documentation]    GIVEN healthcheck WHEN services down THEN exits 0
    [Tags]    unit    hooks    healthcheck    exit    graceful
    ${result}=    Healthcheck Exits Zero Always
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[exit_zero]

# =============================================================================
# Healthcheck State Management Tests
# =============================================================================

State File Created
    [Documentation]    GIVEN healthcheck WHEN run THEN creates state file
    [Tags]    unit    hooks    healthcheck    state    file
    ${result}=    State File Created
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[exists]
    Should Be True    ${result}[has_master_hash]
    Should Be True    ${result}[has_last_check]

Unchanged State Triggers Summary
    [Documentation]    GIVEN unchanged state WHEN run THEN returns summary
    [Tags]    unit    hooks    healthcheck    state    unchanged
    ${result}=    Unchanged State Triggers Summary
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[summary_or_unchanged]

Retry Ceiling After 30 Seconds
    [Documentation]    GIVEN 30s unchanged WHEN run THEN stable output
    [Tags]    unit    hooks    healthcheck    state    ceiling
    ${result}=    Retry Ceiling After 30 Seconds
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[stable_output]

# =============================================================================
# Healthcheck Service Detection Tests
# =============================================================================

Detects Docker Status
    [Documentation]    GIVEN healthcheck WHEN run THEN detects container runtime
    [Tags]    unit    hooks    healthcheck    docker    detect
    ${result}=    Detects Docker Status
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[detected]

Provides Recovery Hint When Down
    [Documentation]    GIVEN services down WHEN run THEN provides hint
    [Tags]    unit    hooks    healthcheck    recovery    hint
    ${result}=    Provides Recovery Hint When Down
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[has_hint]

# =============================================================================
# Healthcheck Non-Blocking Tests
# =============================================================================

Subprocess Timeout Protection
    [Documentation]    GIVEN healthcheck WHEN inspect THEN all subprocess have timeout
    [Tags]    unit    hooks    healthcheck    timeout    subprocess
    ${result}=    Subprocess Timeout Protection
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[all_have_timeout]

Socket Timeout Protection
    [Documentation]    GIVEN healthcheck WHEN inspect THEN sockets have timeout
    [Tags]    unit    hooks    healthcheck    timeout    socket
    ${result}=    Socket Timeout Protection
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[has_timeout]

Global Timeout Wrapper
    [Documentation]    GIVEN healthcheck WHEN inspect THEN has global timeout
    [Tags]    unit    hooks    healthcheck    timeout    global
    ${result}=    Global Timeout Wrapper
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[has_protection]

# =============================================================================
# Frankel Hash Tests
# =============================================================================

Hash Deterministic
    [Documentation]    GIVEN same input WHEN hash THEN same output
    [Tags]    unit    hooks    frankel    hash    deterministic
    ${result}=    Hash Deterministic
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    compute_frankel_hash not available
    Should Be True    ${result}[deterministic]

Hash Changes On State Change
    [Documentation]    GIVEN different state WHEN hash THEN different output
    [Tags]    unit    hooks    frankel    hash    change
    ${result}=    Hash Changes On State Change
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    compute_frankel_hash not available
    Should Be True    ${result}[different]

Hash Is 8 Chars
    [Documentation]    GIVEN data WHEN hash THEN 8 uppercase hex chars
    [Tags]    unit    hooks    frankel    hash    format
    ${result}=    Hash Is 8 Chars
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    compute_frankel_hash not available
    Should Be True    ${result}[len_8]
    Should Be True    ${result}[is_upper]
    Should Be True    ${result}[all_hex]

# =============================================================================
# Entropy Monitor Output Tests
# =============================================================================

Entropy Returns Valid JSON
    [Documentation]    GIVEN entropy monitor WHEN run THEN returns valid JSON
    [Tags]    unit    hooks    entropy    output    json
    ${result}=    Entropy Returns Valid JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[valid_json]

Entropy Exits Zero Always
    [Documentation]    GIVEN entropy monitor WHEN error THEN exits 0
    [Tags]    unit    hooks    entropy    exit    graceful
    ${result}=    Entropy Exits Zero Always
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[exit_zero]

Entropy Status Command
    [Documentation]    GIVEN --status WHEN run THEN returns entropy state
    [Tags]    unit    hooks    entropy    status    command
    ${result}=    Entropy Status Command
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[has_hook_output]
    Should Be True    ${result}[has_entropy_or_tools]

# =============================================================================
# Entropy Monitor State Management Tests
# =============================================================================

Entropy State File Created
    [Documentation]    GIVEN entropy monitor WHEN run THEN creates state file
    [Tags]    unit    hooks    entropy    state    file
    ${result}=    Entropy State File Created
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[exists]
    Should Be True    ${result}[has_session_start]
    Should Be True    ${result}[has_tool_count]

State Has Audit Trail Fields
    [Documentation]    GIVEN entropy state WHEN check THEN has audit fields
    [Tags]    unit    hooks    entropy    state    audit
    ${result}=    State Has Audit Trail Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[has_session_hash]
    Should Be True    ${result}[has_check_count]
    Should Be True    ${result}[has_history]

Session Hash Is 4 Chars
    [Documentation]    GIVEN session hash WHEN check THEN 4 uppercase hex
    [Tags]    unit    hooks    entropy    hash    format
    ${result}=    Session Hash Is 4 Chars
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[len_4]
    Should Be True    ${result}[valid_hex]
    Should Be True    ${result}[is_upper]

Check Count Increments
    [Documentation]    GIVEN entropy monitor WHEN run THEN check_count increments
    [Tags]    unit    hooks    entropy    state    increment
    ${result}=    Check Count Increments
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[incremented]

Reset Creates History Entry
    [Documentation]    GIVEN --reset WHEN run THEN creates SESSION_RESET entry
    [Tags]    unit    hooks    entropy    reset    history
    ${result}=    Reset Creates History Entry
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[has_history]
    Should Be True    ${result}[has_reset_event]

Tool Count Increments
    [Documentation]    GIVEN entropy monitor WHEN run THEN tool_count increments
    [Tags]    unit    hooks    entropy    tool    increment
    ${result}=    Tool Count Increments
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[incremented]

# =============================================================================
# Entropy Monitor Warning Tests
# =============================================================================

No Warning Below Threshold
    [Documentation]    GIVEN tool_count < 50 WHEN run THEN no warning
    [Tags]    unit    hooks    entropy    warning    below
    ${result}=    No Warning Below Threshold
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[no_warning]

Low Threshold Warning
    [Documentation]    GIVEN tool_count = 50 WHEN run THEN shows warning
    [Tags]    unit    hooks    entropy    warning    low
    ${result}=    Low Threshold Warning
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[has_warning]

High Threshold Warning
    [Documentation]    GIVEN tool_count = 100 WHEN run THEN strong warning
    [Tags]    unit    hooks    entropy    warning    high
    ${result}=    High Threshold Warning
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[has_warning]

# =============================================================================
# Entropy Monitor Non-Blocking Tests
# =============================================================================

Entropy Completes Quickly
    [Documentation]    GIVEN entropy monitor WHEN run THEN completes in 1s
    [Tags]    unit    hooks    entropy    timeout    performance
    ${result}=    Entropy Completes Quickly
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[within_1s]
    Should Be True    ${result}[exit_zero]

Graceful On Corrupt State
    [Documentation]    GIVEN corrupt state WHEN run THEN handles gracefully
    [Tags]    unit    hooks    entropy    corrupt    graceful
    ${result}=    Graceful On Corrupt State
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[exit_zero]
    Should Be True    ${result}[valid_json]

# =============================================================================
# Module Import Tests
# =============================================================================

Core Module Imports
    [Documentation]    GIVEN hooks.core WHEN import THEN no errors
    [Tags]    unit    hooks    module    core    import
    ${result}=    Core Module Imports
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Core module not implemented
    Should Be True    ${result}[hook_config]
    Should Be True    ${result}[hook_result]
    Should Be True    ${result}[output_formatter]

Checkers Module Imports
    [Documentation]    GIVEN hooks.checkers WHEN import THEN no errors
    [Tags]    unit    hooks    module    checkers    import
    ${result}=    Checkers Module Imports
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Checkers module not implemented
    Should Be True    ${result}[service_checker]
    Should Be True    ${result}[entropy_checker]
    Should Be True    ${result}[amnesia_detector]

Recovery Module Imports
    [Documentation]    GIVEN hooks.recovery WHEN import THEN no errors
    [Tags]    unit    hooks    module    recovery    import
    ${result}=    Recovery Module Imports
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Recovery module not implemented
    Should Be True    ${result}[docker_recovery]

# =============================================================================
# E2E Claude Code Compatibility Tests
# =============================================================================

Hooks Produce Claude Code Compatible Output
    [Documentation]    GIVEN healthcheck WHEN run THEN Claude Code compatible
    [Tags]    e2e    hooks    compatibility    claude    output
    ${result}=    Hooks Produce Claude Code Compatible Output
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[exit_zero]
    Should Be True    ${result}[valid_json]
    Should Be True    ${result}[has_hook_output]
    Should Be True    ${result}[has_context]

Entropy Produces Claude Code Compatible Output
    [Documentation]    GIVEN entropy monitor WHEN run THEN Claude Code compatible
    [Tags]    e2e    hooks    compatibility    claude    entropy
    ${result}=    Entropy Produces Claude Code Compatible Output
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    entropy_monitor.py not implemented
    Should Be True    ${result}[exit_zero]
    Should Be True    ${result}[valid_json]

Hooks Handle Concurrent Execution
    [Documentation]    GIVEN concurrent runs WHEN execute THEN all succeed
    [Tags]    e2e    hooks    concurrent    stress    execution
    ${result}=    Hooks Handle Concurrent Execution
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[all_success]
    Should Be True    ${result}[all_valid_json]

Hooks State Isolation
    [Documentation]    GIVEN rapid writes WHEN execute THEN state valid
    [Tags]    e2e    hooks    state    isolation    integrity
    ${result}=    Hooks State Isolation
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    healthcheck.py not implemented
    Should Be True    ${result}[valid_json]
    Should Be True    ${result}[has_master_hash]
    Should Be True    ${result}[has_check_count]
