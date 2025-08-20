import os
import re
from pathlib import Path
from api.clients.trackerggapi import TrackerGGAPI
from aiogram.types import Message, FSInputFile
from aiogram import Router
from aiogram.filters import Command
from decouple import config
from bot.utils.validation import validate_riot_id, get_error_message, APIError
from bot.create_bot import all_media_dir
import utils.card_generator as CardGen

tracker = TrackerGGAPI()

profile_router = Router()

async def get_enhanced_stats(riot_id: str, tagline: str):
    """Получение расширенной статистики (legacy функция)"""
    tracker = TrackerGGAPI()
    profile_data = await tracker.get_player_profile(riot_id, tagline)
    
    if not profile_data:
        return None
        
    summary = tracker.get_player_summary(profile_data)
    return summary

def sanitize_filename(name: str) -> str:
    """Заменяет пробелы на подчеркивания и удаляет опасные символы"""
    name = name.replace(' ', '_')
    name = re.sub(r'[<>:"/\\|?*\0]', '', name)
    return name

@profile_router.message(Command("profile"))
async def profile_stat(message: Message):
    """Основной обработчик команды /profile"""
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.answer("❌ Используйте: /profile name#tag\n\nПример: /profile Riot#123")
            return
    
        validation_result = validate_riot_id(args[1])
        if not validation_result:
            await message.answer(
                "❌ Неправильный формат Riot ID!\n\n"
                "Используйте: /profile name#tag\n"
                "• Имя: 3-16 символов\n"
                "• Тег: 3-5 символов\n\n"
                "Пример: /profile PlayerName#1234"
            )
            return

        riot_id, tagline = validation_result
        
        # Показываем сообщение о загрузке
        loading_msg = await message.answer(f"🔍 Создаю карточку для {riot_id}#{tagline}...")
        
        # Генерируем карточку
        card_path = await CardGen.generate_enhanced_profile_card(riot_id, tagline)
            
        if not card_path or not os.path.exists(card_path):
            await loading_msg.edit_text("❌ Не удалось создать карточку. Возможно, игрок не найден или нет данных.")
            return
        
        # Получаем данные для caption
        tracker_api = TrackerGGAPI()
        profile_data = await tracker_api.get_player_profile(riot_id, tagline)
        
        if profile_data:
            summary = tracker_api.get_player_summary(profile_data)
            
            # Формируем caption с текстовой статистикой
            caption_text = f"🎮 **{riot_id}#{tagline}**\n\n"
            
            if summary:
                # Получаем данные из current_season
                current_season = summary.get('current_season', {})
                
                # Ранг
                rank = current_season.get('rank') or "Не определен"
                caption_text += f"🏆 **Ранг:** {rank}\n"
                
                # Регион и уровень
                if summary.get('region'):
                    caption_text += f"🌍 **Регион:** {summary.get('region')}\n"
                if summary.get('account_level'):
                    caption_text += f"⭐ **Уровень:** {summary.get('account_level')}\n"
                
                # Матчи и винрейт
                matches = current_season.get('matches_played', 0) or 0
                win_rate = current_season.get('win_rate', 0) or 0
                caption_text += f"🎯 **Матчей:** {matches}\n"
                caption_text += f"📊 **Процент побед:** {win_rate:.1f}%\n"
                
                # K/D
                kd = current_season.get('kd_ratio', 0) or 0
                caption_text += f"⚔️ **K/D:** {kd:.2f}\n"
                
                # Любимый агент из топ агентов
                top_agents = summary.get('top_agents', [])
                if top_agents:
                    main_agent = top_agents[0]
                    agent_name = main_agent.get('name', 'Неизвестен')
                    agent_matches = main_agent.get('matches_played', 0) or 0
                    caption_text += f"🎭 **Любимый агент:** {agent_name} ({agent_matches} матчей)\n"
                    
                # Стиль игры
                play_style = summary.get('play_style', '')
                if play_style:
                    caption_text += f"🎨 **Стиль:** {play_style}\n"
            else:
                caption_text += "📊 Статистика с Tracker.gg"
        else:
            caption_text = f"🎮 **{riot_id}#{tagline}**\n📊 Статистика с Tracker.gg"
                
        # Отправляем карточку с caption
        try:
            photo_file = FSInputFile(card_path)
            await message.reply_photo(
                photo=photo_file, 
                caption=caption_text,
                parse_mode="Markdown"
            )
            await loading_msg.delete()
                
            # Удаляем временный файл
            await safe_delete_file(card_path)
                
        except Exception as e:
            await loading_msg.edit_text(f"❌ Ошибка при отправке карточки: {str(e)}")
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")



async def safe_delete_file(file_path: str):
    """Безопасное удаление файла"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Файл удален: {file_path}")
    except Exception as e:
        print(f"⚠️ Не удалось удалить файл {file_path}: {e}")
