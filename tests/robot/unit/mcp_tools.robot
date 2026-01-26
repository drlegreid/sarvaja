*** Settings ***
Documentation    MCP Tools Tests
...              Per P4.1: MCP → Agno @tool Wrapper
...              Migrated from tests/test_mcp_tools.py
Library          Collections
Library          ../../libs/MCPToolsLibrary.py
Resource         ../resources/common.resource
Tags             unit    mcp    tools

*** Test Cases ***
# =============================================================================
# GovernanceTools Unit Tests
# =============================================================================

Test Governance Tools Class Exists
    [Documentation]    GovernanceTools class exists and is importable
    [Tags]    governance
    ${result}=    Governance Tools Class Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}

Test Governance Tools Is Toolkit
    [Documentation]    GovernanceTools inherits from Toolkit
    [Tags]    governance
    ${result}=    Governance Tools Is Toolkit
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_toolkit']}

Test Governance Tools Has Name
    [Documentation]    GovernanceTools has toolkit name
    [Tags]    governance
    ${result}=    Governance Tools Has Name
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['name_correct']}

Test Governance Config Defaults
    [Documentation]    GovernanceConfig has sensible defaults
    [Tags]    config
    ${result}=    Governance Config Defaults
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['host_default']}
    Should Be True    ${result['port_default']}
    Should Be True    ${result['db_default']}

Test Governance Config Custom
    [Documentation]    GovernanceConfig accepts custom values
    [Tags]    config
    ${result}=    Governance Config Custom
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['host_custom']}
    Should Be True    ${result['port_custom']}
    Should Be True    ${result['db_custom']}

# =============================================================================
# Method Existence Tests
# =============================================================================

Test Query Rules Method Exists
    [Documentation]    query_rules method exists
    [Tags]    methods
    ${result}=    Query Rules Method Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_method']}
    Should Be True    ${result['is_callable']}

Test Get Rule Method Exists
    [Documentation]    get_rule method exists
    [Tags]    methods
    ${result}=    Get Rule Method Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_method']}
    Should Be True    ${result['is_callable']}

Test Get Dependencies Method Exists
    [Documentation]    get_dependencies method exists
    [Tags]    methods
    ${result}=    Get Dependencies Method Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_method']}
    Should Be True    ${result['is_callable']}

Test Find Conflicts Method Exists
    [Documentation]    find_conflicts method exists
    [Tags]    methods
    ${result}=    Find Conflicts Method Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_method']}
    Should Be True    ${result['is_callable']}

Test Get Trust Score Method Exists
    [Documentation]    get_trust_score method exists
    [Tags]    methods
    ${result}=    Get Trust Score Method Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_method']}
    Should Be True    ${result['is_callable']}

Test List Agents Method Exists
    [Documentation]    list_agents method exists
    [Tags]    methods
    ${result}=    List Agents Method Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_method']}
    Should Be True    ${result['is_callable']}

Test Health Check Method Exists
    [Documentation]    health_check method exists
    [Tags]    methods
    ${result}=    Health Check Method Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_method']}
    Should Be True    ${result['is_callable']}

# =============================================================================
# Return Format Tests
# =============================================================================

Test Query Rules Returns JSON
    [Documentation]    query_rules returns JSON string
    [Tags]    return_format
    ${result}=    Query Rules Returns JSON
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['valid_json']}

Test Get Rule Returns JSON
    [Documentation]    get_rule returns JSON string
    [Tags]    return_format
    ${result}=    Get Rule Returns JSON
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['valid_json']}

Test Health Check Returns JSON
    [Documentation]    health_check returns JSON string
    [Tags]    return_format
    ${result}=    Health Check Returns JSON
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['valid_json']}
    Should Be True    ${result['has_status']}

# =============================================================================
# Convenience Function Tests
# =============================================================================

Test Create Governance Tools Exists
    [Documentation]    create_governance_tools function exists
    [Tags]    convenience
    ${result}=    Create Governance Tools Exists
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['exists']}
    Should Be True    ${result['callable']}

Test Create Governance Tools Returns Toolkit
    [Documentation]    create_governance_tools returns GovernanceTools instance
    [Tags]    convenience
    ${result}=    Create Governance Tools Returns Toolkit
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_instance']}

Test Create Governance Tools With Custom Config
    [Documentation]    create_governance_tools accepts custom config
    [Tags]    convenience
    ${result}=    Create Governance Tools With Custom Config
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['host_custom']}
    Should Be True    ${result['port_custom']}
    Should Be True    ${result['db_custom']}

# =============================================================================
# Tool Decorator Tests
# =============================================================================

Test Query Rules Has Tool Metadata
    [Documentation]    query_rules has tool metadata
    [Tags]    decorator
    ${result}=    Query Rules Has Tool Metadata
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_metadata']}

Test All Seven Tools Registered
    [Documentation]    All seven tools are registered in toolkit
    [Tags]    decorator
    ${result}=    All Seven Tools Registered
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['count_correct']}

# =============================================================================
# Health Response Structure Tests (GAP-MCP-002)
# =============================================================================

Test Health Response Structure
    [Documentation]    Health check response has required GAP-MCP-002 fields
    [Tags]    health    gap-mcp-002
    ${result}=    Health Response Structure
    Should Be True    ${result['unhealthy_fields_ok']}
    Should Be True    ${result['healthy_fields_ok']}

Test Action Required Pattern For Claude Code
    [Documentation]    action_required: START_SERVICES triggers Claude Code recovery
    [Tags]    health    gap-mcp-002
    ${result}=    Action Required Pattern For Claude Code
    Should Be True    ${result['action_start_services']}
    Should Be True    ${result['has_typedb']}
    Should Be True    ${result['has_chromadb']}
    Should Be True    ${result['has_docker_command']}
    Should Be True    ${result['hint_has_typedb']}
    Should Be True    ${result['hint_has_chromadb']}

# =============================================================================
# Vote Weight Calculation Tests
# =============================================================================

Test High Trust Gets Full Weight
    [Documentation]    High trust agents (>= 0.5) get vote weight of 1.0
    [Tags]    trust    vote_weight
    ${result}=    High Trust Gets Full Weight
    Should Be True    ${result['full_weight']}

Test Low Trust Gets Reduced Weight
    [Documentation]    Low trust agents (< 0.5) get vote weight equal to trust score
    [Tags]    trust    vote_weight
    ${result}=    Low Trust Gets Reduced Weight
    Should Be True    ${result['reduced_weight']}

Test Boundary Trust At Half
    [Documentation]    Trust score exactly at 0.5 gets full weight
    [Tags]    trust    vote_weight
    ${result}=    Boundary Trust At Half
    Should Be True    ${result['boundary_full']}

Test Very Low Trust Weight
    [Documentation]    Very low trust (0.1) gets proportional weight
    [Tags]    trust    vote_weight
    ${result}=    Very Low Trust Weight
    Should Be True    ${result['proportional']}
