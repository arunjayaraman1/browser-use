<url>
https://www.pfizerforall.com/
</url>
<query>
Within the currently open top navigation dropdown labeled 'Get Savings', extract:
- dropdown_name: 'Get Savings'
- For each visible subgroup/section heading in this dropdown, capture group_name (use exact visible headings; if no subgroup for a link, use 'None').
- For each link inside this dropdown, capture an object with: link_text (visible text), url (absolute URL starting with https://), group_name (as above), and dropdown_name ('Get Savings'). Only include links contained within this open dropdown panel (not page body).
Return as a JSON array of objects with keys: link_text, url, type='dropdown', dropdown_name, group_name.
Ensure all URLs are absolute (resolve relative to https://www.pfizerforall.com).
</query>
<result>
Information unavailable: The ‘Get Savings’ dropdown contains a single link (“Get Financial Assistance”), but its URL is not present in the provided content, so an absolute URL cannot be resolved. If you can provide more of the navigation markup (use start_from_char), I can return the required JSON.
</result>