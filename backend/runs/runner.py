"""Run the exported CodeAgent session (my_session.py)."""
import asyncio
import sys
from pathlib import Path

# Ensure backend/runs is on path so my_session can be imported
_runs_dir = Path(__file__).resolve().parent
if str(_runs_dir) not in sys.path:
	sys.path.insert(0, str(_runs_dir))

from my_session import main as my_session_main


async def main() -> None:
	await my_session_main()


if __name__ == "__main__":
	asyncio.run(main())
