import os
import re
from pathlib import Path
from api.clients.trackerggapi import TrackerGGAPI
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import Router, F
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
        
        # Создаем инлайн кнопки для выбора типа карточки
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Enhanced (Tracker.gg)", callback_data=f"enhanced:{riot_id}:{tagline}"),
                InlineKeyboardButton(text="📊 Basic (Riot API)", callback_data=f"basic:{riot_id}:{tagline}")
            ]
        ])
        
        await message.answer(
            f"🎯 **Профиль: {riot_id}#{tagline}**\n\n"
            "Выберите тип карточки:\n"
            "• **Enhanced** - полная статистика с Tracker.gg\n"
            "• **Basic** - базовая информация с Riot API",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@profile_router.callback_query(F.data.startswith('enhanced:') | F.data.startswith('basic:'))
async def handle_profile_callback(callback: CallbackQuery):
    """Обработчик callback для выбора типа карточки"""
    try:
        await callback.answer()
        
        data_parts = callback.data.split(':', 2)
        if len(data_parts) != 3:
            await callback.message.edit_text("❌ Ошибка в данных запроса")
            return
        
        card_type, riot_id, tagline = data_parts
        
        loading_msg = await callback.message.edit_text(
            f"🔍 Создаю {card_type} карточку для {riot_id}#{tagline}..."
        )
        
        if card_type == 'enhanced':
            # Генерируем enhanced карточку
            card_path = await CardGen.generate_enhanced_profile_card(riot_id, tagline)
            
            if not card_path or not os.path.exists(card_path):
                await loading_msg.edit_text("❌ Не удалось создать enhanced карточку. Возможно, игрок не найден или нет данных.")
                return
                
            # Отправляем enhanced карточку
            try:
                photo_file = FSInputFile(card_path)
                await callback.message.reply_photo(
                    photo=photo_file, 
                    caption=f"🚀 **Enhanced карточка**\n{riot_id}#{tagline}\n\n📊 Данные с Tracker.gg",
                    parse_mode="Markdown"
                )
                await loading_msg.delete()
                
                # Удаляем временный файл
                await safe_delete_file(card_path)
                
            except Exception as e:
                await loading_msg.edit_text(f"❌ Ошибка при отправке карточки: {str(e)}")
                
        else:  # basic
            # Используем старый код для basic карточки
            await loading_msg.edit_text("❌ Basic карточки пока недоступны. Используйте Enhanced.")
                
    except Exception as e:
        await callback.message.edit_text(f"⚠️ Произошла неожиданная ошибка: {str(e)}")

async def safe_delete_file(file_path: str):
    """Безопасное удаление файла"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Файл удален: {file_path}")
    except Exception as e:
        print(f"⚠️ Не удалось удалить файл {file_path}: {e}")
