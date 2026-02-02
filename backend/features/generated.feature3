Feature: Sandbox Static Page UI interactions

Background:
  Given I open the sandbox static page "https://nat-studio-pfizer.genai-newpage.com/sandbox-static"
  Then I should see the page title "Sandbox Static Page"
  And I should see the description "This page contains various UI elements including forms, dropdowns, buttons, images, and icons for testing purposes."

Scenario: Verify main menu toggle opens the menu
  Given I am on the sandbox static page
  When I click the "Menu" button
  Then I should see the menu panel
  And I should see the "Contact Us" menu option
  And I should see the "About" menu option
  And I should see the "Support" menu option
  And I should see the menu close button

Scenario: Verify closing the menu hides menu options
  Given I am on the sandbox static page with the menu open
  When I click the menu close button
  Then I should not see the menu panel
  And I should not see the "Contact Us" menu option
  And I should not see the "About" menu option
  And I should not see the "Support" menu option

Scenario: Verify clicking Click Me button updates UI
  Given I am on the sandbox static page
  And I should see the "Click Me" button
  When I click the "Click Me" button
  Then the "Click Me" button state should change to "✓ Button Clicked!"
  And I should see a banner message "Button state changed!" indicating both primary buttons are active

Scenario: Verify clicking Center Aligned Button updates UI and banner
  Given I am on the sandbox static page
  And I should see the "Center Aligned Button" button
  When I click the "Center Aligned Button" button
  Then the "Center Aligned Button" button state should change to "✓ Center Button Activated!"
  And I should see a banner message "Button state changed! Both buttons are now active!" indicating both primary buttons are active

Scenario: Verify dropdown default state
  Given I am on the sandbox static page
  Then I should see the label "Select an Option"
  And I should see the dropdown with placeholder "Choose an option..."

Scenario: Select Option 1 from the dropdown
  Given I am on the sandbox static page
  When I open the "Select an Option" dropdown
  And I select "Option 1" from the dropdown
  Then I should see the label "Selected: option1"

Scenario: Select Option 2 from the dropdown
  Given I am on the sandbox static page
  When I open the "Select an Option" dropdown
  And I select "Option 2" from the dropdown
  Then I should see the label "Selected: option2"

Scenario: Select Option 3 from the dropdown
  Given I am on the sandbox static page
  When I open the "Select an Option" dropdown
  And I select "Option 3" from the dropdown
  Then I should see the label "Selected: option3"

Scenario: Select Option 4 from the dropdown
  Given I am on the sandbox static page
  When I open the "Select an Option" dropdown
  And I select "Option 4" from the dropdown
  Then I should see the label "Selected: option4"

Scenario: Select Option 5 from the dropdown
  Given I am on the sandbox static page
  When I open the "Select an Option" dropdown
  And I select "Option 5" from the dropdown
  Then I should see the label "Selected: option5"

Scenario: Submit Sign Up form successfully
  Given I am on the sandbox static page
  And I scroll to the "Sign Up Form" section
  And I should see the "First Name" field in the Sign Up form
  And I should see the "Last Name" field in the Sign Up form
  And I should see the "Middle Name" field in the Sign Up form
  And I should see the "Email Address" field in the Sign Up form
  When I enter "John" into the Sign Up form First Name field 
  And I enter "Doe" into the Last Name field 
  And I enter "A" into the Middle Name field 
  And I enter "john.doe@example.com" into the Email Address field
  And I click the "Sign Up" button
  Then I should see the notification "Sign up successful! Your account has been created."
  And I should see the notification inside the Notifications section

Scenario: Submit Sign Up form with only First Name entered
  Given I am on the sandbox static page
  And I scroll to the "Sign Up Form" section
  When I enter "John" into the First Name field
  And I click the "Sign Up" button
  Then I should see the validation message "Last name is required"
  And I should see the validation message "Middle name is required"
  And I should see the validation message "Email is required"
  And I should not see a success notification

Scenario: Submit Registration form successfully
  Given I am on the sandbox static page
  And I scroll to the "Registration Form" section
  And I should see the "First Name" field in the Registration form
  And I should see the "Last Name" field in the Registration form
  And I should see the "state" field in the Registration form
  And I should see the "Email Address" field in the Registration form
  When I enter "Alice" into the Registration form First Name field and "Smith" into the Last Name field and "California" into the state field and "alice.smith@example.com" into the Email Address field
  And I click the "Register" button
  Then I should see the notification "Registration successful! Your account has been registered."
  And I should see the notification inside the Notifications section

Scenario: Submit Registration form with all fields empty
  Given I am on the sandbox static page
  And I scroll to the "Registration Form" section
  When I click the "Register" button without entering any details
  Then I should see the validation message "First name is required"
  And I should see the validation message "Last name is required"
  And I should see the validation message "state is required"
  And I should see the validation message "Email is required"
  And I should not see a registration success notification

Scenario: Submit Registration form with missing state field
  Given I am on the sandbox static page
  And I scroll to the "Registration Form" section
  When I enter "Alice" into the First Name field
  And I enter "Smith" into the Last Name field
  And I enter "alice.smith@example.com" into the Email Address field
  And I click the "Register" button
  Then I should see the validation message "state is required"
  And I should not see a registration success notification

Scenario: Submit Sign Up form with invalid email format
  Given I am on the sandbox static page
  And I scroll to the "Sign Up Form" section
  When I enter "John" into the First Name field
  And I enter "Doe" into the Last Name field
  And I enter "A" into the Middle Name field
  And I enter "invalid-email" into the Email Address field
  And I click the "Sign Up" button
  Then I should see the validation message "Please enter a valid email"
  And I should not see a success notification

Scenario: Submit Registration form with invalid email
  Given I am on the sandbox static page
  And I scroll to the "Registration Form" section
  When I enter "Alice" into the First Name field
  And I enter "Smith" into the Last Name field
  And I enter "California" into the state field
  And I enter "invalid-email" into the Email Address field
  And I click the "Register" button
  Then I should see the validation message "Please enter a valid email"
  And I should not see a registration success notification

Scenario: Verify Contact Us menu link navigation
  Given I am on the sandbox static page with the menu open
  When I click the "Contact Us" menu option
  Then I navigate to "https://nat-studio-pfizer.genai-newpage.com/contact-us"

Scenario: Verify About menu link navigation
  Given I am on the sandbox static page with the menu open
  When I click the "About" menu option
  Then I navigate to "https://nat-studio-pfizer.genai-newpage.com/about"

Scenario: Verify Support menu link navigation
  Given I am on the sandbox static page with the menu open
  When I click the "Support" menu option
  Then I navigate to "https://nat-studio-pfizer.genai-newpage.com/support"

Scenario: Verify footer Contact Us link navigation
  Given I am on the sandbox static page
  And I scroll to the footer links
  And I should see the footer link "Contact Us"
  When I click the footer link "Contact Us"
  Then I navigate to "https://nat-studio-pfizer.genai-newpage.com/contact-us"

Scenario: Verify Link For Break footer link navigation
  Given I am on the sandbox static page
  And I scroll to the footer links
  And I should see the footer link "Link For Break"
  When I click the footer link "Link For Break"
  Then I navigate to "https://nat-studio-dev.genai-newpage.com/sandbox-dynamic"