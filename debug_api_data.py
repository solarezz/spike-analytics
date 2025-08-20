#!/usr/bin/env python3
"""
Отладка данных от API
"""
import asyncio
from api.clients.trackerggapi import TrackerGGAPI

async def debug_api_data():
    api = TrackerGGAPI()
    enhanced_stats = await api.get_enhanced_player_stats("porsche enjoyer", "ILD")
    
    if enhanced_stats:
        print("🔍 Все данные от API:")
        for key, value in enhanced_stats.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Не удалось получить данные")

if __name__ == "__main__":
    asyncio.run(debug_api_data())
