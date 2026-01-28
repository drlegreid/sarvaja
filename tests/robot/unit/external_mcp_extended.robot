*** Settings ***
Documentation    RF-004: External MCP Extended Tests (Combined, DesktopCommander, OctoCode, Playwright, PowerShell)
...              Migrated from test_external_mcp_tools.py
...              Per RF-007 Robot Framework Migration
Library          ../../libs/ExternalMCPCombinedLibrary.py
Library          ../../libs/ExternalMCPDesktopCommanderLibrary.py
Library          ../../libs/ExternalMCPOctoCodeLibrary.py
Library          ../../libs/ExternalMCPPlaywrightLibrary.py
Library          ../../libs/ExternalMCPPowerShellLibrary.py
Library          Collections
Resource         ../resources/common.resource
Force Tags             unit    mcp    external    extended    low    validate    ARCH-MCP-02-v1

*** Test Cases ***
# =============================================================================
# Combined Toolkit Tests
# =============================================================================

Combined Toolkit Creation
    [Documentation]    Test: Combined Toolkit Creation
    ${result}=    Combined Toolkit Creation
    Skip If Import Failed    ${result}

All Toolkits Enabled
    [Documentation]    Test: All Toolkits Enabled
    ${result}=    All Toolkits Enabled
    Skip If Import Failed    ${result}

Selective Toolkits
    [Documentation]    Test: Selective Toolkits
    ${result}=    Selective Toolkits
    Skip If Import Failed    ${result}

Prefixed Tool Names
    [Documentation]    Test: Prefixed Tool Names
    ${result}=    Prefixed Tool Names
    Skip If Import Failed    ${result}

Total Tool Count
    [Documentation]    Test: Total Tool Count
    ${result}=    Total Tool Count
    Skip If Import Failed    ${result}

Disabled Toolkit Not Registered
    [Documentation]    Test: Disabled Toolkit Not Registered
    ${result}=    Disabled Toolkit Not Registered
    Skip If Import Failed    ${result}

Get All External Tools
    [Documentation]    Test: Get All External Tools
    ${result}=    Get All External Tools
    Skip If Import Failed    ${result}

Get Web Automation Tools
    [Documentation]    Test: Get Web Automation Tools
    ${result}=    Get Web Automation Tools
    Skip If Import Failed    ${result}

Get DevOps Tools
    [Documentation]    Test: Get DevOps Tools
    ${result}=    Get DevOps Tools
    Skip If Import Failed    ${result}

Get File Tools
    [Documentation]    Test: Get File Tools
    ${result}=    Get File Tools
    Skip If Import Failed    ${result}

Get Code Research Tools
    [Documentation]    Test: Get Code Research Tools
    ${result}=    Get Code Research Tools
    Skip If Import Failed    ${result}

AGNO Available Flag
    [Documentation]    Test: AGNO Available Flag
    ${result}=    AGNO Available Flag
    Skip If Import Failed    ${result}

Stub Decorator When No AGNO
    [Documentation]    Test: Stub Decorator When No AGNO
    ${result}=    Stub Decorator When No AGNO
    Skip If Import Failed    ${result}

All Tools Return Valid JSON
    [Documentation]    Test: All Tools Return Valid JSON
    ${result}=    All Tools Return Valid JSON
    Skip If Import Failed    ${result}

Results Have Action Field
    [Documentation]    Test: Results Have Action Field
    ${result}=    Results Have Action Field
    Skip If Import Failed    ${result}

Results Have Message Field
    [Documentation]    Test: Results Have Message Field
    ${result}=    Results Have Message Field
    Skip If Import Failed    ${result}

Tier 1 Tools Present
    [Documentation]    Test: Tier 1 Tools Present
    ${result}=    Tier 1 Tools Present
    Skip If Import Failed    ${result}

Tier 2 Tools Present
    [Documentation]    Test: Tier 2 Tools Present
    ${result}=    Tier 2 Tools Present
    Skip If Import Failed    ${result}

# =============================================================================
# Desktop Commander Tests
# =============================================================================

Desktop Commander Default Config
    [Documentation]    Test: Desktop Commander Default Config
    ${result}=    Desktop Commander Default Config
    Skip If Import Failed    ${result}

Desktop Commander Custom Config
    [Documentation]    Test: Desktop Commander Custom Config
    ${result}=    Desktop Commander Custom Config
    Skip If Import Failed    ${result}

Desktop Commander Toolkit Creation
    [Documentation]    Test: Desktop Commander Toolkit Creation
    ${result}=    Desktop Commander Toolkit Creation
    Skip If Import Failed    ${result}

Desktop Commander Tool Registration
    [Documentation]    Test: Desktop Commander Tool Registration
    ${result}=    Desktop Commander Tool Registration
    Skip If Import Failed    ${result}

Desktop Commander Read File Tool
    [Documentation]    Test: Desktop Commander Read File Tool
    ${result}=    Desktop Commander Read File Tool
    Skip If Import Failed    ${result}

Desktop Commander Write File Tool
    [Documentation]    Test: Desktop Commander Write File Tool
    ${result}=    Desktop Commander Write File Tool
    Skip If Import Failed    ${result}

Desktop Commander List Directory Tool
    [Documentation]    Test: Desktop Commander List Directory Tool
    ${result}=    Desktop Commander List Directory Tool
    Skip If Import Failed    ${result}

Desktop Commander Search Files Tool
    [Documentation]    Test: Desktop Commander Search Files Tool
    ${result}=    Desktop Commander Search Files Tool
    Skip If Import Failed    ${result}

Desktop Commander Search Content
    [Documentation]    Test: Desktop Commander Search Content
    ${result}=    Desktop Commander Search Content
    Skip If Import Failed    ${result}

Desktop Commander Get File Info Tool
    [Documentation]    Test: Desktop Commander Get File Info Tool
    ${result}=    Desktop Commander Get File Info Tool
    Skip If Import Failed    ${result}

Desktop Commander Create Directory Tool
    [Documentation]    Test: Desktop Commander Create Directory Tool
    ${result}=    Desktop Commander Create Directory Tool
    Skip If Import Failed    ${result}

Desktop Commander Move File Tool
    [Documentation]    Test: Desktop Commander Move File Tool
    ${result}=    Desktop Commander Move File Tool
    Skip If Import Failed    ${result}

# =============================================================================
# OctoCode Tests
# =============================================================================

OctoCode Default Config
    [Documentation]    Test: OctoCode Default Config
    ${result}=    OctoCode Default Config
    Skip If Import Failed    ${result}

OctoCode Custom Config
    [Documentation]    Test: OctoCode Custom Config
    ${result}=    OctoCode Custom Config
    Skip If Import Failed    ${result}

OctoCode Toolkit Creation
    [Documentation]    Test: OctoCode Toolkit Creation
    ${result}=    OctoCode Toolkit Creation
    Skip If Import Failed    ${result}

OctoCode Tool Registration
    [Documentation]    Test: OctoCode Tool Registration
    ${result}=    OctoCode Tool Registration
    Skip If Import Failed    ${result}

OctoCode Search Code Tool
    [Documentation]    Test: OctoCode Search Code Tool
    ${result}=    OctoCode Search Code Tool
    Skip If Import Failed    ${result}

OctoCode Search Code No Owner
    [Documentation]    Test: OctoCode Search Code No Owner
    ${result}=    OctoCode Search Code No Owner
    Skip If Import Failed    ${result}

OctoCode Get File Content Tool
    [Documentation]    Test: OctoCode Get File Content Tool
    ${result}=    OctoCode Get File Content Tool
    Skip If Import Failed    ${result}

OctoCode Get File Content With Match
    [Documentation]    Test: OctoCode Get File Content With Match
    ${result}=    OctoCode Get File Content With Match
    Skip If Import Failed    ${result}

OctoCode View Repo Structure Tool
    [Documentation]    Test: OctoCode View Repo Structure Tool
    ${result}=    OctoCode View Repo Structure Tool
    Skip If Import Failed    ${result}

OctoCode Search Repositories Tool
    [Documentation]    Test: OctoCode Search Repositories Tool
    ${result}=    OctoCode Search Repositories Tool
    Skip If Import Failed    ${result}

OctoCode Search Pull Requests Tool
    [Documentation]    Test: OctoCode Search Pull Requests Tool
    ${result}=    OctoCode Search Pull Requests Tool
    Skip If Import Failed    ${result}

OctoCode Search Pull Requests Open
    [Documentation]    Test: OctoCode Search Pull Requests Open
    ${result}=    OctoCode Search Pull Requests Open
    Skip If Import Failed    ${result}

# =============================================================================
# Playwright Tests
# =============================================================================

Playwright Default Config
    [Documentation]    Test: Playwright Default Config
    ${result}=    Playwright Default Config
    Skip If Import Failed    ${result}

Playwright Custom Config
    [Documentation]    Test: Playwright Custom Config
    ${result}=    Playwright Custom Config
    Skip If Import Failed    ${result}

Playwright Toolkit Creation
    [Documentation]    Test: Playwright Toolkit Creation
    ${result}=    Playwright Toolkit Creation
    Skip If Import Failed    ${result}

Playwright Toolkit With Config
    [Documentation]    Test: Playwright Toolkit With Config
    ${result}=    Playwright Toolkit With Config
    Skip If Import Failed    ${result}

Playwright Tool Registration
    [Documentation]    Test: Playwright Tool Registration
    ${result}=    Playwright Tool Registration
    Skip If Import Failed    ${result}

Playwright Navigate Tool
    [Documentation]    Test: Playwright Navigate Tool
    ${result}=    Playwright Navigate Tool
    Skip If Import Failed    ${result}

Playwright Snapshot Tool
    [Documentation]    Test: Playwright Snapshot Tool
    ${result}=    Playwright Snapshot Tool
    Skip If Import Failed    ${result}

Playwright Click Tool
    [Documentation]    Test: Playwright Click Tool
    ${result}=    Playwright Click Tool
    Skip If Import Failed    ${result}

Playwright Type Text Tool
    [Documentation]    Test: Playwright Type Text Tool
    ${result}=    Playwright Type Text Tool
    Skip If Import Failed    ${result}

Playwright Screenshot Tool
    [Documentation]    Test: Playwright Screenshot Tool
    ${result}=    Playwright Screenshot Tool
    Skip If Import Failed    ${result}

Playwright Evaluate Tool
    [Documentation]    Test: Playwright Evaluate Tool
    ${result}=    Playwright Evaluate Tool
    Skip If Import Failed    ${result}

Playwright Wait For Text
    [Documentation]    Test: Playwright Wait For Text
    ${result}=    Playwright Wait For Text
    Skip If Import Failed    ${result}

Playwright Wait For Time
    [Documentation]    Test: Playwright Wait For Time
    ${result}=    Playwright Wait For Time
    Skip If Import Failed    ${result}

# =============================================================================
# PowerShell Tests
# =============================================================================

PowerShell Default Config
    [Documentation]    Test: PowerShell Default Config
    ${result}=    PowerShell Default Config
    Skip If Import Failed    ${result}

PowerShell Custom Config
    [Documentation]    Test: PowerShell Custom Config
    ${result}=    PowerShell Custom Config
    Skip If Import Failed    ${result}

PowerShell Toolkit Creation
    [Documentation]    Test: PowerShell Toolkit Creation
    ${result}=    PowerShell Toolkit Creation
    Skip If Import Failed    ${result}

PowerShell Tool Registration
    [Documentation]    Test: PowerShell Tool Registration
    ${result}=    PowerShell Tool Registration
    Skip If Import Failed    ${result}

PowerShell Run Script Tool
    [Documentation]    Test: PowerShell Run Script Tool
    ${result}=    PowerShell Run Script Tool
    Skip If Import Failed    ${result}

PowerShell Run Script With Timeout
    [Documentation]    Test: PowerShell Run Script With Timeout
    ${result}=    PowerShell Run Script With Timeout
    Skip If Import Failed    ${result}

PowerShell Run Command Tool
    [Documentation]    Test: PowerShell Run Command Tool
    ${result}=    PowerShell Run Command Tool
    Skip If Import Failed    ${result}
