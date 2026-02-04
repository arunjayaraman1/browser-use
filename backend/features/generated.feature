Feature: Sandbox Static Page visible UI interactions

  Background:
    Given the user is on the Sandbox Static Page

  Scenario: Menu toggle visibility and toggling
    Then the Menu button is visible
    When the user clicks the Menu button
    Then a menu becomes visible
    When the user clicks the Menu button again
    Then the menu is not visible

  Scenario: Dropdown shows default placeholder
    Then the Select an Option dropdown displays "Choose an option..."

  Scenario: Open and close dropdown without selection
    When the user opens the Select an Option dropdown
    Then the dropdown options are visible
    When the user clicks outside the dropdown
    Then the dropdown options are not visible

  Scenario Outline: Select an option from the dropdown
    When the user opens the Select an Option dropdown
    And the user selects "<option>"
    Then the Select an Option dropdown displays "<option>"

    Examples:
      | option   |
      | Option 1 |
      | Option 2 |
      | Option 3 |

  Scenario: Click primary button
    Then the "Click Me" button is visible
    When the user clicks the "Click Me" button
    Then the "Click Me" button remains visible

  Scenario: Click center aligned button
    Then the "Center Aligned Button" button is visible
    When the user clicks the "Center Aligned Button" button
    Then the "Center Aligned Button" button remains visible

  Scenario: Follow Contact Us link
    Then the "Contact Us" link is visible
    When the user clicks the "Contact Us" link
    Then navigation starts to the link destination

  Scenario: Follow Link For Break
    Then the "Link For Break" link is visible
    When the user clicks the "Link For Break" link
    Then navigation starts to the link destination

  Scenario: Sign Up Form accepts input values
    Then the Sign Up Form is visible
    And the "First Name" field with placeholder "Enter your first name" is visible in Sign Up Form
    And the "Last Name" field with placeholder "Enter your last name" is visible in Sign Up Form
    And the "Middle Name" field with placeholder "Enter your Middle name" is visible in Sign Up Form
    And the "Email Address" field with placeholder "Enter your email" is visible in Sign Up Form
    When the user types "Alice" into the "First Name" field in Sign Up Form
    And the user types "Doe" into the "Last Name" field in Sign Up Form
    And the user types "Q" into the "Middle Name" field in Sign Up Form
    And the user types "alice@example.com" into the "Email Address" field in Sign Up Form
    Then the "First Name" field value is "Alice" in Sign Up Form
    And the "Last Name" field value is "Doe" in Sign Up Form
    And the "Middle Name" field value is "Q" in Sign Up Form
    And the "Email Address" field value is "alice@example.com" in Sign Up Form

  Scenario: Sign Up Form clear fields shows placeholders
    When the user clears the "First Name" field in Sign Up Form
    And the user clears the "Last Name" field in Sign Up Form
    And the user clears the "Middle Name" field in Sign Up Form
    And the user clears the "Email Address" field in Sign Up Form
    Then the "First Name" field placeholder is "Enter your first name" in Sign Up Form
    And the "Last Name" field placeholder is "Enter your last name" in Sign Up Form
    And the "Middle Name" field placeholder is "Enter your Middle name" in Sign Up Form
    And the "Email Address" field placeholder is "Enter your email" in Sign Up Form

  Scenario: Sign Up button clickable with empty fields
    Then the "Sign Up" button is visible in Sign Up Form
    When the user clicks the "Sign Up" button in Sign Up Form
    Then the "Sign Up" button remains visible in Sign Up Form

  Scenario: Sign Up button clickable with filled fields
    When the user types "Bob" into the "First Name" field in Sign Up Form
    And the user types "Smith" into the "Last Name" field in Sign Up Form
    And the user types "A" into the "Middle Name" field in Sign Up Form
    And the user types "bob@example.com" into the "Email Address" field in Sign Up Form
    And the user clicks the "Sign Up" button in Sign Up Form
    Then the "Sign Up" button remains visible in Sign Up Form

  Scenario: Registration Form accepts input values
    Then the Registration Form is visible
    And the "First Name" field with placeholder "Enter your first name" is visible in Registration Form
    And the "Last Name" field with placeholder "Enter your last name" is visible in Registration Form
    And the "state" field with placeholder "Enter your state" is visible in Registration Form
    And the "Email Address" field with placeholder "Enter your email" is visible in Registration Form
    When the user types "Carol" into the "First Name" field in Registration Form
    And the user types "Johnson" into the "Last Name" field in Registration Form
    And the user types "NY" into the "state" field in Registration Form
    And the user types "carol@example.com" into the "Email Address" field in Registration Form
    Then the "First Name" field value is "Carol" in Registration Form
    And the "Last Name" field value is "Johnson" in Registration Form
    And the "state" field value is "NY" in Registration Form
    And the "Email Address" field value is "carol@example.com" in Registration Form

  Scenario: Registration Form clear fields shows placeholders
    When the user clears the "First Name" field in Registration Form
    And the user clears the "Last Name" field in Registration Form
    And the user clears the "state" field in Registration Form
    And the user clears the "Email Address" field in Registration Form
    Then the "First Name" field placeholder is "Enter your first name" in Registration Form
    And the "Last Name" field placeholder is "Enter your last name" in Registration Form
    And the "state" field placeholder is "Enter your state" in Registration Form
    And the "Email Address" field placeholder is "Enter your email" in Registration Form

  Scenario: Register button clickable with empty fields
    Then the "Register" button is visible in Registration Form
    When the user clicks the "Register" button in Registration Form
    Then the "Register" button remains visible in Registration Form

  Scenario: Register button clickable with filled fields
    When the user types "Dan" into the "First Name" field in Registration Form
    And the user types "Lee" into the "Last Name" field in Registration Form
    And the user types "CA" into the "state" field in Registration Form
    And the user types "dan@example.com" into the "Email Address" field in Registration Form
    And the user clicks the "Register" button in Registration Form
    Then the "Register" button remains visible in Registration Form