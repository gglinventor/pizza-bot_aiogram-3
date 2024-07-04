from aiogram import Bot, types
from aiogram.filters import Filter

class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types
    
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types
    
class Is_Administrator(Filter):
    def __init__(self) -> None:
        pass
    
    async def __call__(self, message: types.Message, bot: Bot) -> bool:
        return message.from_user.id in bot.admins_list