from api.clients.henrik_client import HenrikAPIClient
from aiogram.types import Message
from aiogram import Router, F
from aiogram.filters import Command
from decouple import config

client = HenrikAPIClient(api_key=config("HENRIK_API"))

profile_router = Router()

@profile_router.message(Command("profile"))
async def profile_stat(message: Message):
    await message.answer("Отправляю запрос!")
    
    # Получаем аргументы команды (все после /profile)
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or "#" not in args[1]:
        await message.answer("❌ Используйте: /profile name#tag")
        return
    
    name, tag = args[1].split("#", 1)

    
    player = client.get_full_player_info(name, tag)
    
    if player:
        await message.answer(player.format_for_telegram())
    else:
        await message.answer("❌ Не удалось получить данные игрока. Проверьте правильность имени и тега.")