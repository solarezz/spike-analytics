import os
import re
from pathlib import Path
from api.clients.henrik_client import HenrikAPIClient
from aiogram.types import Message, FSInputFile
from aiogram import Router, F
from aiogram.filters import Command
from decouple import config
from bot.utils.validation import validate_riot_id, get_error_message, APIError
from bot.create_bot import all_media_dir
import utils.card_generator as CardGen

client = HenrikAPIClient(api_key=config("HENRIK_API"))

profile_router = Router()

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
        if not validate_riot_id:
            await message.answer(
                "❌ Неправильный формат Riot ID!\n\n"
                "Используйте: /profile name#tag\n"
                "• Имя: 3-16 символов\n"
                "• Тег: 3-5 символов\n\n"
                "Пример: /profile PlayerName#1234"
            )
            return
        
        name, tag = validation_result
        
        loading_msg = await message.answer("🔍 Ищу игрока...")
        
        player, error = await client.get_full_player_info(name, tag)
        

        print(player)
        
        if error:
            await message.answer(get_error_message(error))
            return
        
        if player:
            # Генерируем карточку (файл создается в корне проекта)
            img_bytes = CardGen.generate_profile_card(player)
            
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
                    await message.answer_photo(photo=photo_file)
                    await loading_msg.delete()
                    await message.answer(player.format_for_telegram())
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