import asyncio, os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from handlers.user_private import user_private_router
from handlers.user_group import user_group_router
from handlers.admin_private import admin_private_router
from middlewares.db_session import DataBaseSession
from database.engine import create_database, drop_database, session_maker
from text_info.bot_commands import user_private

bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
bot.admins_list = []
bot.pizza_admins = []
bot.chat_identification = 0
bot.not_instruction = []
bot.food_category = ['Пицца 🍕', 'Напитки 🍹', 'Закуски 🍪']

dp = Dispatcher()

dp.include_router(user_private_router)
dp.include_router(user_group_router)
dp.include_router(admin_private_router)

async def on_startup():
    #await drop_database()
    await create_database()
    print('bot start successful')
    
async def on_shutdown():
    print('bot disconnected')

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=user_private, scope=types.BotCommandScopeAllPrivateChats())
    #await bot.set_my_commands(commands=admin_private, scope=types.BotCommandScopeChatAdministrators())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())    

asyncio.run(main())

