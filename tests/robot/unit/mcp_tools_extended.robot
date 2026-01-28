*** Settings ***
Documentation    RF-004: MCP Tools Extended Tests (Health, Unit)
...              Migrated from test_mcp_server_split.py
...              Per RF-007 Robot Framework Migration
Library          ../../libs/MCPToolsHealthLibrary.py
Library          ../../libs/MCPToolsUnitLibrary.py
Library          Collections
Resource         ../resources/common.resource
Force Tags             unit    mcp    tools    extended    low    validate    ARCH-MCP-02-v1

*** Test Cases ***
# =============================================================================
# Health Response Tests
# =============================================================================

Health Response Structure
    [Documentation]    Test: Health Response Structure
    ${result}=    Health Response Structure
    Skip If Import Failed    ${result}

Action Required Pattern For Claude Code
    [Documentation]    Test: Action Required Pattern For Claude Code
    ${result}=    Action Required Pattern For Claude Code
    Skip If Import Failed    ${result}

High Trust Gets Full Weight
    [Documentation]    Test: High Trust Gets Full Weight
    ${result}=    High Trust Gets Full Weight
    Skip If Import Failed    ${result}

Low Trust Gets Reduced Weight
    [Documentation]    Test: Low Trust Gets Reduced Weight
    ${result}=    Low Trust Gets Reduced Weight
    Skip If Import Failed    ${result}

Boundary Trust At Half
    [Documentation]    Test: Boundary Trust At Half
    ${result}=    Boundary Trust At Half
    Skip If Import Failed    ${result}

Very Low Trust Weight
    [Documentation]    Test: Very Low Trust Weight
    ${result}=    Very Low Trust Weight
    Skip If Import Failed    ${result}

# =============================================================================
# Unit Tests
# =============================================================================

Governance Tools Class Exists
    [Documentation]    Test: Governance Tools Class Exists
    ${result}=    Governance Tools Class Exists
    Skip If Import Failed    ${result}

Governance Tools Is Toolkit
    [Documentation]    Test: Governance Tools Is Toolkit
    ${result}=    Governance Tools Is Toolkit
    Skip If Import Failed    ${result}

Governance Tools Has Name
    [Documentation]    Test: Governance Tools Has Name
    ${result}=    Governance Tools Has Name
    Skip If Import Failed    ${result}

Governance Config Defaults
    [Documentation]    Test: Governance Config Defaults
    ${result}=    Governance Config Defaults
    Skip If Import Failed    ${result}

Governance Config Custom
    [Documentation]    Test: Governance Config Custom
    ${result}=    Governance Config Custom
    Skip If Import Failed    ${result}

Query Rules Method Exists
    [Documentation]    Test: Query Rules Method Exists
    ${result}=    Query Rules Method Exists
    Skip If Import Failed    ${result}

Get Rule Method Exists
    [Documentation]    Test: Get Rule Method Exists
    ${result}=    Get Rule Method Exists
    Skip If Import Failed    ${result}

Get Dependencies Method Exists
    [Documentation]    Test: Get Dependencies Method Exists
    ${result}=    Get Dependencies Method Exists
    Skip If Import Failed    ${result}

Find Conflicts Method Exists
    [Documentation]    Test: Find Conflicts Method Exists
    ${result}=    Find Conflicts Method Exists
    Skip If Import Failed    ${result}

Get Trust Score Method Exists
    [Documentation]    Test: Get Trust Score Method Exists
    ${result}=    Get Trust Score Method Exists
    Skip If Import Failed    ${result}

List Agents Method Exists
    [Documentation]    Test: List Agents Method Exists
    ${result}=    List Agents Method Exists
    Skip If Import Failed    ${result}

Health Check Method Exists
    [Documentation]    Test: Health Check Method Exists
    ${result}=    Health Check Method Exists
    Skip If Import Failed    ${result}

Query Rules Returns JSON
    [Documentation]    Test: Query Rules Returns JSON
    ${result}=    Query Rules Returns JSON
    Skip If Import Failed    ${result}

Get Rule Returns JSON
    [Documentation]    Test: Get Rule Returns JSON
    ${result}=    Get Rule Returns JSON
    Skip If Import Failed    ${result}

Health Check Returns JSON
    [Documentation]    Test: Health Check Returns JSON
    ${result}=    Health Check Returns JSON
    Skip If Import Failed    ${result}

Create Governance Tools Exists
    [Documentation]    Test: Create Governance Tools Exists
    ${result}=    Create Governance Tools Exists
    Skip If Import Failed    ${result}

Create Governance Tools Returns Toolkit
    [Documentation]    Test: Create Governance Tools Returns Toolkit
    ${result}=    Create Governance Tools Returns Toolkit
    Skip If Import Failed    ${result}

Create Governance Tools With Custom Config
    [Documentation]    Test: Create Governance Tools With Custom Config
    ${result}=    Create Governance Tools With Custom Config
    Skip If Import Failed    ${result}

Query Rules Has Tool Metadata
    [Documentation]    Test: Query Rules Has Tool Metadata
    ${result}=    Query Rules Has Tool Metadata
    Skip If Import Failed    ${result}

All Seven Tools Registered
    [Documentation]    Test: All Seven Tools Registered
    ${result}=    All Seven Tools Registered
    Skip If Import Failed    ${result}
