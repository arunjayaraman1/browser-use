import os
import asyncio
from browser_use import Agent, Browser, ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-5.1")


async def generate_gherkin(url: str):
    browser = Browser(headless=False)

    task = f"""
Open {url}

Analyze the page and generate a Gherkin feature file.

GENERAL RULES (STRICT):
- Output ONLY raw Gherkin text
- No markdown, no explanations
- Use valid Gherkin syntax only
- Write behavior exactly as a real user experiences it
- Document ONLY visible UI elements
- Each UI element verification MUST be its own step
- Avoid assumptions about backend logic
- Use simple user actions like click, type, scroll, view

STRUCTURE:
Feature:
Background:
Scenario:

Focus on:
- Navigation
- Buttons
- Forms
- Menus
- Modals
- Visible text
"""

    agent = Agent(
        task=task,
        llm=ChatOpenAI(model=MODEL_NAME),
        browser=browser,
    )

    result = await agent.run()
    print(result)


if __name__ == "__main__":
    asyncio.run(generate_gherkin("https://nat-studio-pfizer.genai-newpage.com/sandbox-static"))
