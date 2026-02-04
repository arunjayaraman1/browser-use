Feature: Validate provided DATA object

Scenario: Handle null dom and empty arrays
Given the DATA object
"""
{
  "dom": null,
  "errors": [],
  "notifications": [],
  "observations": []
}
"""
Then the field "dom" is null
And the field "errors" is []
And the field "notifications" is []
And the field "observations" is []