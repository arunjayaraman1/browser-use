
import os
import asyncio
from browser_use import Agent, Browser, ChatOpenAI, ChatBrowserUse
# from dotenv import load_dotenv

# load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5")


async def generate_gherkin(url: str):
    browser = Browser(
        headless=False,
        minimum_wait_page_load_time=3.0,
        wait_for_network_idle_page_load_time=8.0,
        wait_between_actions=2.0,
    )

    task = f"""
You are a Senior QA Automation Engineer specialized in Behavior-Driven Development (BDD).

WEBSITE UNDER TEST:
{url}

OBJECTIVE:
Analyze the entire visible UI of this website and generate ONE complete Gherkin Feature file that validates real end-user behavior.

STRICT GLOBAL RULES:
- Output ONLY raw Gherkin text.
- DO NOT use markdown.
- DO NOT include explanations, comments, or code blocks.
- DO NOT mention selectors, IDs, classes, or DOM terms.
- Write behavior exactly as a human user experiences it.
- Avoid duplicate or redundant scenarios.
- Every interactive UI element must have at least one scenario.
- Include both Positive and Negative scenarios wherever applicable.
- Validate UI text, labels, state changes, navigation, and notifications.
- Use professional QA phrasing only.

ELEMENT COVERAGE RULES:

BUTTONS:
- Click action
- UI change or result
- Notification/banner validation if present
- Negative scenario if prerequisites are missing

FORMS:
- Field presence validation
- Successful submission
- Missing required fields
- Invalid formats
- Notification validation after submission

DROPDOWNS:
- Opening dropdown
- Selecting an option
- Verifying selected value/label
- Negative scenario for no selection or invalid selection

LINKS / NAVIGATION:
- Navigation trigger
- Correct destination validation
- Menu interaction if applicable

INPUT FIELDS:
- Typing valid value
- Typing invalid value
- Empty input validation

TOGGLES / SWITCHES / CHECKBOXES:
- Enable/disable behavior
- State change validation

NOTIFICATIONS / ALERTS:
- Validate exact visible text
- Validate visibility after action
- Validate placement inside notification/alert area if present

SCENARIO STRUCTURE RULES:
- Use Feature, Background, Scenario, Scenario Outline only when necessary.
- Use Given / When / Then / And correctly.
- Each step must describe visible user behavior.
- No technical terms.
- No assumptions about backend logic.
- No test data unless clearly visible on UI.
- Do not invent features that are not visible.

QUALITY RULES:
- Prefer clarity over quantity.
- Avoid repeating the same behavior in multiple scenarios.
- Group related behaviors logically.
- Ensure professional QA language.

FINAL OUTPUT REQUIREMENT:
Return ONLY the final Gherkin Feature file text.
Nothing before it.
Nothing after it.
No explanations.


    """
    primary_llm = ChatOpenAI(model=MODEL_NAME, temperature=0)

    agent = Agent(
        browser=browser,
        llm=primary_llm,
        task=task,
        max_steps=200,
        llm_timeout=180,
        step_timeout=300,
        max_retries=2,
        max_failures=5,
    )

    history = await agent.run()
    result = history.final_result()

    await browser.kill()

    if not result:
        print("❌ No Gherkin generated")
        return

    print("\n===== GENERATED GHERKIN =====\n")
    print(result)
    print("\n============================\n")

    # Optional: save to file
    features_dir = os.path.join(os.path.dirname(__file__), "features")
    os.makedirs(features_dir, exist_ok=True)
    feature_path = os.path.join(features_dir, "generated.feature2")
    with open(feature_path, "w", encoding="utf-8") as f:
        f.write(result)
        print("✅ Saved to generated.feature")


if __name__ == "__main__":
    asyncio.run(
        generate_gherkin(
            input("Enter the URL: ") or "https://nat-studio-pfizer.genai-newpage.com/sandbox-static"
        )
    )