from aiogram import types
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


def simpe_inline_keyboard(*, buttons: dict[str, str], sizes: tuple[int]):
    keyboard = InlineKeyboardBuilder()
    
    for text, value in buttons.items():
        if '://' in value:
            keyboard.add(InlineKeyboardButton(text=text, url=value))
        else:
            keyboard.add(InlineKeyboardButton(text=text, callback_data=value))
        
    return keyboard.adjust(*sizes).as_markup()


class UserCallBack(CallbackData, prefix='menu'):
    level: int
    menu_name: str
    category: int | None = None
    page: int = 1
    product_id: int | None = None
    order_user: int | None = None
    ques_id: int | None = None
    

class HelpCallBack(CallbackData, prefix='help'):
    level: int
    type_help: str | None = None

    
def get_user_main_buttons(*, level: int, sizes: tuple[int]):
    keyboard = InlineKeyboardBuilder()
    
    buttons = {
        'Товары 🥘': 'catalog',
        'Корзина 🛒': 'cart',
        'О нас 📕': 'about',
        'Вопросы ❓': 'question',
        'Оплата 💰': 'payment',
        'Доставка 🚗': 'shipping',
    }
    for text, menu_name in buttons.items():
        if menu_name == 'catalog':
            keyboard.add(InlineKeyboardButton(text=text, callback_data=UserCallBack(level=level + 1, menu_name=menu_name).pack()))
        elif menu_name == 'cart':
            keyboard.add(InlineKeyboardButton(text=text, callback_data=UserCallBack(level=3, menu_name=menu_name).pack()))
        elif menu_name == 'question':
            keyboard.add(InlineKeyboardButton(text=text, callback_data=UserCallBack(level=4, menu_name=menu_name).pack()))
        else:
            keyboard.add(InlineKeyboardButton(text=text, callback_data=UserCallBack(level=level, menu_name=menu_name).pack()))
            
    return keyboard.adjust(*sizes).as_markup()


def get_user_catalog_buttons(*, level: int, categories: list, sizes: tuple[int]):
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Назад ↩️', callback_data=UserCallBack(level=level-1, menu_name='main').pack()))
    keyboard.add(InlineKeyboardButton(text='Корзина 🛒', callback_data=UserCallBack(level=3, menu_name='cart').pack()))

    for category in categories:
        keyboard.add(InlineKeyboardButton(text=category, callback_data=UserCallBack(level=2, menu_name=category, category=categories.index(category) + 1).pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_products_buttons(*, level: int, category: int, page: int, pagination_buttons: dict, product_id: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Назад ↩️', callback_data=UserCallBack(level=level-1, menu_name='catalog').pack()))
    keyboard.add(InlineKeyboardButton(text='Корзина 🛒', callback_data=UserCallBack(level=3, menu_name='cart').pack()))
    keyboard.add(InlineKeyboardButton(text='Купить 💶', callback_data=UserCallBack(level=level, menu_name='add_to_cart', product_id=product_id).pack()))

    keyboard.adjust(*sizes)
    
    add_keyboard = []
    for text, menu_name in pagination_buttons.items():
        if menu_name == 'next':
            add_keyboard.append(InlineKeyboardButton(text=text, callback_data=UserCallBack(level=level, menu_name=menu_name, category=category, page=page + 1).pack()))
        
        elif menu_name == 'previous':
            add_keyboard.append(InlineKeyboardButton(text=text, callback_data=UserCallBack(level=level, menu_name=menu_name, category=category, page=page - 1).pack()))
    
    return keyboard.row(*add_keyboard).as_markup()


def get_user_cart(*, level: int, page: int | None = None, pagination_buttons: dict | None = None, product_id: int | None = None, sizes: tuple[int] = (3,), user_id: int | None = None):
    keyboard = InlineKeyboardBuilder()
    
    if page:
        keyboard.add(InlineKeyboardButton(text='Удалить', callback_data=UserCallBack(level=level, menu_name='delete', product_id=product_id, page=page).pack()))
        keyboard.add(InlineKeyboardButton(text='-1', callback_data=UserCallBack(level=level, menu_name='decrement', product_id=product_id, page=page).pack()))
        keyboard.add(InlineKeyboardButton(text='+1', callback_data=UserCallBack(level=level, menu_name='increment', product_id=product_id, page=page).pack()))

        keyboard.adjust(*sizes)
        
        add_keyboard = []
        for text, menu_name in pagination_buttons.items():
            if menu_name == 'next':
                add_keyboard.append(InlineKeyboardButton(text=text, callback_data=UserCallBack(level=level, menu_name=menu_name, page=page + 1).pack()))
        
            elif menu_name == 'previous':
                add_keyboard.append(InlineKeyboardButton(text=text, callback_data=UserCallBack(level=level, menu_name=menu_name, page=page - 1).pack()))
    
        keyboard.row(*add_keyboard)
    
        add_keyboard_2 = [
            InlineKeyboardButton(text='Главная 🏡', callback_data=UserCallBack(level=0, menu_name='main').pack()),
            InlineKeyboardButton(text='Заказать 📦', callback_data=UserCallBack(level=0, menu_name='main', order_user=user_id).pack())
        ]
        return keyboard.row(*add_keyboard_2).as_markup()

    else:
        keyboard.add(InlineKeyboardButton(text='Главная 🏡', callback_data=UserCallBack(level=0, menu_name='main').pack()))
        return keyboard.adjust(*sizes).as_markup()
        
    
def get_user_questions(*, questions: list | tuple, sizes: tuple[int] = (1,)):
    keyboard = InlineKeyboardBuilder()
    for question in questions:
        print(question.name, question.id, type(question.name), type(question.id))
        keyboard.add(InlineKeyboardButton(text=question.name, callback_data=UserCallBack(level=5, menu_name='answer', ques_id=question.id).pack()))
    
    keyboard.add(InlineKeyboardButton(text='Назад ↩️', callback_data=UserCallBack(level=0, menu_name='main').pack()))
    
    return keyboard.adjust(*sizes).as_markup()


def get_user_answer(*, level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text='Назад ↩️', callback_data=UserCallBack(level=level - 1, menu_name='question').pack()))
    keyboard.add(InlineKeyboardButton(text='Главная 🏡', callback_data=UserCallBack(level=0, menu_name='main').pack()))
    
    return keyboard.adjust(*sizes).as_markup()


def get_user_help(*, level: int, sizes: tuple[int] = (3,)):
    keyboard = InlineKeyboardBuilder()
    buttons = {
        'Все команды 📖':'all_command',
        'Ошибка 🔧':'error',
        'Техподдержка 🦸‍♂️':'support'
    }
    
    for text, type_help in buttons.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=HelpCallBack(level=level + 1, type_help=type_help).pack()))
    
    return keyboard.adjust(*sizes).as_markup()


def get_user_inline_support(*, sizes: tuple[int] = (1,)):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Назад ↩️', callback_data=HelpCallBack(level=0).pack()))
    
    return keyboard.adjust(*sizes).as_markup()
