#!/usr/bin/env python3
"""
Production-ready bot runner.
Run from project root: python run_bot.py
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now import and run the bot
from bot.aiogram_run import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())