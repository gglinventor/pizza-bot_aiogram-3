from aiogram import types, Router, Bot, F
from aiogram.filters import CommandStart, Command
from aiogram.exceptions import TelegramBadRequest
from filters.chat_filter import ChatTypeFilter
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.user_private_utils import get_user_content, get_user_support
from database.orm_query import orm_add_user, orm_get_users, orm_add_to_cart, orm_get_carts, orm_get_user_carts
from keyboards.inline_kb import UserCallBack, HelpCallBack, get_user_help
from keyboards.pagination import List_of_Carts

user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(['private']))


@user_private_router.message(CommandStart())
async def user_command_start(message: types.Message, session):
    media, reply_markup = await get_user_content(session, level=0, menu_name='main')
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)
    await message.delete()


async def add_to_cart(callback: types.CallbackQuery, callback_data: UserCallBack, session: AsyncSession):
    user = callback.from_user
    users = await orm_get_users(session)
    carts = await orm_get_carts(session)
    if user.username:
        user_info = user.username
    else:
        user_info = user.full_name
    await orm_add_user(session=session, id=len(users) + 1, user_id=user.id, username=user_info, phone=None)
    await orm_add_to_cart(session=session, id=len(carts) + 1, user_id=user.id, product_id=callback_data.product_id)
    await callback.answer('Товар добавлен в корзину')


async def order_from_user(session: AsyncSession, callback_data: UserCallBack, bot: Bot):
    carts = await orm_get_user_carts(session=session, user_id=callback_data.order_user)
    list_of_Carts = List_of_Carts(carts)
    carts = list_of_Carts.get_carts()
    for admin in bot.pizza_admins:
        all_price = 0
        await bot.send_message(chat_id=admin, text=f'Поступил новый заказ от @{carts[0].user.username} 🙋‍♂️:')
        for cart in carts:
            local_price = round(cart.product.price * cart.quantity, 2)
            all_price += local_price
            await bot.send_photo(admin, photo=cart.product.image, caption=f'<strong>{cart.product.name}</strong>\nЦена: {round(cart.product.price, 2)} x {cart.quantity} = {local_price} {cart.product.valute}')
        await bot.send_message(admin, f'Общая цена: {round(all_price, 2)} {cart.product.valute}')
    

@user_private_router.callback_query(UserCallBack.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: UserCallBack, session: AsyncSession, bot: Bot):
    if callback_data.menu_name == 'add_to_cart':
        await add_to_cart(callback, callback_data, session)
        return
    elif callback_data.order_user:
        await order_from_user(session, callback_data, bot)
        await callback.message.answer('Вы успешно оформили заказ, ожидайте его 🤗\nP.s. тут могла бы быть ваша реклама')
        
    
    media, reply_markup = await get_user_content(session, level=callback_data.level,
        menu_name=callback_data.menu_name, category=callback_data.category, page=callback_data.page,
        product_id=callback_data.product_id, user_id=callback.from_user.id, bot=bot, ques_id=callback_data.ques_id)
    try:
        await callback.message.edit_media(media=media, reply_markup=reply_markup)
        await callback.answer()
    except TelegramBadRequest:
        await callback.answer('Вы уже нажали на кнопку!')
    

@user_private_router.message(Command('help', ignore_case=True))
async def user_command_help(message: types.Message):
    text, reply_markup = await get_user_support(level=0)
    await message.answer(text=text, reply_markup=reply_markup)
    await message.delete()


@user_private_router.callback_query(HelpCallBack.filter())
async def user_support(callback: types.CallbackQuery, callback_data: HelpCallBack):
    text, reply_markup = await get_user_support(level=callback_data.level, type_help=callback_data.type_help)

    await callback.message.edit_text(text=text, reply_markup=reply_markup)
    await callback.answer()
    

@user_private_router.message(Command('info', ignore_case=True))
async def user_command_info(message: types.Message):
    await message.answer('Разработчик-программист: @GGL_Inventor\nИнформационный безопасник: @GGL_Inventor\nТестировщик: @GGL_Inventor\n\nВерсия фреймворка: aiogram 3.7.0')


@user_private_router.message(Command('admin_start'))
async def user_command_get_administrators(message: types.Message, bot: Bot):
    id = bot.chat_identification
    administrators = await bot.get_chat_administrators(chat_id=id)
    administrators = [member.user.id for member in administrators if member.status == 'administrator' or member.status == 'creator']
    bot.admins_list = administrators
    if message.from_user.id in administrators:
        if message.chat.id not in bot.pizza_admins:
            bot.pizza_admins.append(message.chat.id)
        await message.delete()
