import os
import asyncio
from pathlib import Path

from browser_use import Agent, Browser, ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME") or "gpt-5"
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL") or "gpt-4.1-mini"
DEFAULT_URL = os.getenv("DEFAULT_URL", "https://www.pfizerforall.com")

LINKS_TASK_PROMPT = """Go to the given URL and find every link on the page by automation: navigate, scroll, open menus/dropdowns, and select links to build the list.

TASK:
1. Navigate to the URL (use the navigate action).
2. Find links by interacting with the page:
   - Scroll the page (header, body, footer) so all sections are visible.
   - Open any navigation dropdowns or menus (hover or click) to expose links inside them.
   - For each visible link, identify it (by its index in the interactive elements or by reading the page after scrolling/opening menus). Record the link text (visible text) and the full URL (href). You may use the extract action to get link text and URL from the current view after each scroll or menu open.
   - Cover the full page top to bottom and every dropdown/menu. Do not click links to follow them; only open menus and scroll to discover links, then record each link's text and url.
3. Use the write_file action to save the list to a file named "links.txt". Format: one link per line as "link_text | url" (literal pipe between text and url). Each url must be a full absolute URL.
4. When the file is written, call the done action.

Output only the link list in the file. No other files. No explanations in the file."""


async def get_links(url: str) -> Path | None:
	backend_dir = Path(__file__).resolve().parent
	links_path = backend_dir / "links.txt"

	browser = Browser(
		headless=False,
		minimum_wait_page_load_time=2.0,
		wait_for_network_idle_page_load_time=4.0,
		wait_between_actions=0.5,
	)

	llm = ChatOpenAI(model=MODEL_NAME, temperature=0)

	agent = Agent(
		browser=browser,
		llm=llm,
		task=f"{LINKS_TASK_PROMPT}\n\nURL:\n{url}",
		file_system_path=str(backend_dir),
		max_steps=25,
		llm_timeout=120,
		step_timeout=180,
	)

	try:
		history = await agent.run()
		result = history.final_result()
		if result:
			print("\n===== RESULT =====\n")
			print((result or "").strip())
			print("\n==================\n")
		if links_path.exists():
			print(f"✅ Links saved to {links_path}")
			return links_path
		print("⚠️ links.txt was not created; check agent steps.")
		return None
	except Exception as e:
		print(f"❌ Error: {e}")
		return None
	finally:
		await browser.kill()


if __name__ == "__main__":
	url = input("Enter the URL: ").strip() or DEFAULT_URL
	asyncio.run(get_links(url))
