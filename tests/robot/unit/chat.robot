*** Settings ***
Documentation    Agent Chat Tests (ORCH-006)
...              Per: RF-005 Robot Framework Migration
...              Migrated from tests/test_chat.py
Library          Collections
Library          ../../libs/ChatLibrary.py
Resource         ../resources/common.resource
Force Tags             unit    chat    orch-006    rule-023    medium    mcp    session    validate    ARCH-MCP-02-v1

*** Test Cases ***
# =============================================================================
# Chat State Constants Tests
# =============================================================================

Test Role Colors Defined
    [Documentation]    Chat role colors are defined
    [Tags]    state    constants
    ${result}=    Role Colors Defined
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_user']}
    Should Be True    ${result['has_agent']}
    Should Be True    ${result['has_system']}
    Should Be True    ${result['has_error']}

Test Status Icons Defined
    [Documentation]    Chat status icons are defined
    [Tags]    state    constants
    ${result}=    Status Icons Defined
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_pending']}
    Should Be True    ${result['has_processing']}
    Should Be True    ${result['has_complete']}
    Should Be True    ${result['has_error']}

# =============================================================================
# Chat State Transforms Tests
# =============================================================================

Test With Chat Messages Transform
    [Documentation]    Set chat messages
    [Tags]    state    transforms
    ${result}=    With Chat Messages Transform
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['new_state_correct']}
    Should Be True    ${result['original_unchanged']}

Test With Chat Message Append
    [Documentation]    Append a chat message
    [Tags]    state    transforms
    ${result}=    With Chat Message Append
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['length_increased']}
    Should Be True    ${result['message_appended']}

Test With Chat Loading Transform
    [Documentation]    Set chat loading state
    [Tags]    state    transforms
    ${result}=    With Chat Loading Transform
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['loading_set']}

Test With Chat Input Transform
    [Documentation]    Set chat input text
    [Tags]    state    transforms
    ${result}=    With Chat Input Transform
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['input_set']}

Test With Chat Agent Transform
    [Documentation]    Set selected chat agent
    [Tags]    state    transforms
    ${result}=    With Chat Agent Transform
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['agent_set']}

Test With Chat Session Transform
    [Documentation]    Set chat session ID
    [Tags]    state    transforms
    ${result}=    With Chat Session Transform
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['session_set']}

Test With Chat Task Transform
    [Documentation]    Set chat task ID
    [Tags]    state    transforms
    ${result}=    With Chat Task Transform
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['task_set']}

# =============================================================================
# Chat Helper Functions Tests
# =============================================================================

Test Get Chat Role Color
    [Documentation]    Get color for chat role
    [Tags]    helpers
    ${result}=    Get Chat Role Color
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['user_primary']}
    Should Be True    ${result['agent_success']}
    Should Be True    ${result['system_grey']}
    Should Be True    ${result['error_error']}
    Should Be True    ${result['unknown_default']}

Test Get Chat Status Icon
    [Documentation]    Get icon for chat status
    [Tags]    helpers
    ${result}=    Get Chat Status Icon
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['pending_clock']}
    Should Be True    ${result['processing_loading']}
    Should Be True    ${result['complete_check']}
    Should Be True    ${result['error_alert']}

# =============================================================================
# Chat Message Formatting Tests
# =============================================================================

Test Format Chat Message User
    [Documentation]    Format user message
    [Tags]    message    formatting
    ${result}=    Format Chat Message User
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['role_user']}
    Should Be True    ${result['is_user_true']}
    Should Be True    ${result['is_agent_false']}
    Should Be True    ${result['role_color_primary']}

Test Format Chat Message Agent
    [Documentation]    Format agent message
    [Tags]    message    formatting
    ${result}=    Format Chat Message Agent
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['role_agent']}
    Should Be True    ${result['is_user_false']}
    Should Be True    ${result['is_agent_true']}
    Should Be True    ${result['agent_name_correct']}
    Should Be True    ${result['role_color_success']}

# =============================================================================
# Chat Message Creation Tests
# =============================================================================

Test Create User Message
    [Documentation]    Create user message
    [Tags]    message    creation
    ${result}=    Create User Message
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['role_user']}
    Should Be True    ${result['content_correct']}
    Should Be True    ${result['status_complete']}
    Should Be True    ${result['id_prefix']}
    Should Be True    ${result['has_timestamp']}

Test Create Agent Message
    [Documentation]    Create agent message
    [Tags]    message    creation
    ${result}=    Create Agent Message
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['role_agent']}
    Should Be True    ${result['content_correct']}
    Should Be True    ${result['agent_id_correct']}
    Should Be True    ${result['agent_name_correct']}
    Should Be True    ${result['id_prefix']}

Test Create System Message
    [Documentation]    Create system message
    [Tags]    message    creation
    ${result}=    Create System Message
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['role_system']}
    Should Be True    ${result['content_correct']}
    Should Be True    ${result['status_complete']}

# =============================================================================
# Chat API Models Tests
# =============================================================================

Test Chat Message Request Model
    [Documentation]    ChatMessageRequest model
    [Tags]    api    models
    ${result}=    Chat Message Request Model
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['content_correct']}
    Should Be True    ${result['agent_id_correct']}
    Should Be True    ${result['session_id_correct']}

Test Chat Message Request Defaults
    [Documentation]    ChatMessageRequest with defaults
    [Tags]    api    models
    ${result}=    Chat Message Request Defaults
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['content_correct']}
    Should Be True    ${result['agent_id_none']}
    Should Be True    ${result['session_id_none']}

Test Chat Message Response Model
    [Documentation]    ChatMessageResponse model
    [Tags]    api    models
    ${result}=    Chat Message Response Model
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['id_correct']}
    Should Be True    ${result['role_correct']}
    Should Be True    ${result['agent_name_correct']}

# =============================================================================
# Chat Command Processing Tests
# =============================================================================

Test Help Command Processing
    [Documentation]    Process /help command
    [Tags]    commands
    ${result}=    Help Command Processing
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_available_commands']}
    Should Be True    ${result['has_status_command']}
    Should Be True    ${result['has_tasks_command']}

Test Status Command Processing
    [Documentation]    Process /status command
    [Tags]    commands
    ${result}=    Status Command Processing
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_status_info']}

Test Tasks Command Processing
    [Documentation]    Process /tasks command
    [Tags]    commands
    ${result}=    Tasks Command Processing
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_task_info']}

Test Rules Command Processing
    [Documentation]    Process /rules command
    [Tags]    commands
    ${result}=    Rules Command Processing
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_rule_info']}

Test Agents Command Processing
    [Documentation]    Process /agents command
    [Tags]    commands
    ${result}=    Agents Command Processing
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_agent_info']}

Test Search Command No Query
    [Documentation]    Process /search without query
    [Tags]    commands
    ${result}=    Search Command No Query
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_usage_or_search']}

Test Delegate Command No Task
    [Documentation]    Process /delegate without task
    [Tags]    commands
    ${result}=    Delegate Command No Task
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_usage_or_delegate']}

Test Natural Language Fallback
    [Documentation]    Natural language processing
    [Tags]    commands    nlp
    ${result}=    Natural Language Fallback
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['has_response']}

# =============================================================================
# Chat Session Management Tests
# =============================================================================

Test Generate Session Id
    [Documentation]    Generate chat session ID
    [Tags]    session
    ${result}=    Generate Session Id
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['starts_with_chat']}
    Should Be True    ${result['length_valid']}

Test Generate Unique Session Ids
    [Documentation]    Session IDs are unique
    [Tags]    session
    ${result}=    Generate Unique Session Ids
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['all_unique']}

# =============================================================================
# Integration Tests
# =============================================================================

Test Send Message Creates Session
    [Documentation]    Sending message creates new session
    [Tags]    integration    api
    ${result}=    Send Message Creates Session
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['status_200']}
    Should Be True    ${result['role_agent']}
    Should Be True    ${result['has_commands']}

Test Send Message With Agent
    [Documentation]    Send message to specific agent
    [Tags]    integration    api
    ${result}=    Send Message With Agent
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['status_200']}
    Should Be True    ${result['has_agent_id']}

Test List Chat Sessions
    [Documentation]    List chat sessions
    [Tags]    integration    api
    ${result}=    List Chat Sessions
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['status_200']}
    Should Be True    ${result['is_list']}

Test Get Nonexistent Session
    [Documentation]    Get nonexistent session returns 404
    [Tags]    integration    api
    ${result}=    Get Nonexistent Session
    Skip If    ${result.get('skipped', False)}    ${result.get('reason', 'Import failed')}
    Should Be True    ${result['status_404']}
