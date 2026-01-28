*** Settings ***
Documentation    External MCP Tools Tests
...              Per: RULE-007 (MCP Tool Matrix)
...              Migrated from tests/test_external_mcp_tools.py
Library          Collections
Library          ../../libs/ExternalMCPToolsLibrary.py
Resource         ../resources/common.resource
Force Tags             unit    mcp    external    rule-007    low    validate    ARCH-MCP-02-v1

*** Test Cases ***
# =============================================================================
# Playwright Config Tests (P5.1)
# =============================================================================

Test Playwright Default Config
    [Documentation]    Test default configuration values
    [Tags]    playwright    config
    ${result}=    Playwright Default Config
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['browser_chromium']}
    Should Be True    ${result['headless_true']}
    Should Be True    ${result['timeout_30000']}

Test Playwright Custom Config
    [Documentation]    Test custom configuration
    [Tags]    playwright    config
    ${result}=    Playwright Custom Config
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['browser_firefox']}
    Should Be True    ${result['headless_false']}
    Should Be True    ${result['timeout_60000']}

# =============================================================================
# Playwright Tools Tests
# =============================================================================

Test Playwright Toolkit Creation
    [Documentation]    Test toolkit can be created
    [Tags]    playwright    toolkit
    ${result}=    Playwright Toolkit Creation
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['name_correct']}
    Should Be True    ${result['config_exists']}

Test Playwright Toolkit With Config
    [Documentation]    Test toolkit with custom config
    [Tags]    playwright    toolkit
    ${result}=    Playwright Toolkit With Config
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['browser_webkit']}

Test Playwright Tool Registration
    [Documentation]    Test all tools are registered
    [Tags]    playwright    registration
    ${result}=    Playwright Tool Registration
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['navigate_registered']}
    Should Be True    ${result['snapshot_registered']}
    Should Be True    ${result['click_registered']}
    Should Be True    ${result['type_text_registered']}
    Should Be True    ${result['screenshot_registered']}
    Should Be True    ${result['evaluate_registered']}
    Should Be True    ${result['wait_for_registered']}

Test Playwright Navigate Tool
    [Documentation]    Test navigate tool returns valid JSON
    [Tags]    playwright    tool
    ${result}=    Playwright Navigate Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_navigate']}
    Should Be True    ${result['url_correct']}
    Should Be True    ${result['status_simulated']}

Test Playwright Snapshot Tool
    [Documentation]    Test snapshot tool returns valid JSON
    [Tags]    playwright    tool
    ${result}=    Playwright Snapshot Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_snapshot']}
    Should Be True    ${result['filename_correct']}

Test Playwright Click Tool
    [Documentation]    Test click tool returns valid JSON
    [Tags]    playwright    tool
    ${result}=    Playwright Click Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_click']}
    Should Be True    ${result['element_correct']}
    Should Be True    ${result['ref_correct']}

Test Playwright Type Text Tool
    [Documentation]    Test type_text tool returns valid JSON
    [Tags]    playwright    tool
    ${result}=    Playwright Type Text Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_type']}
    Should Be True    ${result['text_correct']}
    Should Be True    ${result['submit_true']}

Test Playwright Screenshot Tool
    [Documentation]    Test screenshot tool returns valid JSON
    [Tags]    playwright    tool
    ${result}=    Playwright Screenshot Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_screenshot']}
    Should Be True    ${result['full_page_true']}

Test Playwright Evaluate Tool
    [Documentation]    Test evaluate tool returns valid JSON
    [Tags]    playwright    tool
    ${result}=    Playwright Evaluate Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_evaluate']}
    Should Be True    ${result['function_correct']}

Test Playwright Wait For Text
    [Documentation]    Test wait_for with text
    [Tags]    playwright    tool
    ${result}=    Playwright Wait For Text
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_wait']}
    Should Be True    ${result['text_correct']}

Test Playwright Wait For Time
    [Documentation]    Test wait_for with time
    [Tags]    playwright    tool
    ${result}=    Playwright Wait For Time
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['time_correct']}

# =============================================================================
# PowerShell Tests (P5.2)
# =============================================================================

Test PowerShell Default Config
    [Documentation]    Test default configuration values
    [Tags]    powershell    config
    ${result}=    PowerShell Default Config
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['timeout_300']}
    Should Be True    ${result['working_directory_none']}

Test PowerShell Custom Config
    [Documentation]    Test custom configuration
    [Tags]    powershell    config
    ${result}=    PowerShell Custom Config
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['timeout_600']}
    Should Be True    ${result['working_directory_correct']}

Test PowerShell Toolkit Creation
    [Documentation]    Test toolkit can be created
    [Tags]    powershell    toolkit
    ${result}=    PowerShell Toolkit Creation
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['name_correct']}

Test PowerShell Tool Registration
    [Documentation]    Test all tools are registered
    [Tags]    powershell    registration
    ${result}=    PowerShell Tool Registration
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['run_script_registered']}
    Should Be True    ${result['run_command_registered']}

Test PowerShell Run Script Tool
    [Documentation]    Test run_script tool returns valid JSON
    [Tags]    powershell    tool
    ${result}=    PowerShell Run Script Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_run_script']}
    Should Be True    ${result['code_length_correct']}
    Should Be True    ${result['timeout_default']}

Test PowerShell Run Script With Timeout
    [Documentation]    Test run_script with custom timeout
    [Tags]    powershell    tool
    ${result}=    PowerShell Run Script With Timeout
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['timeout_custom']}

Test PowerShell Run Command Tool
    [Documentation]    Test run_command wraps run_script
    [Tags]    powershell    tool
    ${result}=    PowerShell Run Command Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_run_script']}

# =============================================================================
# Desktop Commander Tests (P5.3)
# =============================================================================

Test Desktop Commander Default Config
    [Documentation]    Test default configuration values
    [Tags]    desktop_commander    config
    ${result}=    Desktop Commander Default Config
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['allowed_directories_none']}
    Should Be True    ${result['file_read_limit_1000']}

Test Desktop Commander Custom Config
    [Documentation]    Test custom configuration
    [Tags]    desktop_commander    config
    ${result}=    Desktop Commander Custom Config
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['allowed_directories_count']}
    Should Be True    ${result['file_read_limit_500']}

Test Desktop Commander Toolkit Creation
    [Documentation]    Test toolkit can be created
    [Tags]    desktop_commander    toolkit
    ${result}=    Desktop Commander Toolkit Creation
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['name_correct']}

Test Desktop Commander Tool Registration
    [Documentation]    Test all tools are registered
    [Tags]    desktop_commander    registration
    ${result}=    Desktop Commander Tool Registration
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['read_file_registered']}
    Should Be True    ${result['write_file_registered']}
    Should Be True    ${result['list_directory_registered']}
    Should Be True    ${result['search_files_registered']}
    Should Be True    ${result['get_file_info_registered']}
    Should Be True    ${result['create_directory_registered']}
    Should Be True    ${result['move_file_registered']}

Test Desktop Commander Read File Tool
    [Documentation]    Test read_file tool returns valid JSON
    [Tags]    desktop_commander    tool
    ${result}=    Desktop Commander Read File Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_read_file']}
    Should Be True    ${result['path_correct']}
    Should Be True    ${result['offset_correct']}
    Should Be True    ${result['length_correct']}

Test Desktop Commander Write File Tool
    [Documentation]    Test write_file tool returns valid JSON
    [Tags]    desktop_commander    tool
    ${result}=    Desktop Commander Write File Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_write_file']}
    Should Be True    ${result['content_length_11']}
    Should Be True    ${result['mode_append']}

Test Desktop Commander List Directory Tool
    [Documentation]    Test list_directory tool returns valid JSON
    [Tags]    desktop_commander    tool
    ${result}=    Desktop Commander List Directory Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_list_directory']}
    Should Be True    ${result['path_correct']}
    Should Be True    ${result['depth_1']}

Test Desktop Commander Search Files Tool
    [Documentation]    Test search_files tool returns valid JSON
    [Tags]    desktop_commander    tool
    ${result}=    Desktop Commander Search Files Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_search']}
    Should Be True    ${result['pattern_py']}
    Should Be True    ${result['search_type_files']}

Test Desktop Commander Search Content
    [Documentation]    Test search_files for content
    [Tags]    desktop_commander    tool
    ${result}=    Desktop Commander Search Content
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['search_type_content']}

Test Desktop Commander Get File Info Tool
    [Documentation]    Test get_file_info tool returns valid JSON
    [Tags]    desktop_commander    tool
    ${result}=    Desktop Commander Get File Info Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_get_file_info']}
    Should Be True    ${result['path_correct']}

Test Desktop Commander Create Directory Tool
    [Documentation]    Test create_directory tool returns valid JSON
    [Tags]    desktop_commander    tool
    ${result}=    Desktop Commander Create Directory Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_create_directory']}
    Should Be True    ${result['path_correct']}

Test Desktop Commander Move File Tool
    [Documentation]    Test move_file tool returns valid JSON
    [Tags]    desktop_commander    tool
    ${result}=    Desktop Commander Move File Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_move_file']}
    Should Be True    ${result['source_correct']}
    Should Be True    ${result['destination_correct']}

# =============================================================================
# OctoCode Tests (P5.4)
# =============================================================================

Test OctoCode Default Config
    [Documentation]    Test default configuration values
    [Tags]    octocode    config
    ${result}=    OctoCode Default Config
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['default_limit_10']}
    Should Be True    ${result['include_minified_true']}

Test OctoCode Custom Config
    [Documentation]    Test custom configuration
    [Tags]    octocode    config
    ${result}=    OctoCode Custom Config
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['default_limit_5']}
    Should Be True    ${result['include_minified_false']}

Test OctoCode Toolkit Creation
    [Documentation]    Test toolkit can be created
    [Tags]    octocode    toolkit
    ${result}=    OctoCode Toolkit Creation
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['name_correct']}

Test OctoCode Tool Registration
    [Documentation]    Test all tools are registered
    [Tags]    octocode    registration
    ${result}=    OctoCode Tool Registration
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['search_code_registered']}
    Should Be True    ${result['get_file_content_registered']}
    Should Be True    ${result['view_repo_structure_registered']}
    Should Be True    ${result['search_repositories_registered']}
    Should Be True    ${result['search_pull_requests_registered']}

Test OctoCode Search Code Tool
    [Documentation]    Test search_code tool returns valid JSON
    [Tags]    octocode    tool
    ${result}=    OctoCode Search Code Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_search_code']}
    Should Be True    ${result['keywords_correct']}
    Should Be True    ${result['owner_correct']}
    Should Be True    ${result['repo_correct']}
    Should Be True    ${result['match_file']}

Test OctoCode Search Code No Owner
    [Documentation]    Test search_code without owner/repo
    [Tags]    octocode    tool
    ${result}=    OctoCode Search Code No Owner
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['owner_none']}
    Should Be True    ${result['repo_none']}

Test OctoCode Get File Content Tool
    [Documentation]    Test get_file_content tool returns valid JSON
    [Tags]    octocode    tool
    ${result}=    OctoCode Get File Content Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_get_file_content']}
    Should Be True    ${result['owner_correct']}
    Should Be True    ${result['repo_correct']}
    Should Be True    ${result['path_correct']}
    Should Be True    ${result['branch_main']}

Test OctoCode Get File Content With Match
    [Documentation]    Test get_file_content with match_string
    [Tags]    octocode    tool
    ${result}=    OctoCode Get File Content With Match
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['match_string_correct']}

Test OctoCode View Repo Structure Tool
    [Documentation]    Test view_repo_structure tool returns valid JSON
    [Tags]    octocode    tool
    ${result}=    OctoCode View Repo Structure Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_view_structure']}
    Should Be True    ${result['owner_correct']}
    Should Be True    ${result['repo_correct']}
    Should Be True    ${result['path_src']}
    Should Be True    ${result['depth_2']}

Test OctoCode Search Repositories Tool
    [Documentation]    Test search_repositories tool returns valid JSON
    [Tags]    octocode    tool
    ${result}=    OctoCode Search Repositories Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_search_repos']}
    Should Be True    ${result['keywords_correct']}
    Should Be True    ${result['topics_correct']}
    Should Be True    ${result['stars_correct']}
    Should Be True    ${result['limit_5']}

Test OctoCode Search Pull Requests Tool
    [Documentation]    Test search_pull_requests tool returns valid JSON
    [Tags]    octocode    tool
    ${result}=    OctoCode Search Pull Requests Tool
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['action_search_prs']}
    Should Be True    ${result['owner_correct']}
    Should Be True    ${result['repo_correct']}
    Should Be True    ${result['query_correct']}
    Should Be True    ${result['state_closed']}

Test OctoCode Search Pull Requests Open
    [Documentation]    Test search_pull_requests for open PRs
    [Tags]    octocode    tool
    ${result}=    OctoCode Search Pull Requests Open
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['state_open']}

# =============================================================================
# Combined Toolkit Tests
# =============================================================================

Test Combined Toolkit Creation
    [Documentation]    Test combined toolkit can be created
    [Tags]    combined    toolkit
    ${result}=    Combined Toolkit Creation
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['name_correct']}

Test All Toolkits Enabled
    [Documentation]    Test all toolkits enabled by default
    [Tags]    combined    toolkit
    ${result}=    All Toolkits Enabled
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['playwright_enabled']}
    Should Be True    ${result['powershell_enabled']}
    Should Be True    ${result['desktop_commander_enabled']}
    Should Be True    ${result['octocode_enabled']}

Test Selective Toolkits
    [Documentation]    Test selective toolkit enabling
    [Tags]    combined    toolkit
    ${result}=    Selective Toolkits
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['playwright_enabled']}
    Should Be True    ${result['powershell_disabled']}
    Should Be True    ${result['desktop_commander_disabled']}
    Should Be True    ${result['octocode_enabled']}

Test Prefixed Tool Names
    [Documentation]    Test tools have prefixed names
    [Tags]    combined    toolkit
    ${result}=    Prefixed Tool Names
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['playwright_navigate']}
    Should Be True    ${result['powershell_run_script']}
    Should Be True    ${result['desktop_commander_read_file']}
    Should Be True    ${result['octocode_search_code']}

Test Total Tool Count
    [Documentation]    Test total number of registered tools
    [Tags]    combined    toolkit
    ${result}=    Total Tool Count
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['count_21']}

Test Disabled Toolkit Not Registered
    [Documentation]    Test disabled toolkit tools not registered
    [Tags]    combined    toolkit
    ${result}=    Disabled Toolkit Not Registered
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['powershell_not_in_functions']}
    Should Be True    ${result['playwright_still_enabled']}

# =============================================================================
# Convenience Function Tests
# =============================================================================

Test Get All External Tools
    [Documentation]    Test get_all_external_tools returns all toolkits
    [Tags]    convenience
    ${result}=    Get All External Tools
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['count_4']}
    Should Be True    ${result['has_playwright']}
    Should Be True    ${result['has_powershell']}
    Should Be True    ${result['has_desktop_commander']}
    Should Be True    ${result['has_octocode']}

Test Get Web Automation Tools
    [Documentation]    Test get_web_automation_tools returns PlaywrightTools
    [Tags]    convenience
    ${result}=    Get Web Automation Tools
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_playwright']}
    Should Be True    ${result['name_playwright']}

Test Get DevOps Tools
    [Documentation]    Test get_devops_tools returns PowerShellTools
    [Tags]    convenience
    ${result}=    Get DevOps Tools
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_powershell']}
    Should Be True    ${result['name_powershell']}

Test Get File Tools
    [Documentation]    Test get_file_tools returns DesktopCommanderTools
    [Tags]    convenience
    ${result}=    Get File Tools
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_desktop_commander']}
    Should Be True    ${result['name_desktop_commander']}

Test Get Code Research Tools
    [Documentation]    Test get_code_research_tools returns OctoCodeTools
    [Tags]    convenience
    ${result}=    Get Code Research Tools
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_octocode']}
    Should Be True    ${result['name_octocode']}

# =============================================================================
# Module-Level Tests
# =============================================================================

Test AGNO Available Flag
    [Documentation]    Test AGNO_AVAILABLE flag exists
    [Tags]    module
    ${result}=    AGNO Available Flag
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['is_bool']}

Test Stub Decorator When No AGNO
    [Documentation]    Test stub decorator marks functions
    [Tags]    module
    ${result}=    Stub Decorator When No AGNO
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['navigate_valid_tool']}

# =============================================================================
# JSON Output Validation Tests
# =============================================================================

Test All Tools Return Valid JSON
    [Documentation]    Test all tools return parseable JSON
    [Tags]    json    validation
    ${result}=    All Tools Return Valid JSON
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['all_valid_json']}
    Should Be True    ${result['all_have_simulated_status']}

Test Results Have Action Field
    [Documentation]    Test all results include action field
    [Tags]    json    validation
    ${result}=    Results Have Action Field
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_action']}

Test Results Have Message Field
    [Documentation]    Test all results include message field
    [Tags]    json    validation
    ${result}=    Results Have Message Field
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_message']}

# =============================================================================
# Tool Matrix Compliance (RULE-007)
# =============================================================================

Test Tier 1 Tools Present
    [Documentation]    Test Tier 1 tools (required) are present
    [Tags]    compliance    rule-007
    ${result}=    Tier 1 Tools Present
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['playwright_has_5_plus_tools']}

Test Tier 2 Tools Present
    [Documentation]    Test Tier 2 tools (recommended) are present
    [Tags]    compliance    rule-007
    ${result}=    Tier 2 Tools Present
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['powershell_2_plus']}
    Should Be True    ${result['desktop_commander_5_plus']}
    Should Be True    ${result['octocode_4_plus']}
