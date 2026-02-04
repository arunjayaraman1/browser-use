import os
import asyncio
from browser_use import Agent, Browser, ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME") or "gpt-5"
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL") or "gpt-4.1-mini"
# DEFAULT_URL = "https://nat-studio-pfizer.genai-newpage.com/sandbox-static"
DEFAULT_URL = "https://www.pfizerforall.com"


AGENT_PROMPT = """
Analyze the given webpage and test ALL navigation links. Output EXACTLY ONE valid Gherkin Feature file.

GOAL:
Validate navigation for:
1) Links directly visible on the page.
2) Links inside EVERY dropdown or menu in the navigation bar.

OUTPUT RULES (STRICT):
- Output ONLY raw Gherkin text.
- Do NOT use markdown, code blocks, bullet points, JSON, or explanations.
- Use ONLY valid Gherkin keywords: Feature, Background, Scenario Outline, Given, When, Then, And, Examples.
- Produce EXACTLY one Feature.
- Always include ONE Background section with the base page URL.
- Use Scenario Outline for link lists.
- Use Scenario only if there is truly a single unique case.
- Never output labels like "dropdown_name:" or "group_name:" outside tables.
- Never output comments inside Examples tables.
- Never output empty rows or mismatched columns.
- Use plain ASCII pipe characters `|` only.
- url_value MUST be a FULL absolute URL.
- Treat duplicate link_text values in different locations as separate rows.

STRUCTURE TO FOLLOW:

Feature: Validate all navigation links

Background:
  Given I am on "<base_url>"

Scenario Outline: Validate direct page link navigation
  When I click the "<link_text>" link
  Then I should be navigated to "<url_value>"
  Then I should see the page title "<page_title>"
  
Examples:
  | link_text | url_value | page_title |

Scenario Outline: Validate dropdown link navigation
  When I open the "<dropdown_name>" menu
  And I select the "<link_text>" link under group "<group_name>"
  And I should be navigated to "<url_value>"
  Then I should see the page title "<page_title>"

Examples: if Possible Customize sections are present in the dropdown then cover all the links inside it.
  | dropdown_name | group_name | link_text | url_value | page_title |

DATA COLLECTION RULES:

DIRECT PAGE LINKS:
- Identify every visible clickable link.
- Click → verify navigation → go back.
- Record link_text and full url_value.
- Capture the carousel links from beginning to end and cover all the links inside it.

DROPDOWN / MENU LINKS:
- Open each navigation dropdown/menu (hover or click).
- For each group/category inside it:
  - Capture dropdown_name and group_name.
- For each link inside each group:
  - Click → verify navigation → go back.
  - Record dropdown_name, group_name, link_text, url_value.
- If a link has no group, use "None" as group_name.
- Must check all the dropdowns and menus and cover all the links inside it.
- Top to Bottom Checking is mandatory.

NAVIGATION CHECK:
- For each link: open it, then verify (1) the browser URL is correct and (2) the page <title> matches the link text and intended destination.
- After every link check, return to the homepage before testing the next link. This is required.
- Do not add a "back to homepage" step in the Gherkin feature file; returning home is part of the flow but is not written as a scenario step.

CONSTRAINTS:
- Use ONLY text and URLs actually visible in the UI.
- DO NOT invent links, names, or categories.
- DO NOT extract or summarize destination page content .
- ONLY confirm navigation occurred and capture the final full URL.
- Back to Homepage is mandatory after each navigation.
- Dont add "And I navigate back to the homepage" in the Gherkin feature file.
- Check all the dropdowns links and cover all the links inside it.
- Cover full Homepage top to bottom and cover all the links.
Return ONLY the final Gherkin feature text. Nothing before or after.
"""


async def generate_gherkin(url: str):
    browser = Browser(
        headless=False,
        minimum_wait_page_load_time=2.0,
        wait_for_network_idle_page_load_time=6.0,
        wait_between_actions=1.5,
    )

    primary_llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
    fallback_llm = ChatOpenAI(model=FALLBACK_MODEL, temperature=0)

    agent = Agent(
        browser=browser,
        llm=primary_llm,
        fallback_llm=fallback_llm,
        # use_vision=True,
        # vision_detail_level='auto',
        task=f"{AGENT_PROMPT}\n\nWEBSITE:\n{url}",
        max_steps=35,
        llm_timeout=240,
        step_timeout=300,
        max_retries=2,
        max_failures=4,
    )

    try:
        history = await agent.run()
        result = history.final_result()

        if not result or len(result.strip()) < 20:
            print("❌ No valid Gherkin generated")
            return

        result = result.strip()

        print("\n===== GENERATED GHERKIN =====\n")
        print(result)
        print("\n============================\n")

        # Save to file
        features_dir = os.path.join(os.path.dirname(__file__), "features")
        os.makedirs(features_dir, exist_ok=True)

        feature_path = os.path.join(features_dir, "generated.feature--2")
        with open(feature_path, "w", encoding="utf-8") as f:
            f.write(result)

        print(f"✅ Saved to {feature_path}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        await browser.kill()


if __name__ == "__main__":
    url = input("Enter the URL: ").strip() or DEFAULT_URL
    asyncio.run(generate_gherkin(url))
