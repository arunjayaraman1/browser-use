<url>
https://www.pfizerforall.com/
</url>
<query>
Within the currently open top navigation dropdown labeled 'Find the Care You Need', extract:
- dropdown_name: 'Find the Care You Need'
- For each visible subgroup/section heading in this dropdown, capture group_name (use exact visible headings; if no subgroup for a link, use 'None').
- For each link inside this dropdown, capture an object with: link_text (visible text), url (absolute URL starting with https://), group_name (as above), and dropdown_name ('Find the Care You Need'). Only include links contained within this open dropdown panel (not page body).
Return as a JSON array of objects with keys: link_text, url, type='dropdown', dropdown_name, group_name.
Ensure all URLs are absolute (resolve relative to https://www.pfizerforall.com).
</query>
<result>
[
  {
    "link_text": "Talk to a Healthcare Provider",
    "url": "https://www.pfizerforall.com/find-care/talk-to-a-doctor",
    "type": "dropdown",
    "dropdown_name": "Find the Care You Need",
    "group_name": "None"
  },
  {
    "link_text": "Schedule a Vaccine",
    "url": "https://www.vaxassist.com/?exitCode=pfa",
    "type": "dropdown",
    "dropdown_name": "Find the Care You Need",
    "group_name": "None"
  },
  {
    "link_text": "Discover Cancer Screening",
    "url": "https://www.pfizerforall.com/find-care/cancer-screening/",
    "type": "dropdown",
    "dropdown_name": "Find the Care You Need",
    "group_name": "None"
  },
  {
    "link_text": "Explore Biomarker Testing",
    "url": "https://www.pfizerforall.com/find-care/biomarker-testing/",
    "type": "dropdown",
    "dropdown_name": "Find the Care You Need",
    "group_name": "None"
  },
  {
    "link_text": "Prepare for Care",
    "url": "https://www.pfizerforall.com/find-care/prepare-for-care",
    "type": "dropdown",
    "dropdown_name": "Find the Care You Need",
    "group_name": "None"
  }
]
</result>