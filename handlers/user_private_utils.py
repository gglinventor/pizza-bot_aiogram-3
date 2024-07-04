from aiogram import Bot, types
from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_banner, orm_get_products, orm_add_to_cart, orm_get_user_carts, orm_delete_from_cart, orm_reduce_product_in_cart, orm_get_question, orm_get_questions
from keyboards.inline_kb import get_user_main_buttons, get_user_catalog_buttons, get_products_buttons, get_user_cart, get_user_questions, get_user_answer, get_user_help, get_user_inline_support
from keyboards.pagination import Paginator


async def main_menu(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    keyboards = get_user_main_buttons(level=level, sizes=(2,2,2))
    
    return image, keyboards


async def catalog(session, level, menu_name, bot):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    categories = bot.food_category
    
    keyboards = get_user_catalog_buttons(level=level, categories=categories, sizes=(2,1,2))
    
    return image, keyboards


def pages(paginator: Paginator):
    buttons = dict()
    if paginator.has_previous():
        buttons["◀ Пред."] = 'previous'
        
    if paginator.has_naxt():
        buttons["След. ▶"] = 'next'
        
    return buttons


async def products(session, level, category, page, bot):
    products = await orm_get_products(session, category_id=category)
    if products:
        paginator = Paginator(products, page=page)
        product = paginator.get_page()[0]
    
        text = f"<strong>{product.name}</strong>\n{product.info}\nСтоимость: {round(product.price, 2)} {product.valute}"
        if product.comment != '' and product.comment != None:
            text += f'\n{product.comment}'
        image = InputMediaPhoto(media=product.image,
            caption=text+f"\n<strong>Товар {paginator.page} из {paginator.pages}</strong>")
    
        pagination_buttons = pages(paginator)
    
        keyboards = get_products_buttons(level=level, category=category, page=page, pagination_buttons=pagination_buttons, product_id=product.id)
    
    else:
        categories = bot.food_category
        banner = await orm_get_banner(session, 'main')
        image = InputMediaPhoto(media=banner.image, caption=f'Товаров категории "{categories[category - 1]}" нет 🤔')
    
        keyboards = get_user_main_buttons(level=0, sizes=(2,2,2))
        
    return image, keyboards


async def carts(session, level, menu_name, page, user_id, product_id):
    if menu_name == 'delete':
        await orm_delete_from_cart(session, user_id, product_id)
        if page > 1:
            page -= 1
    elif menu_name == 'decrement':
        result = await orm_reduce_product_in_cart(session, user_id, product_id)
        if page > 1 and result == False:
            page -= 1
    elif menu_name == 'increment':
        await orm_add_to_cart(session=session, user_id=user_id, product_id=product_id)
    
    carts = await orm_get_user_carts(session=session, user_id=user_id)

    if not carts:
        banner = await orm_get_banner(session=session, banner_name='cart')
        image = InputMediaPhoto(media=banner.image, caption=banner.description)
        keyboards = get_user_cart(level=level)
        
    else:
        paginator = Paginator(carts, page=page)
        cart = paginator.get_page()[0]
        
        cart_price = round(cart.quantity * cart.product.price, 2)
        all_price = round(sum(cart.quantity * cart.product.price for cart in carts), 2)
        image = InputMediaPhoto(media=cart.product.image, caption=f"<strong>{cart.product.name}</strong>\
            \n{round(cart.product.price, 2)} {cart.product.valute} x {cart.quantity} = {cart_price} {cart.product.valute}\
            \nСтоимость товаров во всей корзине: {all_price} {cart.product.valute}\nТовар {paginator.page} из {paginator.pages} товаров в корзине")
        
        pagination_buttons = pages(paginator)
        keyboards = get_user_cart(level=level, page=page, pagination_buttons=pagination_buttons, product_id=cart.product.id, user_id=user_id)
        
    return image, keyboards


async def questions(session: AsyncSession, menu_name: str):
    questions = await orm_get_questions(session)
    keyboards = get_user_questions(questions=questions)
    
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    
    return image, keyboards


async def answer(session: AsyncSession, level: int, menu_name: str, ques_id: int):
    question = await orm_get_question(session, ques_id)
    keyboards = get_user_answer(level=level)
    
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=f'<strong>{question.name}</strong>\n\n{question.info}')
    
    return image, keyboards    


async def get_user_content(session: AsyncSession, level: int, menu_name: str, bot: Bot | None = None, category: int | None = None, page: int | None = None, product_id: int | None = None, user_id: int | None = None, ques_id: int | None = None):
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog(session, level, menu_name, bot)
    elif level == 2:
        return await products(session, level, category, page, bot)
    elif level == 3:
        return await carts(session, level, menu_name, page, user_id, product_id)
    elif level == 4:
        return await questions(session, menu_name)
    elif level == 5:
        return await answer(session, level, menu_name=menu_name, ques_id=ques_id)


async def helping(level: int):
    text = 'У вас возникли трудности? Следующий набор кнопок постарается решить вашу проблему!\n\n1)Если возникли трудности с пониманием команд, нажмите на кнопку "Все команды"\n\n2)Если какая-то команда не работает, нажмите на кнопку "Ошибка"\n\n3)Если ничего не поможет, обратитесь в поддержку, нажав на кнопку "Тех. поддержка"'
    
    keyboards = get_user_help(level=level)
    
    return text, keyboards


async def helping_2(level: int, type_help: str):
    answers = {'all_command': '/start - команда для запуска бота\nПосле её нажатия присылается инлайн-карточка с различными кнопками:\nПри нажании кнопки "Товары" и выбора категории вы получите соответствующие товары пиццерии, а кнопкой "Купить" отправите их в корзину\nПри нажатии кнопки "Корзина" вы увидите ваши товары в корзине\nПри нажатии кнопки "О нас" вы получите краткую информацию о заведении\nПри нажатии кнопки "Вопросы" вы сможете получить ответы на частозадаваемые вопросы\nПри нажатии кнопки "Оплата" вы поличите варианты оплаты\nПри нажатии кнопки "Доставка" вы получите варианты доставки\n\n/help - команда для помощи пользователям\nПосле её нажатия присылается инлайн-карточка с различными кнопками:\nПри нажании кнопки "Все команды" вы получите список всех команд в боте\nПри нажании кнопки "Ошибка" вы получите информацию как действовать в случае ошибки в боте\nПри нажании кнопки "Тех. поддержка" вы узнаете, как и когда мы сможем вам помочь, если всё вышеперечисленное вам не помогло\n\n/info - команда для просмотра информации о боте',
                'error': '1)НЕВНИМАТЕЛЬНОСТЬ\nПрочитайте все сообщения в основной группе https://t.me/+7GW4GjeWaUI5MzMy возможно вы не заметили важных объявлений касающихся бота, например: "Временное отключение некоторых функций" и другие, или вы некорректно следовали указаниям бота. Также проверьте у себя подключение к интернету, это очень частая проблема у пользователей!\n\n2)НЕМНОГО ТЕРПЕНИЯ\nПодождите некотрое время, возможно бот был нагружен работой и ещё не успел ответить, возможно сервера телеграма зависли и не отвечают на запрос, но суть всего этого в том, что надо немного подождать или ещё раз отправить запрос боту.',
                'support': f'Если указания в кнопке "Ошибка" вам не помогли, то обратитесь за помощью к администратору https://t.me/GGL_Inventor но обращайтесь за помощью, если действительно трудная ситуация. Администратор - человек и ответит не сразу!' }
    
    text = answers.get(type_help)
    keyboards = get_user_inline_support()
    
    return text, keyboards


async def get_user_support(level: int, type_help: str | None = None):
    if level == 0:
        return await helping(level)
    if level == 1:
        return await helping_2(level, type_help)