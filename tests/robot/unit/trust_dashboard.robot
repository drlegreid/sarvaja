*** Settings ***
Documentation    RF-004: Unit Tests - Trust Dashboard
...              Migrated from tests/test_trust_dashboard.py
...              Per P9.5: Agent trust scoring and compliance metrics
Library          Collections
Library          ../../libs/TrustDashboardLibrary.py

*** Test Cases ***
# =============================================================================
# Data Access Tests
# =============================================================================

Get Agents Returns Empty On Connection Failure
    [Documentation]    GIVEN connection fails WHEN get_agents THEN empty list
    [Tags]    unit    trust    dashboard    agents    failure
    ${result}=    Get Agents Returns Empty On Connection Failure
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[empty_list]

Get Agents Returns Agents List
    [Documentation]    GIVEN connected WHEN get_agents THEN returns list
    [Tags]    unit    trust    dashboard    agents    list
    ${result}=    Get Agents Returns Agents List
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_three]
    Should Be True    ${result}[first_correct]

Get Agent Trust Score Returns None On Failure
    [Documentation]    GIVEN connection fails WHEN get_trust THEN None
    [Tags]    unit    trust    dashboard    score    failure
    ${result}=    Get Agent Trust Score Returns None On Failure
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_none]

Get Agent Trust Score Returns Score
    [Documentation]    GIVEN connected WHEN get_trust THEN returns score
    [Tags]    unit    trust    dashboard    score    success
    ${result}=    Get Agent Trust Score Returns Score
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct_score]

# =============================================================================
# Trust Calculation Tests
# =============================================================================

Calculate Trust Score Correct
    [Documentation]    GIVEN metrics WHEN calculate THEN correct formula
    [Tags]    unit    trust    dashboard    calculate    formula
    ${result}=    Calculate Trust Score Correct
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct]

Tenure Normalization Works
    [Documentation]    GIVEN tenure WHEN normalize THEN 0-1 scale
    [Tags]    unit    trust    dashboard    tenure    normalize
    ${result}=    Tenure Normalization Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[veteran_higher]

Zero Values Handled
    [Documentation]    GIVEN zeros WHEN calculate THEN handles gracefully
    [Tags]    unit    trust    dashboard    zero    edge
    ${result}=    Zero Values Handled
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[is_zero]

Score Clamped To Max
    [Documentation]    GIVEN high values WHEN calculate THEN max 1.0
    [Tags]    unit    trust    dashboard    clamp    max
    ${result}=    Score Clamped To Max
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[max_one]

# =============================================================================
# Leaderboard Tests
# =============================================================================

Build Trust Leaderboard Sorts By Score
    [Documentation]    GIVEN agents WHEN build_leaderboard THEN sorted desc
    [Tags]    unit    trust    dashboard    leaderboard    sort
    ${result}=    Build Trust Leaderboard Sorts By Score
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[first_highest]
    Should Be True    ${result}[last_lowest]

Leaderboard Includes Rank
    [Documentation]    GIVEN leaderboard WHEN build THEN includes rank
    [Tags]    unit    trust    dashboard    leaderboard    rank
    ${result}=    Leaderboard Includes Rank
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[rank_1]
    Should Be True    ${result}[rank_2]
    Should Be True    ${result}[rank_3]

Leaderboard Includes Trust Level
    [Documentation]    GIVEN leaderboard WHEN build THEN includes level
    [Tags]    unit    trust    dashboard    leaderboard    level
    ${result}=    Leaderboard Includes Trust Level
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[high]
    Should Be True    ${result}[medium]
    Should Be True    ${result}[low]

# =============================================================================
# State Management Tests
# =============================================================================

Initial State Has Trust Fields
    [Documentation]    GIVEN initial state WHEN check THEN has trust fields
    [Tags]    unit    trust    dashboard    state    initial
    ${result}=    Initial State Has Trust Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_agents]
    Should Be True    ${result}[has_selected_agent]
    Should Be True    ${result}[has_trust_leaderboard]
    Should Be True    ${result}[has_proposals]
    Should Be True    ${result}[has_escalated]

Navigation Includes Trust
    [Documentation]    GIVEN navigation WHEN check THEN has trust
    [Tags]    unit    trust    dashboard    state    navigation
    ${result}=    Navigation Includes Trust
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_trust]

With Agents Transform Works
    [Documentation]    GIVEN state WHEN with_agents THEN transforms
    [Tags]    unit    trust    dashboard    state    transform
    ${result}=    With Agents Transform Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[agents_set]
    Should Be True    ${result}[leaderboard_built]

# =============================================================================
# Trust Level Helpers Tests
# =============================================================================

Trust Level Colors Defined
    [Documentation]    GIVEN TRUST_LEVEL_COLORS WHEN check THEN all defined
    [Tags]    unit    trust    dashboard    helper    colors
    ${result}=    Trust Level Colors Defined
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_high]
    Should Be True    ${result}[has_medium]
    Should Be True    ${result}[has_low]

Get Trust Level Color Works
    [Documentation]    GIVEN level WHEN get_color THEN correct
    [Tags]    unit    trust    dashboard    helper    color
    ${result}=    Get Trust Level Color Works
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[high_success]
    Should Be True    ${result}[medium_warning]
    Should Be True    ${result}[low_error]
    Should Be True    ${result}[unknown_grey]

Get Trust Level Categorizes Correctly
    [Documentation]    GIVEN score WHEN get_level THEN correct category
    [Tags]    unit    trust    dashboard    helper    category
    ${result}=    Get Trust Level Categorizes Correctly
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[high_92]
    Should Be True    ${result}[medium_78]
    Should Be True    ${result}[low_45]
    Should Be True    ${result}[high_boundary]
    Should Be True    ${result}[medium_boundary]

# =============================================================================
# Governance Metrics Tests
# =============================================================================

Consensus Score In Range
    [Documentation]    GIVEN votes WHEN calculate_consensus THEN 0-1 range
    [Tags]    unit    trust    dashboard    metrics    consensus
    ${result}=    Consensus Score In Range
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[in_range]

Governance Stats Has Fields
    [Documentation]    GIVEN data WHEN get_stats THEN has all fields
    [Tags]    unit    trust    dashboard    metrics    stats
    ${result}=    Governance Stats Has Fields
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[has_total_agents]
    Should Be True    ${result}[has_avg_trust]
    Should Be True    ${result}[has_pending]
    Should Be True    ${result}[has_approval]

Average Trust Score Correct
    [Documentation]    GIVEN agents WHEN avg_trust THEN correct
    [Tags]    unit    trust    dashboard    metrics    average
    ${result}=    Average Trust Score Correct
    ${skipped}=    Evaluate    $result.get('skipped', False)
    Skip If    ${skipped}    Import failed
    Should Be True    ${result}[correct]
