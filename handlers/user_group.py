import asyncio
from aiogram import types, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.methods.delete_message import DeleteMessage
from filters.chat_filter import ChatTypeFilter

from keyboards.inline_kb import simpe_inline_keyboard

user_group_router = Router()
user_group_router.message.filter(ChatTypeFilter(['group', 'supergroup']))


@user_group_router.message(CommandStart())
async def group_command_start(message: types.Message, bot: Bot):
    msg = await message.answer(text='Прейдите в ЛС с ботом для продолжения беседы:', reply_markup=simpe_inline_keyboard(buttons={'Общение в ЛС': 'https://t.me/Pizza_inventor_2_bot'}, sizes=(1,)))
    await asyncio.sleep(20)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await msg.delete()


@user_group_router.message(Command('get_id'))
async def group_command_get_administrators(message: types.Message, bot: Bot):
    if bot.chat_identification == 0:
        identi = message.chat.id
        bot.chat_identification = identi
        await message.delete()