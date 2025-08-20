import os
import re
from pathlib import Path
from api.clients.trackerggapi import TrackerGGAPI
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.filters import Command
from decouple import config
from bot.utils.validation import validate_riot_id, get_error_message, APIError
from bot.create_bot import all_media_dir
import utils.card_generator as CardGen
from aiogram.types import CallbackQuery

tracker = TrackerGGAPI()

profile_router = Router()

async def get_enhanced_stats(riot_id: str, tagline: str):
    tracker = TrackerGGAPI()
    profile_data = await tracker.get_player_profile(riot_id, tagline)
    
    if not profile_data:
        return None
        
    summary = tracker.get_player_summary(profile_data)
    return summary

def sanitize_filename(name: str) -> str:
    """Заменяет пробелы на подчеркивания и удаляет опасные символы"""
    # Сохраняем пробелы, заменяя их на подчеркивания
    name = name.replace(' ', '_')
    # Удаляем только действительно опасные символы для файловых систем
    name = re.sub(r'[<>:"/\\|?*\0]', '', name)
    return name

@profile_router.message(Command("profile"))
async def profile_stat(message: Message):
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
                
        else:  # basic
            # Используем старый код для basic карточки
            stats = await get_enhanced_stats(riot_id, tagline)
        
        if not stats:
            await loading_msg.edit_text("❌ Не удалось получить данные игрока")
            return
        text = f"""🎯 **{stats['riot_id']}** 
        
📊 **Текущий сезон ({stats['current_season']['season_name']})**
├ 🎮 Матчей: {stats['current_season']['matches_played']}
├ 🏆 Винрейт: {stats['current_season']['win_rate']:.1f}%
├ ⚔️ K/D: {stats['current_season']['kd_ratio']:.2f}
├ 🎯 Хэдшоты: {stats['current_season']['headshot_percentage']:.1f}%
└ 🔥 Клатчи: {stats['clutch_master']['clutch_percentage']:.1f}%

🏅 **Топ агенты**"""
        
        for i, agent in enumerate(stats['top_agents'][:3], 1):
            text += f"\n{i}. {agent['name']} ({agent['role']}) - {agent['matches_played']} игр"
            
        text += f"""

🎭 **Стиль игры:** {stats['play_style']}
🎪 **Основная роль:** {stats['main_role']}
👁 **Просмотров профиля:** {stats['profile_views']}"""

        
        if stats:
            # Генерируем карточку (файл создается в корне проекта)
            img_bytes = CardGen.generate_profile_card(stats)
            
            # Определяем путь к созданному файлу
            safe_name = sanitize_filename(name)
            filename = f"{safe_name}-{tag}.png"
            
            # ПРАВИЛЬНЫЙ путь: корневая папка проекта (spike-analytics/)
            # Текущий файл: spike-analytics/bot/handlers/profile.py
            # Нужно подняться на 2 уровня вверх
            current_file = Path(__file__)
            print(f"Текущий файл: {current_file}")
            print(f"Parent: {current_file.parent}")
            print(f"Parent.parent: {current_file.parent.parent}")
            print(f"Parent.parent.parent: {current_file.parent.parent.parent}")
            
            project_root = current_file.parent.parent.parent  # spike-analytics/
            generated_file_path = project_root / filename
            
            try:
                print(f"Ожидаемый путь к файлу: {generated_file_path}")
                print(f"Файл существует: {generated_file_path.exists()}")
                
                # Проверим также все файлы в корневой папке
                print(f"Файлы в корневой папке:")
                for file in project_root.glob("*.png"):
                    print(f"  - {file}")
                
                # Отправляем фото напрямую из корневой папки
                if generated_file_path.exists():
                    photo_file = FSInputFile(path=generated_file_path)
                    await message.answer_photo(photo=photo_file, caption=text)
                    await loading_msg.delete()
                else:
                    await message.answer("⚠️ Файл карточки не был создан.")
                
            except Exception as e:
                print(f"Error in profile generation: {e}")
                await message.answer("⚠️ Ошибка при генерации карточки профиля.")
            finally:
                # Простое удаление файла через os.remove
                try:
                    if generated_file_path.exists():
                        os.remove(generated_file_path)
                        print(f"Файл {generated_file_path} успешно удален")
                    else:
                        print(f"Файл {generated_file_path} не существует для удаления")
                except Exception as delete_error:
                    print(f"Ошибка при удалении файла {generated_file_path}: {delete_error}")
        else:
            await message.answer("❌ Не удалось получить данные игрока.")
            
    except Exception as e:
        print(f"Unexpected error in profile handler: {e}")
        await message.answer("⚠️ Произошла неожиданная ошибка. Попробуйте позже.")