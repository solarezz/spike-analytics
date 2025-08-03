"""
Entry point for running the bot as a module.
Usage: python -m bot
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from bot.aiogram_run import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())