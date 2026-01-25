*** Settings ***
Documentation    RF-004: Unit Tests - MCP Agents Tools
...              Migrated from tests/test_mcp_agents.py
...              Per P10.4: Agent CRUD MCP tools
Library          Collections
Library          ../../libs/MCPAgentsLibrary.py

*** Test Cases ***
# =============================================================================
# Tools Existence Tests
# =============================================================================

Agents Tools Importable
    [Documentation]    GIVEN mcp_tools.agents WHEN import THEN works
    [Tags]    unit    mcp    agents    tools    import
    ${result}=    Agents Tools Importable
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Agents tools not yet implemented
    Should Be True    ${result}[importable]

Agents Tools Registered
    [Documentation]    GIVEN mcp_tools WHEN check THEN register_agent_tools exported
    [Tags]    unit    mcp    agents    tools    register
    ${result}=    Agents Tools Registered
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    register_agent_tools not exported
    Should Be True    ${result}[registered]

# =============================================================================
# Create Agent Tests
# =============================================================================

Create Agent Tool Exists
    [Documentation]    GIVEN compat WHEN check THEN governance_create_agent callable
    [Tags]    unit    mcp    agents    create    exists
    ${result}=    Create Agent Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_create_agent not yet exported
    Should Be True    ${result}[exists]

Create Agent Returns JSON
    [Documentation]    GIVEN agent data WHEN create THEN valid JSON
    [Tags]    integration    mcp    agents    create    json
    ${result}=    Create Agent Returns JSON
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_create_agent not yet exported
    Should Be True    ${result}[is_dict]

# =============================================================================
# Read Agent Tests
# =============================================================================

Get Agent Tool Exists
    [Documentation]    GIVEN compat WHEN check THEN governance_get_agent callable
    [Tags]    unit    mcp    agents    get    exists
    ${result}=    Get Agent Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_get_agent not yet exported
    Should Be True    ${result}[exists]

List Agents Tool Exists
    [Documentation]    GIVEN compat WHEN check THEN governance_list_agents callable
    [Tags]    unit    mcp    agents    list    exists
    ${result}=    List Agents Tool Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_list_agents not yet exported
    Should Be True    ${result}[exists]

# =============================================================================
# Update Agent Tests
# =============================================================================

Update Agent Trust Exists
    [Documentation]    GIVEN compat WHEN check THEN governance_update_agent_trust callable
    [Tags]    unit    mcp    agents    update    trust
    ${result}=    Update Agent Trust Exists
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    governance_update_agent_trust not yet exported
    Should Be True    ${result}[exists]

# =============================================================================
# TypeDB Operations Tests
# =============================================================================

Client Has Agent Operations
    [Documentation]    GIVEN TypeDBClient WHEN check THEN has agent CRUD
    [Tags]    integration    mcp    agents    typedb    operations
    ${result}=    Client Has Agent Operations
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    TypeDBClient not available
    Should Be True    ${result}[has_insert_agent]
    Should Be True    ${result}[has_get_agent]
    Should Be True    ${result}[has_get_all_agents]
    Should Be True    ${result}[has_update_agent_trust]

Get All Agents From TypeDB
    [Documentation]    GIVEN TypeDB WHEN get_all_agents THEN returns list
    [Tags]    integration    mcp    agents    typedb    query
    ${result}=    Get All Agents From TypeDB
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Cannot connect to TypeDB or not implemented
    Should Be True    ${result}[is_list]
