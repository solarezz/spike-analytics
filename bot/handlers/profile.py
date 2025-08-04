from api.clients.henrik_client import HenrikAPIClient
from aiogram.types import Message
from aiogram import Router, F
from aiogram.filters import Command
from decouple import config
from bot.utils.validation import validate_riot_id, get_error_message, APIError

client = HenrikAPIClient(api_key=config("HENRIK_API"))

profile_router = Router()

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

        
        if error:
            await message.answer(get_error_message(error))
            return
        
        if player:
            await message.answer(player.format_for_telegram())
        else:
            await message.answer("❌ Не удалось получить данные игрока.")
            
    except Exception as e:
        print(f"Unexpected error in profile handler: {e}")
        await message.answer("⚠️ Произошла неожиданная ошибка. Попробуйте позже.")