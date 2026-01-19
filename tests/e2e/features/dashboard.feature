@e2e @dashboard
Feature: Governance Dashboard Navigation
  As a platform operator
  I want to navigate the governance dashboard
  So that I can manage rules, tasks, and agents

  Background:
    Given the dashboard is running on port 8081
    And the browser is open

  @smoke
  Scenario: Dashboard loads successfully
    When I navigate to the dashboard
    Then I should see "Sarvaja Governance Dashboard"
    And I should see the navigation menu

  @navigation
  Scenario Outline: Navigate to different views
    When I navigate to the dashboard
    And I click on "<tab>" navigation
    Then I should see "<expected_heading>"

    Examples:
      | tab      | expected_heading        |
      | Rules    | Governance Rules        |
      | Agents   | Registered Agents       |
      | Tasks    | Platform Tasks          |
      | Sessions | Session Evidence        |
      | Trust    | Agent Trust Dashboard   |

  @rules
  Scenario: View rule details
    When I navigate to the dashboard
    And I click on "Rules" navigation
    And I click on the first rule in the list
    Then I should see "Directive"
    And I should see "Edit" button
    And I should see "Delete" button

  @tasks
  Scenario: Tasks show status badges
    When I navigate to the dashboard
    And I click on "Tasks" navigation
    Then I should see task status badges
    And I should see "Add Task" button

  @infra
  Scenario: Infrastructure health dashboard
    When I navigate to the dashboard
    And I click on "Infra" navigation
    Then I should see "Infrastructure Health"
    And I should see service status cards
    And I should see recovery action buttons
