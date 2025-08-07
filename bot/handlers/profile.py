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
        
        await loading_msg.delete()

        print(player)
        
        if error:
            await message.answer(get_error_message(error))
            return
        
        if player:
            safe_name = sanitize_filename(name)
            filename = f"{safe_name}-{tag}.png"
            output_path = Path(all_media_dir) / filename
            img_bytes = CardGen.generate_profile_card(player)
            try:
                with open(output_path, 'wb') as f:
                    f.write(img_bytes)
                
                # Отправляем фото
                photo_file = FSInputFile(path=output_path)
                await message.answer_photo(photo=photo_file)
                await message.answer(player.format_for_telegram())
                
            finally:
                # Удаляем временный файл
                if output_path.exists():
                    output_path.unlink()
        else:
            await message.answer("❌ Не удалось получить данные игрока.")
            
    except Exception as e:
        print(f"Unexpected error in profile handler: {e}")
        await message.answer("⚠️ Произошла неожиданная ошибка. Попробуйте позже.")