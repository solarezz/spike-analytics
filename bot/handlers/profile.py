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
    
    if len(args) < 2:
        await message.answer("❌ Неправильный формат! Используйте: /profile name#tag")
        return
    
    name_tag_str = args[1]
    
    if "#" not in name_tag_str:
        await message.answer("❌ Неправильный формат! Используйте: /profile name#tag")
        return
    
    name_tag = name_tag_str.split("#")
    
    if len(name_tag) != 2:
        await message.answer("❌ Неправильный формат! Используйте: /profile name#tag")
        return
    
    player_data = client.get_player_stats(name_tag[0], name_tag[1])
    
    if player_data:
        await message.answer(str(player_data))
    else:
        await message.answer("❌ Не удалось получить данные игрока. Проверьте правильность имени и тега.")