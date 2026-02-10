Feature: Validate all navigation links

Background:
  Given I am on "https://www.pfizerforall.com/"

Scenario Outline: Validate direct page link navigation
  When I click the "<link_text>" link
  Then I should be navigated to "<url_value>"
  Then I should see the page title "<page_title>"

Examples:
  | link_text | url_value | page_title |
  | PfizerForAll | https://www.pfizerforall.com/ | pfizerforall.com |
  | Explore cancer screenings | https://www.pfizerforall.com/find-care/cancer-screening/ | undefined |
  | Get started | https://www.pfizerforall.com/savings-support/prescription-assistance | undefined |
  | Find a provider | https://www.pfizerforall.com/find-care/talk-to-a-doctor | undefined |

Scenario Outline: Validate dropdown link navigation
  When I open the "<dropdown_name>" menu
  And I select the "<link_text>" link under group "<group_name>"
  Then I should be navigated to "<url_value>"
  And I should see the page title "<page_title>"

Examples:
  | dropdown_name | group_name | link_text | url_value | page_title |