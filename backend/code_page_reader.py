"""
Gherkin generator using CodeAgent: same goal as page_reader.py but the agent
writes and executes Python code (navigate, click, extract, etc.) and we export
the session as a Python script and Jupyter notebook.
"""

import os
import asyncio
from pathlib import Path

from browser_use import Browser, CodeAgent
from browser_use.code_use.notebook_export import export_to_ipynb, session_to_python_script
from browser_use.code_use.views import CellType
from dotenv import load_dotenv

load_dotenv()

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
- page_title MUST be the actual document title or "N/A"; never use "undefined".
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
  | link_text | url_value |

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
Return ONLY the final Gherkin feature text. Nothing before or after. When done, call done(text=<gherkin_string>, success=True) with the raw Gherkin string.
"""


async def generate_gherkin(url: str) -> None:
	backend_dir = Path(__file__).resolve().parent
	runs_dir = backend_dir / "runs"
	features_dir = backend_dir / "features"
	runs_dir.mkdir(parents=True, exist_ok=True)
	features_dir.mkdir(parents=True, exist_ok=True)

	browser = Browser(
		headless=False,
		minimum_wait_page_load_time=2.0,
		wait_for_network_idle_page_load_time=6.0,
		wait_between_actions=1.5,
	)
	await browser.start()

	agent = CodeAgent(
		browser=browser,
		task=f"{AGENT_PROMPT}\n\nWEBSITE:\n{url}",
		max_steps=35,
	)

	try:
		await agent.run()
		history = agent.history
		result = history.final_result()

		# Export CodeAgent session as Python script and Jupyter notebook
		script = session_to_python_script(agent)
		script_path = runs_dir / "my_session.py"
		script_path.write_text(script, encoding="utf-8")
		print(f"✅ Session script saved to {script_path}")

		# Coding file: only the code cells the agent wrote/executed (no boilerplate)
		code_lines = []
		for i, cell in enumerate(agent.session.cells):
			if cell.cell_type == CellType.CODE and cell.source.strip():
				code_lines.append(f"# Cell {i + 1}\n")
				code_lines.append(cell.source.rstrip())
				code_lines.append("\n\n")
		coding_path = runs_dir / "agent_code.py"
		coding_path.write_text("".join(code_lines).strip() or "# No code cells executed\n", encoding="utf-8")
		print(f"✅ Coding file saved to {coding_path}")

		notebook_path = runs_dir / "my_session.ipynb"
		export_to_ipynb(agent, notebook_path)
		print(f"✅ Session notebook saved to {notebook_path}")

		if not result or len(result.strip()) < 20:
			print("❌ No valid Gherkin generated")
			return

		result = result.strip()
		# Normalize invalid values from agent output
		result = result.replace("| undefined |", "| N/A |")
		print("\n===== GENERATED GHERKIN =====\n")
		print(result)
		print("\n============================\n")

		feature_path = features_dir / "generated_code_agent.feature"
		feature_path.write_text(result, encoding="utf-8")
		print(f"✅ Gherkin saved to {feature_path}")

	except Exception as e:
		print(f"❌ Error: {e}")
		raise
	finally:
		await agent.close()


if __name__ == "__main__":
	url = input("Enter the URL: ").strip() or DEFAULT_URL
	asyncio.run(generate_gherkin(url))
