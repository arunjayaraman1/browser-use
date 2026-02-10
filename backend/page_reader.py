import os
import asyncio
from browser_use import Agent, Browser, ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME") or "gpt-5"
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL") or "gpt-4.1-mini"
# DEFAULT_URL = "https://www.pfizerforall.com"
DEFAULT_URL = "https://www.tukysa.com"


AGENT_PROMPT = """
Analyze the given webpage and test ALL navigation links. Output EXACTLY ONE valid Gherkin Feature file.

GOAL:
Validate navigation for:
1) Links directly visible on the page.
2) Links inside EVERY dropdown or menu in the navigation bar.

OUTPUT RULES (STRICT):
- Output ONLY raw Gherkin text.
- Do NOT use markdown, code blocks, bullet points, JSON, or explanations.
- Use ONLY valid Gherkin keywords: Feature, Background, Scenario Outline, Scenario, Given, When, Then, And, Examples.
- Produce EXACTLY one Feature.
- Always include ONE Background section with the base page URL.
- Use Scenario Outline for multiple links.
- Use Scenario only if there is a single unique case.
- Never output labels outside tables.
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

Examples:
  | link_text | url_value |

Scenario Outline: Validate dropdown link navigation
  When I open the "<dropdown_name>" menu
  And I click the "<link_text>" link
  Then I should be navigated to "<url_value>"

Examples:
  | dropdown_name | link_text | url_value |

DATA COLLECTION RULES:

WHEN TO COUNT AS SUCCESS:
- If the page loads and shows anything (content, blank but loaded, SPA shell, etc.), treat the navigation as SUCCESS. Record the current URL and return to homepage.
- Count as FAILURE only when: the page is clearly broken (e.g. "Page not found", "404", "Something went wrong", server error message) or there is a DNS/connection error (e.g. "Can't reach this page", "DNS_PROBE_*"). Otherwise, consider the step successful and record the url_value.

DIRECT PAGE LINKS:
- Identify every visible clickable link on the homepage.
- Record link_text and full absolute url_value.
- Capture carousel or slider links from beginning to end.

DROPDOWN / MENU LINKS:
- Open each navigation dropdown or menu (hover or click).
- For each link inside it:
  - Record dropdown_name, link_text, full absolute url_value.
- Must check ALL dropdowns from top to bottom.

NAVIGATION VALIDATION:
- For each link verify only that the browser URL changes correctly.
- Returning to homepage after each check is mandatory.
- DO NOT write "navigate back" steps in Gherkin.

CONSTRAINTS:
- Success = page loaded (anything other than a broken/error page or DNS error). Do not require visible interactives or rich content.
- Use ONLY text and URLs actually visible in the UI.
- DO NOT invent links or names.
- DO NOT summarize destination content.
- ONLY confirm navigation and capture final full URL.
- Cover the entire homepage from top to bottom.
- Return ONLY the final Gherkin feature text. Nothing before or after.
- Strictly Open the links in the same tab.

"""

from browser_use.llm.messages import BaseMessage, UserMessage

CORRECTION_PROMPT = """Correct and clean the following Gherkin feature file. Fix syntax (matching Examples columns to steps,group scenarios outline 
by dropdown name , no duplicate rows, valid pipes). Return ONLY the corrected raw Gherkin text, no markdown or explanation.

Feature file to correct:

{feature_content}
"""


def _get_correction_llm():
    try:
        from langchain_openai import ChatOpenAI as LangChainChatOpenAI
        from examples.models.langchain.chat import ChatLangchain
        return ChatLangchain(chat=LangChainChatOpenAI(model=MODEL_NAME, temperature=0))
    except Exception:
        return None


async def correct_gherkin(gherkin: str) -> str:
    """Send gherkin text to an LLM for correction. Returns corrected Gherkin string."""
    llm = _get_correction_llm()
    if llm is None:
        return gherkin
    prompt = CORRECTION_PROMPT.format(feature_content=gherkin)
    messages: list[BaseMessage] = [UserMessage(content=prompt)]
    response = await llm.ainvoke(messages)
    return str(response.completion).strip()

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
            return None

        result = result.strip()

        print("\n===== GENERATED GHERKIN =====\n")
        print(result)
        print("\n============================\n")

        print(asyncio.run(correct_gherkin(result)))
        # Save to file
        features_dir = os.path.join(os.path.dirname(__file__), "features")
        os.makedirs(features_dir, exist_ok=True)

        feature_path = os.path.join(features_dir, "generated.feature--5")
        with open(feature_path, "w", encoding="utf-8") as f:
            f.write(result)

        print(f"✅ Saved to {feature_path}")
        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

    finally:
        await browser.kill()


if __name__ == "__main__":
    url = input("Enter the URL: ").strip() or DEFAULT_URL
    gherkin = asyncio.run(generate_gherkin(url))
    if gherkin is not None:
        print("\n===== CORRECTED GHERKIN =====\n")
        print(asyncio.run(correct_gherkin(gherkin)))

        print("\n=============================\n")