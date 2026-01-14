@e2e @crud
Feature: CRUD Operations
  As a governance administrator
  I want to create, read, update, and delete entities
  So that I can manage the governance system

  Background:
    Given the dashboard is running on port 8081
    And the browser is open
    And I navigate to the dashboard

  @rules @create
  Scenario: Create a new rule
    When I click on "Rules" navigation
    And I click on "Add Rule" button
    And I fill in rule form with:
      | field      | value                    |
      | rule_id    | RULE-TEST-BDD-001        |
      | name       | BDD Test Rule            |
      | category   | testing                  |
      | priority   | HIGH                     |
      | directive  | Test directive for BDD   |
    And I submit the form
    Then I should see "Rule created successfully"
    And I should see "RULE-TEST-BDD-001" in the rules list

  @rules @read
  Scenario: View existing rule details
    When I click on "Rules" navigation
    And I search for "RULE-001"
    And I click on the rule "RULE-001"
    Then I should see the rule detail panel
    And I should see "Directive" section
    And I should see "Category" field
    And I should see "Priority" field

  @rules @update
  Scenario: Edit an existing rule
    Given a test rule "RULE-TEST-EDIT" exists
    When I click on "Rules" navigation
    And I search for "RULE-TEST-EDIT"
    And I click on the rule "RULE-TEST-EDIT"
    And I click on "Edit" button
    And I update the directive to "Updated directive"
    And I submit the form
    Then I should see "Rule updated successfully"

  @rules @delete
  Scenario: Delete a test rule
    Given a test rule "RULE-TEST-DELETE" exists
    When I click on "Rules" navigation
    And I search for "RULE-TEST-DELETE"
    And I click on the rule "RULE-TEST-DELETE"
    And I click on "Delete" button
    And I confirm the deletion
    Then I should see "Rule deleted successfully"
    And "RULE-TEST-DELETE" should not be in the rules list

  @tasks @lifecycle
  Scenario: Task lifecycle transitions
    Given a task "TASK-BDD-001" exists with status "pending"
    When I click on "Tasks" navigation
    And I search for "TASK-BDD-001"
    And I click on the task "TASK-BDD-001"
    And I change status to "in_progress"
    Then the task should show status "in_progress"
    When I change status to "completed"
    Then the task should show status "completed"

  @agents @trust
  Scenario: Update agent trust score
    Given an agent "claude-code" exists
    When I click on "Trust" navigation
    And I select agent "claude-code"
    And I update trust score to 0.95
    Then the agent should show trust score 0.95
