<url>
https://www.pfizerforall.com/
</url>
<query>
Within the currently open top navigation dropdown labeled 'Understand Your Health', extract:
- dropdown_name: 'Understand Your Health'
- For each visible subgroup/section heading in this dropdown, capture group_name (e.g., 'Vaccines', 'Menopause', 'Migraine', 'Cancer', 'Heart Health', 'Infections', 'Health Information Center', and any 'Recommended' tile section if present). If no subgroup for a link, use 'None'.
- For each link inside this dropdown, capture an object with: link_text (visible text), url (absolute URL starting with https://), group_name (as above), and dropdown_name ('Understand Your Health'). Only include links contained within this open dropdown panel (not page body). Return as a JSON array of objects with keys: link_text, url, type='dropdown', dropdown_name, group_name.
Ensure all URLs are absolute (resolve relative to https://www.pfizerforall.com).
</query>
<result>
[
  {
    "link_text": "Vaccines",
    "url": "https://www.pfizerforall.com/vaccines/",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Vaccines"
  },
  {
    "link_text": "About Vaccines",
    "url": "https://www.pfizerforall.com/vaccines/",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Vaccines"
  },
  {
    "link_text": "COVID-19",
    "url": "https://www.pfizerforall.com/vaccines/covid-19",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Vaccines"
  },
  {
    "link_text": "Flu",
    "url": "https://www.pfizerforall.com/vaccines/flu",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Vaccines"
  },
  {
    "link_text": "Pneumococcal pneumonia",
    "url": "https://www.pfizerforall.com/vaccines/pneumococcal-pneumonia",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Vaccines"
  },
  {
    "link_text": "RSV",
    "url": "https://www.pfizerforall.com/vaccines/rsv",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Vaccines"
  },
  {
    "link_text": "Menopause",
    "url": "https://www.pfizerforall.com/menopause/",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Menopause"
  },
  {
    "link_text": "Migraine",
    "url": "https://www.pfizerforall.com/migraine/",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Migraine"
  },
  {
    "link_text": "Cancer",
    "url": "https://www.pfizerforall.com/cancer",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Cancer"
  },
  {
    "link_text": "ATTR-CM",
    "url": "https://www.pfizerforall.com/attr-cm/",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Heart Health"
  },
  {
    "link_text": "COVID-19",
    "url": "https://www.pfizerforall.com/covid-19/",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Infections"
  },
  {
    "link_text": "Health Information Center",
    "url": "https://www.pfizerforall.com/education/",
    "type": "dropdown",
    "dropdown_name": "Understand Your Health",
    "group_name": "Health Information Center"
  }
]
</result>