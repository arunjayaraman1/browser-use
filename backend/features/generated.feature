Feature: Validate all navigation links

Background:
  Given I am on "https://www.pfizerforall.com"

Scenario Outline: Validate direct page link navigation
  When I click the "<link_text>" link
  Then I should be navigated to "<url_value>"

Examples:
  | link_text                             | url_value                                                                 |
  | Explore cancer screenings             | https://www.pfizerforall.com/find-care/cancer-screening/                  |
  | Visit GoodRx                          | http://goodrx.com/go/pfizer?utm_source=pfe&exitCode=pfa                   |
  | Explore biomarker testing             | https://www.pfizerforall.com/find-care/biomarker-testing/                 |
  | Start here                            | https://www.pfizerforall.com/vaccines/pneumococcal-pneumonia              |
  | Learn why                             | https://www.pfizerforall.com/covid-19/treatment-education                 |
  | Get started                           | https://www.pfizerforall.com/savings-support/prescription-assistance      |
  | Find a provider                       | https://www.pfizerforall.com/find-care/talk-to-a-doctor                   |
  | Find out more                         | https://www.pfizerforall.com/covid-19/treatment-education                 |
  | Find out more                         | https://www.pfizerforall.com/migraine/treatment                           |
  | See here                              | https://www.goodrx.com/go/pfizer?exitCode=pfa                             |
  | Learn more at GoodRx                  | http://goodrx.com/go/pfizer?utm_source=pfe&exitCode=pfa                   |
  | Explore ways to save                  | https://www.pfizerforall.com/savings-support/prescription-assistance      |
  | Ask your question                     | https://healthanswers.pfizer.com/?exitCode=pfa                            |
  | Support                               | https://www.pfizerforall.com/support                                      |
  | Visit Health Answers                  | https://healthanswers.pfizer.com/welcome                                  |
  | Terms of use                          | https://www.pfizer.com/general/terms?exitCode=pfa                         |
  | Privacy policy                        | https://www.pfizer.com/privacy?exitCode=pfa                               |
  | Cookie preferences                    | https://www.pfizerforall.com/#ot-sdk-btn                                  |
  | Privacy Policy                        | https://www.pfizer.com/privacy?exitCode=pfa                               |
  | Washington Health Data Privacy Policy | https://www.pfizer.com/washington-health-data-privacy-policy?exitCode=pfa |

Scenario Outline: Validate dropdown link navigation
  When I open the "<dropdown_name>" menu
  And I select the "<link_text>" link under group "<group_name>"
  Then I should be navigated to "<url_value>"

Examples: Understand Your Health
  | dropdown_name          | group_name             | link_text                     | url_value                                                            |
  | Understand Your Health | None                   | Vaccines                      | https://www.pfizerforall.com/vaccines/                               |
  | Understand Your Health | None                   | COVID-19                      | https://www.pfizerforall.com/vaccines/covid-19                       |
  | Understand Your Health | None                   | Flu                           | https://www.pfizerforall.com/vaccines/flu                            |
  | Understand Your Health | None                   | Pneumococcal pneumonia        | https://www.pfizerforall.com/vaccines/pneumococcal-pneumonia         |
  | Understand Your Health | None                   | RSV                           | https://www.pfizerforall.com/vaccines/rsv                            |
  | Understand Your Health | None                   | Menopause                     | https://www.pfizerforall.com/menopause/                              |
  | Understand Your Health | None                   | Migraine                      | https://www.pfizerforall.com/migraine/                               |
  | Understand Your Health | None                   | Cancer                        | https://www.pfizerforall.com/cancer                                  |
  | Understand Your Health | None                   | ATTR-CM                       | https://www.pfizerforall.com/attr-cm/                                |
  | Understand Your Health | None                   | COVID-19                      | https://www.pfizerforall.com/covid-19/                               |
  | Understand Your Health | None                   | Health Information Center     | https://www.pfizerforall.com/education/                              |
  | Understand Your Health | None                   | About Vaccines                | https://www.pfizerforall.com/vaccines/                               |

Examples: Find the Care You Need
  | dropdown_name          | group_name             | link_text                     | url_value                                                            |
  | Find the Care You Need | Understand Your Health | Talk to a Healthcare Provider | https://www.pfizerforall.com/find-care/talk-to-a-doctor              |
  | Find the Care You Need | Understand Your Health | Schedule a Vaccine            | https://www.vaxassist.com/?exitCode=pfa                              |
  | Find the Care You Need | Understand Your Health | Discover Cancer Screening     | https://www.pfizerforall.com/find-care/cancer-screening/             |
  | Find the Care You Need | Understand Your Health | Explore Biomarker Testing     | https://www.pfizerforall.com/find-care/biomarker-testing/            |
  | Find the Care You Need | Understand Your Health | Prepare for Care              | https://www.pfizerforall.com/find-care/prepare-for-care              |
  | Find the Care You Need | None                   | Talk to a Healthcare Provider | https://www.pfizerforall.com/find-care/talk-to-a-doctor              |
  | Find the Care You Need | None                   | Schedule a Vaccine            | https://www.vaxassist.com/?exitCode=pfa                              |
  | Find the Care You Need | None                   | Discover Cancer Screening     | https://www.pfizerforall.com/find-care/cancer-screening/             |
  | Find the Care You Need | None                   | Explore Biomarker Testing     | https://www.pfizerforall.com/find-care/biomarker-testing/            |
  | Find the Care You Need | None                   | Prepare for Care              | https://www.pfizerforall.com/find-care/prepare-for-care              |

Examples: Get Savings
  | dropdown_name          | group_name             | link_text                     | url_value                                                            |
  | Get Savings            | Understand Your Health | Get Financial Assistance      | https://www.pfizerforall.com/savings-support/prescription-assistance |
  | Get Savings            | None                   | Get Financial Assistance      | https://www.pfizerforall.com/savings-support/prescription-assistance |

Examples: Explore Pfizer
  | dropdown_name          | group_name             | link_text                     | url_value                                                            |
  | Explore Pfizer         | Understand Your Health | Visit Pfizer.com              | https://www.pfizer.com/?exitCode=pfa                                 |
  | Explore Pfizer         | Understand Your Health | Visit Health Answers          | https://healthanswers.pfizer.com/?exitCode=pfa                       |
  | Explore Pfizer         | Understand Your Health | Find a Clinical Trial         | https://www.pfizerclinicaltrials.com/?exitCode=pfa                   |
  | Explore Pfizer         | Understand Your Health | See Our Work in Cancer        | https://cancer.pfizer.com/?exitCode=pfa                              |
  | Explore Pfizer         | None                   | Visit Pfizer.com              | https://www.pfizer.com/?exitCode=pfa                                 |
  | Explore Pfizer         | None                   | Visit Health Answers          | https://healthanswers.pfizer.com/?exitCode=pfa                       |
  | Explore Pfizer         | None                   | Find a Clinical Trial         | https://www.pfizerclinicaltrials.com/?exitCode=pfa                   |
  | Explore Pfizer         | None                   | See Our Work in Cancer        | https://cancer.pfizer.com/?exitCode=pfa                              |
